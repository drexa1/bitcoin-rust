use anyhow::{Context, Result};
use log::{error, info};
use tokio::net::TcpStream;
use tokio::time;
use btclib::network::Message;
use btclib::types::Blockchain;
use btclib::util::Saveable;

pub async fn populate_connections(node_addr: &str, known_nodes: &[String]) -> Result<()> {
    info!("Trying to connect to other nodes...");
    for known_node in known_nodes {
        info!("🔗 Connecting to [{}]", known_node);
        let mut stream = TcpStream::connect(&known_node).await?;
        // Add first all the nodes known by each known node
        Message::DiscoverNodes(node_addr.to_string(), known_node.to_string()).send_async(&mut stream).await?;
        info!("Sending 'DiscoverNodes' to [{}]", known_node);
        let message = Message::receive_async(&mut stream).await?;
        match message {
            Message::NodeList(nodes_response) => {
                info!("Received 'NodeList' from [{}] with {} nodes", known_node, nodes_response.len());
                for node in nodes_response {
                    let stream = TcpStream::connect(&node).await?;
                    info!("➕  Added node [{}]", node);
                    crate::NODES.insert(node, stream);
                }
            }
            e => {
                error!("Unexpected message from [{}]: {:?}", known_node, e);
            }
        }
        // Finally add each known node given as boot config
        info!("➕  Added node [{}]", known_node);
        crate::NODES.insert(known_node.clone(), stream);
    }
    Ok(())
}

pub async fn load_blockchain(blockchain_file: &str) -> Result<()> {
    let new_blockchain = Blockchain::load_from_file(blockchain_file)?;
    info!("Blockchain loaded");
    let mut blockchain = crate::BLOCKCHAIN.write().await;
    *blockchain = new_blockchain;
    info!("Rebuilding UTXOs...");
    blockchain.rebuild_utxos();
    info!("🏹 Checking if target needs to be adjusted:");
    info!("Current target: {}", blockchain.target());
    blockchain.try_adjust_target();
    info!("New target: {}{}", " ".repeat(4), blockchain.target());  // Indent with previous line
    info!("Node initialization complete");
    Ok(())
}

pub async fn find_longest_chain_node() -> Result<(String, u32)> {
    info!("🪜 Finding nodes with the highest blockchain length...");
    let mut longest_node = String::new();
    let mut longest_count = 0;
    let all_nodes = crate::NODES.iter().map(|x| x.key().clone()).collect::<Vec<_>>();
    for node in all_nodes {
        info!("Asking [{}] about blockchain length", node);
        let mut stream = crate::NODES.get_mut(&node).context("no node")?;
        let message = Message::AskDifference(0);
        message.send_async(&mut *stream).await?;
        info!("Sent 'AskDifference' to [{}]", node);
        let message = Message::receive_async(&mut *stream).await?;
        match message {
            Message::Difference(count) => {
                info!("Received 'Difference' from [{}]", node);
                if count > longest_count {
                    info!("New longest blockchain: {} blocks from [{node}]", count);
                    longest_count = count;
                    longest_node = node;
                }
            }
            e => {
                error!("Unexpected message from [{}]: {:?}", node, e);
            }
        }
    }
    Ok((longest_node, longest_count as u32))
}

pub(crate) async fn download_blockchain(node: &str, count: u32) -> Result<()> {
    let mut stream = crate::NODES.get_mut(node).unwrap();
    for i in 0..count as usize {
        let message = Message::FetchBlock(i);
        message.send_async(&mut *stream).await?;
        let message = Message::receive_async(&mut *stream).await?;
        match message {
            Message::NewBlock(block) => {
                let mut blockchain = crate::BLOCKCHAIN.write().await;
                blockchain.add_block(block)?;
            }
            e => {
                error!("Unexpected message from {}: {:?}", node, e);
            }
        }
    }
    Ok(())
}

pub async fn mempool_cleanup() {
    let mut interval = time::interval(time::Duration::from_secs(30));
    loop {
        interval.tick().await;
        info!("🧹 Cleaning mempool old transactions");
        let mut blockchain = crate::BLOCKCHAIN.write().await;
        blockchain.cleanup_mempool();
    }
}

pub async fn save(name: String) {
    let mut interval = time::interval(time::Duration::from_secs(15));
    loop {
        interval.tick().await;
        info!("💾 Saving blockchain to disk");
        let blockchain = crate::BLOCKCHAIN.read().await;
        blockchain.save_to_file(name.clone()).unwrap();
    }
}