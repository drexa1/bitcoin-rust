use std::collections::HashSet;
use std::sync::Arc;
use base64::Engine;
use base64::engine::general_purpose;
use chrono::Utc;
use log::{error, info, warn};
use uuid::Uuid;
use tokio::net::TcpStream;
use tokio::sync::Mutex;
use btclib::crypto::{Hash, MerkleRoot};
use btclib::network::Message;
use btclib::types::{Block, BlockHeader, Transaction, TransactionOutput};
use btclib::network::Message::*;

pub async fn handle(stream: TcpStream) {
    let stream = Arc::new(Mutex::new(stream));
    loop {
        // Read a message from the socket
        let mut locked_stream = stream.lock().await;
        let message = match Message::receive_async(&mut *locked_stream).await {
            Ok(message) => message,
            Err(e) => {
                error!("Invalid message from peer: {e}, closing connection");
                return;
            }
        };
        match message {
            AskDifference(height) => {
                let blockchain = crate::BLOCKCHAIN.read().await;
                let count = blockchain.block_height() as i32 - height as i32;
                let message = Difference(count);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
            DiscoverNodes(dialing_node, current_node) => {
                // Here, the responding node is the dialed one
                info!("📞 [{}] receiving call from [{}]", current_node, dialing_node);
                match TcpStream::connect(&dialing_node).await {
                    Ok(s) => {
                        let stream = Arc::new(Mutex::new(s));
                        crate::NODES.insert(dialing_node.clone(), stream);
                        info!("➕  Added node [{}]", dialing_node);
                        info!("🌐 Known network nodes: [{}]", crate::NODES.len());
                    },
                    Err(e) => {
                        error!("⚠️ Failed to connect to {}: {}", dialing_node, e);
                        return;
                    }
                }
                let nodes: HashSet<String> = crate::NODES.iter().map(|x| x.key().clone()).collect();
                let message = NodeList(nodes);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
            FetchBlock(height) => {
                let blockchain = crate::BLOCKCHAIN.read().await;
                let Some(block) = blockchain.blocks().nth(height).cloned() else {
                    return;
                };
                let message = NewBlock(block);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
            FetchTemplate(pubkey) => {
                let blockchain = crate::BLOCKCHAIN.read().await;
                let mut transactions = vec![];
                // Insert transactions from mempool
                transactions.extend(
                    blockchain
                        .mempool()
                        .iter()
                        .take(btclib::BLOCK_TRANSACTION_CAP)
                        .map(|(_, tx)| tx)
                        .cloned()
                        .collect::<Vec<_>>(),
                );
                // Insert coinbase tx with a pubkey
                transactions.insert(0, Transaction {
                    inputs: vec![],
                    outputs: vec![TransactionOutput {
                        public_key: pubkey,
                        unique_id: Uuid::new_v4(),
                        value: 0,
                    }]
                });
                let merkle_root = MerkleRoot::calculate(&transactions);
                let mut block = Block::new(
                    BlockHeader {
                        timestamp: Utc::now(),
                        prev_block_hash: blockchain.blocks().last().map(|last_block| {
                            last_block.hash()
                        }).unwrap_or(Hash::zero()),
                        nonce: 0,
                        target: blockchain.target(),
                        merkle_root
                    },
                    transactions
                );
                let miner_fees = match block.calculate_miner_fees(blockchain.utxos()) {
                    Ok(fees) => fees,
                    Err(e) => {
                        error!("{e}");
                        return;
                    }
                };
                let reward =  blockchain.calculate_block_reward();
                // Update coinbase tx with reward
                block.transactions[0].outputs[0].value = reward + miner_fees;
                // Recalculate merkle root
                block.header.merkle_root = MerkleRoot::calculate(&block.transactions);
                let message = Template(block);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
            FetchUTXOs(key) => {
                println!("Received request to fetch UTXOs");
                let blockchain = crate::BLOCKCHAIN.read().await;
                let utxos = blockchain.utxos().iter().filter(|(_, (_, tx_out))| {
                    tx_out.public_key == key
                }).map(|(_, (marked, tx_out))| {
                    (tx_out.clone(), *marked)
                }).collect::<Vec<_>>();
                let message = UTXOs(utxos);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
            NewBlock(block) => {
                let mut blockchain = crate::BLOCKCHAIN.write().await;
                info!("📦 Received new block");
                if blockchain.add_block(block).is_err() {
                    error!("❌  Block rejected");
                }
            }
            NewTransaction(tx) => {
                let mut blockchain = crate::BLOCKCHAIN.write().await;
                println!("Received transaction from friend");
                if blockchain.add_to_mempool(tx).is_err() {
                    error!("❌ Transaction rejected, closing connection");
                    return;
                }
            }
            SubmitTemplate(block, miner) => {
                let encoded_point = miner.0.to_encoded_point(true);
                let miner_id = general_purpose::STANDARD.encode(encoded_point.as_bytes());
                info!("Received allegedly mined template from: 👷{}", miner_id);
                let mut blockchain = crate::BLOCKCHAIN.write().await;
                if let Err(e) = blockchain.add_block(block.clone()) {
                    error!("❌  Block rejected: {e}, closing connection");
                    return;
                }
                blockchain.rebuild_utxos();
                info!("Block looks good, broadcasting📡️");
                // Send block to all friend nodes
                let nodes = crate::NODES.iter().map(|x| x.key().clone()).collect::<Vec<_>>();
                for node in nodes {
                    if let Some(stream) = crate::NODES.get_mut(&node) {
                        let message = NewBlock(block.clone());
                        let mut locked_stream = stream.lock().await;
                        if message.send_async(&mut *locked_stream).await.is_err() {
                            error!("⚠️ Failed to send block to {}", node);
                        }
                    }
                }
            }
            SubmitTransaction(tx) => {
                println!("Submit tx");
                let mut blockchain = crate::BLOCKCHAIN.write().await;
                if let Err(e) = blockchain.add_to_mempool(tx.clone()) {
                    error!("❌ Transaction rejected, closing connection: {e}");
                    return;
                }
                info!("🗃️ Added transaction to mempool");
                // Send transaction to all friend nodes
                let nodes = crate::NODES
                    .iter()
                    .map(|x| x.key().clone())
                    .collect::<Vec<_>>();
                for node in nodes {
                    info!("Sending to friend: [{node}]");
                    if let Some(stream) = crate::NODES.get_mut(&node) {
                        let message = NewTransaction(tx.clone());
                        let mut locked_stream = stream.lock().await;
                        if message.send_async(&mut *locked_stream).await.is_err() {
                            error!("⚠️ Failed to send transaction to {}", node);
                        }
                    }
                }
                info!("💰 Transaction sent to friends");
            }
            UTXOs(_) | Template(_) | Difference(_) | TemplateValidity(_) | NodeList(_) => {
                warn!("👋 I am neither a miner nor a wallet! Goodbye");
                return;
            }
            ValidateTemplate(block_template) => {
                let blockchain = crate::BLOCKCHAIN.read().await;
                let status = block_template.header.prev_block_hash == blockchain
                    .blocks()
                    .last()
                    .map(|last_block| last_block.hash())
                    .unwrap_or(Hash::zero());
                let message = TemplateValidity(status);
                message.send_async(&mut *locked_stream).await.unwrap();
            }
        }
    }
}