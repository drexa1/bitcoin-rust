import hashlib
from dataclasses import dataclass
from typing import Any, List
import cbor2
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError  # noqa
from pydantic import BaseModel, field_serializer, field_validator


@dataclass(frozen=True)
class Hash:
    value: int

    @staticmethod
    def hash(data: Any) -> "Hash":
        """
        Hash anything serializable via CBOR
        """
        serialized = cbor2.dumps(data)
        digest = hashlib.sha256(serialized).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        return Hash(value)

    def matches_target(self, target: int) -> bool:
        return self.value <= target

    @staticmethod
    def zero() -> "Hash":
        return Hash(0)

    def as_bytes(self) -> bytes:
        # Little-endian 32 bytes
        return self.value.to_bytes(32, byteorder="little", signed=False)



class PublicKey(BaseModel):
    key: VerifyingKey

    model_config = {
        "arbitrary_types_allowed": True
    }

    # Serializer: VerifyingKey -> hex string
    @field_serializer("key")
    def serialize_key(self, vk: VerifyingKey):
        return vk.to_string().hex()

    # Validator: hex string -> VerifyingKey
    @field_validator("key", mode="before")
    def parse_key(cls, v):
        if isinstance(v, str):
            return VerifyingKey.from_string(bytes.fromhex(v), curve=SECP256k1)
        return v



@dataclass
class PrivateKey:
    key: SigningKey

    @staticmethod
    def new_key() -> "PrivateKey":
        return PrivateKey(SigningKey.generate(curve=SECP256k1))

    def public_key(self) -> PublicKey:
        return PublicKey(key=self.key.get_verifying_key())

    def to_bytes(self) -> bytes:
        return self.key.to_string()

    @staticmethod
    def from_bytes(data: bytes) -> "PrivateKey":
        return PrivateKey(SigningKey.from_string(data, curve=SECP256k1))


@dataclass
class Signature:
    sig_bytes: bytes

    @staticmethod
    def sign_output(output_hash: Hash, private_key: PrivateKey) -> "Signature":
        sig = private_key.key.sign(output_hash.as_bytes())
        return Signature(sig)

    def verify(self, output_hash: Hash, public_key: PublicKey) -> bool:
        try:
            public_key.key.verify(self.sig_bytes, output_hash.as_bytes())
            return True
        except BadSignatureError:
            return False


@dataclass(frozen=True)
class MerkleRoot:
    hash: Hash

    @staticmethod
    def calculate(transactions: List[Any]) -> "MerkleRoot":
        layer: List[Hash] = [Hash.hash(tx) for tx in transactions]
        if not layer:
            return MerkleRoot(Hash.zero())
        while len(layer) > 1:
            new_layer: List[Hash] = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i + 1] if i + 1 < len(layer) else layer[i]
                new_layer.append(Hash.hash([left.value, right.value]))
            layer = new_layer
        return MerkleRoot(layer[0])
