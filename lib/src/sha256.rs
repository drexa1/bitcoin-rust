use std::fmt;
use primitive_types::U256;
use sha256::digest;
use serde::{Serialize, Deserialize};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct Hash(U256);
impl Hash {
    // Hash anything that can be serialized via Ciborium
    pub fn hash<T: serde::Serialize>(data: &T) -> Self {
        let mut serialized: Vec<u8> = vec![];
        if let Err(e) = ciborium::into_writer(data, &mut serialized) {
            panic!("Failed to serialize data {:?}", e);
        }
        let hash = digest(&serialized);
        let hash_bytes = hex::decode(hash).unwrap();
        let hash_array: [u8; 32] = hash_bytes.as_slice().try_into().unwrap();
        Hash(U256::from_big_endian(&hash_array))
    }
    // Check if a hash matches a target
    pub fn matches_target(&self, target: U256) -> bool {
        self.0 <= target
    }
    // Zero hash
    pub fn zero() -> Self {
        Hash(U256::zero())
    }
    // To bytes
    pub fn as_bytes(&self) -> [u8; 32] {
        let bytes = self.0.to_little_endian();
        bytes.as_slice().try_into().unwrap()
    }
}
impl fmt::Display for Hash {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:x}", self.0)
    }
}

pub struct MerkleRoot;

