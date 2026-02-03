use std::collections::HashSet;
use std::io::{Error as IoError, Read, Write};
use serde::{Deserialize, Serialize};
use crate::crypto::PublicKey;
use crate::types::{Block, Transaction, TransactionOutput};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub enum Message {

    /// Ask a node what the highest block it knows about in comparison to the local blockchain is
    AskDifference(u32),

    /// Response to AskDifference
    Difference(i32),

    /// Ask a node to report all the other nodes it knows about
    DiscoverNodes(String, String),

    /// Ask a node to send a block with the specified height
    FetchBlock(usize),

    /// Ask the node to prepare the optimal block template with the coinbase transaction paying the specified public key
    FetchTemplate(PublicKey),

    /// Fetch all UTXOs belonging to a public key
    FetchUTXOs(PublicKey),

    /// Broadcast a new block to other nodes
    NewBlock(Block),

    /// Broadcast a new transaction to other nodes
    NewTransaction(Transaction),

    /// Response to DiscoverNodes
    NodeList(HashSet<String>),

    /// Submit a mined block to a node
    SubmitTemplate(Block, PublicKey),

    /// Send a transaction to the network
    SubmitTransaction(Transaction),

    /// Block template
    Template(Block),

    /// If template is valid
    TemplateValidity(bool),

    /// UTXOs belonging to a public key. Bool = marked
    UTXOs(Vec<(TransactionOutput, bool)>),

    /// Ask the node to validate a block template. This is to prevent the node from mining an invalid block
    /// (i.e: if one has been found in the meantime, or if transactions have been removed from the mempool)
    ValidateTemplate(Block)
}
impl Message {

    /// We will use length-prefixed encoding for message
    pub fn encode(&self) -> Result<Vec<u8>, ciborium::ser::Error<IoError>> {
        let mut bytes = Vec::new();
        ciborium::into_writer(self, &mut bytes)?;
        Ok(bytes)
    }

    pub fn decode(data: &[u8]) -> Result<Self, ciborium::de::Error<IoError>> {
        ciborium::from_reader(data)
    }

    pub fn send(&self, stream: &mut impl Write) -> Result<(), ciborium::ser::Error<IoError>> {
        let bytes = self.encode()?;
        let len = bytes.len() as u64;
        stream.write_all(&len.to_be_bytes())?;
        stream.write_all(&bytes)?;
        Ok(())
    }

    pub fn receive(stream: &mut impl Read) -> Result<Self, ciborium::de::Error<IoError>> {
        let mut len_bytes = [0u8; 8];
        stream.read_exact(&mut len_bytes)?;
        let len = u64::from_be_bytes(len_bytes) as usize;
        let mut data = vec![0u8; len];
        stream.read_exact(&mut data)?;
        Self::decode(&data)
    }

    pub async fn send_async(&self, stream: &mut (impl AsyncWrite + Unpin)) -> Result<(), ciborium::ser::Error<IoError>> {
        let bytes = self.encode()?;
        let len = bytes.len() as u64;
        stream.write_all(&len.to_be_bytes()).await?;
        stream.write_all(&bytes).await?;
        Ok(())
    }

    pub async fn receive_async(stream: &mut (impl AsyncRead + Unpin)) -> Result<Self, ciborium::de::Error<IoError>> {
        let mut len_bytes = [0u8; 8];
        stream.read_exact(&mut len_bytes).await?;
        let len = u64::from_be_bytes(len_bytes) as usize;
        let mut data = vec![0u8; len];
        stream.read_exact(&mut data).await?;
        Self::decode(&data)
    }
}