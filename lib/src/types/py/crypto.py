import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Any
import cbor2
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError  # noqa
from pydantic import BaseModel, field_serializer, field_validator
from lib.src.types.py.util import CBORSerializable


@dataclass(frozen=True)
class Hash:
    value: int

    @staticmethod
    def hash(data: BaseModel | Iterable["Hash"]) -> "Hash":
        serialized = cbor2.dumps(data.model_dump())
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
    def parse_key(cls, v):  # noqa
        if isinstance(v, str):
            return VerifyingKey.from_string(bytes.fromhex(v), curve=SECP256k1)
        return v

    def save(self, filename: Path) -> None:
        with open(filename, "wb") as f:
            f.write(self.key.to_pem())

    @classmethod
    def load(cls, filename: Path) -> "PublicKey":
        with open(filename, "r") as f:
            pem = f.read()
        return cls(key=VerifyingKey.from_pem(pem))



@dataclass
class PrivateKey(CBORSerializable):
    key: SigningKey

    model_config = {
        "arbitrary_types_allowed": True
    }

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
    def calculate(transactions: list[Any]) -> "MerkleRoot":  # list[Transaction] but just to avoid circular import
        layer: list[Hash] = [Hash.hash(tx) for tx in transactions]
        if not layer:
            return MerkleRoot(Hash.zero())
        while len(layer) > 1:
            new_layer: list[Hash] = []
            for i in range(0, len(layer), 2):
                left: Hash = layer[i]
                right: Hash = layer[i + 1] if i + 1 < len(layer) else layer[i]
                new_layer.append(Hash.hash([left, right]))
            layer = new_layer
        return MerkleRoot(layer[0])
