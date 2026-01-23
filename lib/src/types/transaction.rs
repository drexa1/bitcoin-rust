use std::io::{
    Error as IoError, ErrorKind as IoErrorKind, Read,
    Result as IoResult, Write
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::crypto::{Hash, PublicKey, Signature};
use crate::util::Saveable;

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
        Hash::hash(self)
    }
}
/// Save and load expecting CBOR from ciborium as format
impl Saveable for Transaction {
    fn load<I: Read>(reader: I) -> IoResult<Self> {
        ciborium::de::from_reader(reader).map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to deserialize Transaction")
        })
    }

    fn save<O: Write>(&self, writer: O) -> IoResult<()> {
        ciborium::ser::into_writer(self, writer).map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to serialize Transaction")
        })
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