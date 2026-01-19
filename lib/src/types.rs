use std::collections::HashMap;
use chrono::{DateTime, Utc};
use primitive_types::U256;
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use crate::crypto::{Signature, PublicKey};
use crate::error::{BtcError, Result};
use crate::sha256::Hash;
use crate::util::MerkleRoot;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Blockchain {
    pub utxos: HashMap<Hash, TransactionOutput>,
    pub blocks: Vec<Block>,
}
impl Blockchain {
    pub fn new() -> Self {
        Blockchain { utxos: HashMap::new(), blocks: vec![] }
    }
    pub fn add_block(&mut self, block: Block) -> Result<()> {
        // Check if the block is valid
        if self.blocks.is_empty() {
            // If first block, check if the prev block hash is all zeroes
            if block.header.prev_hash != Hash::zero() {
                println!("zero hash");
                return Err(BtcError::InvalidBlock);
            }
        } else {
            // If not the first block, check if the prev block hash is the hash of the last block
            let last_block = self.blocks.last().unwrap();
            if block.header.prev_hash != last_block.hash() {
                println!("wrong prev hash");
                return Err(BtcError::InvalidBlock);
            }
            // Check if the block's hash is less than the target
            if !block.header.hash().matches_target(block.header.target) {
                println!("does not match target");
                return Err(BtcError::InvalidBlock);
            }
            // Check if block's merkle root is correct
            let calculated_merkle_root = MerkleRoot::calculate(&block.transactions);
            if calculated_merkle_root != block.header.merkle_root {
                println!("invalid merkle root");
                return Err(BtcError::InvalidMerkleRoot);
            }
            // Check if the block's timestamp is after the last block's timestamp
            if block.header.timestamp <= last_block.header.timestamp {
                return Err(BtcError::InvalidBlock);
            }
        }
        self.blocks.push(block);
        Ok(())
    }
    // Rebuild UTXO set from the blockchain
    pub fn rebuild_utxos(&mut self) {
        for block in &self.blocks {
            for transaction in &block.transactions {
                for input in &transaction.inputs {
                    self.utxos.remove(&input.prev_transaction_output_hash, );
                }
                for output in transaction.outputs.iter() {
                    self.utxos.insert(transaction.hash(), output.clone());
                }
            }
        }
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Block { pub header: BlockHeader, pub transactions: Vec<Transaction> }
impl Block {
    pub fn new(header: BlockHeader, transactions: Vec<Transaction>) -> Self {
        Block { header, transactions }
    }
    pub fn hash(&self) -> Hash {
        Hash::hash(self)
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct BlockHeader {
    /// The time when the block was created
    pub timestamp: DateTime<Utc>,
    /// Number only used once, we increment it to mine the block
    pub nonce: u64,
    /// Hash of the previous block in the chain
    pub prev_hash: Hash,
    /// The hash of the Merkle tree root derived from all the transactions in this block.
    /// This ensures that all transactions are accounted for and unalterable without changing the header.
    pub merkle_root: MerkleRoot,
    /// A number, which has to be higher than the hash of this block for it to be considered valid.
    pub target: U256,
}
impl BlockHeader {
    pub fn new(
        timestamp: DateTime<Utc>,
        nonce: u64,
        prev_hash: Hash,
        merkle_root: MerkleRoot,
        target: U256
    ) -> Self {
        BlockHeader { timestamp, nonce, prev_hash, merkle_root, target }
    }
    pub fn hash(&self) -> Hash {
        unimplemented!()
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct TransactionInput {
    /// The hash of the transaction output, which we are linking into this transaction as input
    pub prev_transaction_output_hash: Hash,
    /// This is how the user proves they can use the output of the previous transaction
    pub signature: Signature
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct TransactionOutput {
    pub value: u64,
    pub unique_id: Uuid,
    pub public_key: PublicKey
}
impl TransactionOutput {
    pub fn hash(&self) -> Hash {
        Hash::hash(self)
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Transaction {
    pub inputs: Vec<TransactionInput>,
    pub outputs: Vec<TransactionOutput>
}
impl Transaction {
    pub fn new(inputs: Vec<TransactionInput>, outputs: Vec<TransactionOutput>) -> Self {
        Transaction { inputs, outputs }
    }
    pub fn hash(&self) -> Hash {
        unimplemented!()
    }
}

