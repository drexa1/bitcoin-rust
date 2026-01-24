use crate::types::Transaction;
use crate::util::Saveable;
use ecdsa::{signature::{Signer, Verifier}, Signature as ECDSASignature, SigningKey, VerifyingKey};
use k256::elliptic_curve::rand_core::OsRng;
use k256::Secp256k1;
use primitive_types::U256;
use serde::{Deserialize, Serialize};
use sha256::digest;
use spki::EncodePublicKey;
use std::fmt;
use std::io::{Error as IoError, ErrorKind as IoErrorKind, Read, Result as IoResult, Write};


#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq, Serialize, Deserialize)]
pub struct Hash(U256);
impl Hash {
    /// Hash anything that can be serialized via Ciborium
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
    /// Check if a hash matches a target
    pub fn matches_target(&self, target: U256) -> bool {
        self.0 <= target
    }
    /// Zero hash
    pub fn zero() -> Self {
        Hash(U256::zero())
    }
    /// To bytes
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

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Signature(ECDSASignature<Secp256k1>);
impl Signature {
    /// Sign a TransactionOutput from its Sha256 hash
    pub fn sign_output(output_hash: &Hash, private_key: &PrivateKey) -> Self {
        let signing_key = &private_key.0;
        let signature = signing_key.sign(&output_hash.as_bytes());
        Signature(signature)
    }
    /// Verify a signature
    pub fn verify(&self, output_hash: &Hash, public_key: &PublicKey) -> bool {
        public_key.0.verify(&output_hash.as_bytes(), &self.0).is_ok()
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct PublicKey(VerifyingKey<Secp256k1>);
// Save and load as PEM
impl Saveable for PublicKey {
    fn load<I: Read>(mut reader: I) -> IoResult<Self> {
        // Read PEM-encoded public key into string
        let mut buf = String::new();
        reader.read_to_string(&mut buf)?;
        // Decode the public key from PEM
        let public_key = buf.parse().map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to parse PublicKey")
        })?;
        Ok(PublicKey(public_key))
    }
    fn save<O: Write>(&self, mut writer: O) -> IoResult<()> {
        let s = self.0.to_public_key_pem(Default::default()).map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to serialize PublicKey")
        })?;
        writer.write_all(s.as_bytes())
    }
}
impl fmt::Debug for PublicKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let json = serde_json::to_string_pretty(self)
            .map_err(|_| fmt::Error)?;
        write!(f, "{json}")
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct PrivateKey(
    #[serde(with = "signkey_serde")]
    SigningKey<Secp256k1>
);
impl PrivateKey {
    pub fn new_key() -> Self {
        PrivateKey(SigningKey::random(&mut OsRng))
    }
    pub fn public_key(&self) -> PublicKey {
        PublicKey(self.0.verifying_key().clone())
    }
}
impl Saveable for PrivateKey {
    fn load<I: Read>(reader: I) -> IoResult<Self> {
        ciborium::de::from_reader(reader).map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to deserialize PrivateKey")
        })
    }
    fn save<O: Write>(&self, writer: O) -> IoResult<()> {
        ciborium::ser::into_writer(self, writer).map_err(|_| {
            IoError::new(IoErrorKind::InvalidData, "Failed to serialize PrivateKey")
        })
    }
}

mod signkey_serde {
    pub fn serialize<S>(key: &super::SigningKey<super::Secp256k1>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_bytes(&key.to_bytes())
    }
    pub fn deserialize<'de, D>(deserializer: D) -> Result<super::SigningKey<super::Secp256k1>, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let bytes: Vec<u8> = serde::Deserialize::deserialize(deserializer)?;
        Ok(super::SigningKey::from_slice(&bytes).unwrap())
    }
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct MerkleRoot(Hash);
impl MerkleRoot {
    pub fn calculate(transactions: &[Transaction]) -> MerkleRoot {
        let mut layer: Vec<Hash> = vec![];
        for transaction in transactions {
            layer.push(Hash::hash(transaction));
        }
        while layer.len() > 1 {
            let mut new_layer = vec![];
            for pair in layer.chunks(2) {
                let left = pair[0];
                // If there is no right, use the left one again
                let right = pair.get(1).unwrap_or(&pair[0]);
                new_layer.push(Hash::hash(&[left, *right]));
            }
            layer = new_layer;
        }
        MerkleRoot(layer[0])
    }
}