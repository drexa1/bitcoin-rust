use serde::{Deserialize, Serialize};
use crate::crypto::PublicKey;
use crate::types::{Block, Transaction, TransactionOutput};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub enum Message {

    /// Fetch all UTXOs belonging to a public key
    FetchUTXOs(PublicKey),

    /// UTXOs belonging to a public key. Bool = marked
    UTXOs(Vec<(TransactionOutput, bool)>),

    /// Send a transaction to the network
    SubmitTransaction(Transaction),

    /// Broadcast a new transaction to other nodes
    NewTransaction(Transaction),

    /// Ask the node to prepare the optimal block template with the coinbase transaction paying the specified public key
    FetchTemplate(PublicKey),
    
    /// Block template
    Template(Block),
    
    /// Ask the node to validate a block template.
    /// This is to prevent the node from mining an invalid block
    /// (i.e: if one has been found in the meantime, or if transactions have been removed from the mempool)
    ValidateTemplate(Block),

    /// If template is valid
    TemplateValidity(bool),

    /// Submit a mined block to a node
    SubmitTemplate(Block),

    /// Ask a node to report all the other nodes it knows about
    DiscoverNodes,

    /// Response to DiscoverNodes
    NodeList(Vec<String>),

    /// Ask a node what is the highest block it knows about in comparison to the local blockchain
    AskDifference(u32),

    /// Response to AskDifference
    Difference(i32),

    /// Ask a node to send a block with the specified height
    FetchBlock(usize),

    /// Broadcast a new block to other nodes
    NewBlock(Block)

}