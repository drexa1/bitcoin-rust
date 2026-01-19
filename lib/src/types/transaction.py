from dataclasses import dataclass
from typing import List
from uuid import UUID
import cbor2
from pydantic import BaseModel
from crypto import Signature, PublicKey, Hash


@dataclass
class TransactionInput:
    prev_transaction_output_hash: Hash
    signature: Signature

@dataclass
class TransactionOutput:
    value: int
    unique_id: UUID
    public_key: PublicKey

    def hash(self) -> Hash:
        return Hash.hash(self)

class Transaction(BaseModel):
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]

    def hash(self) -> Hash:
        return Hash.hash(self)

    def save(self, filename: str):
        with open(filename, "wb") as f:
            cbor2.dump(self.model_dump(), f)

    @classmethod
    def load(cls, filename: str) -> "Transaction":
        with open(filename, "rb") as f:
            data = cbor2.load(f)
        return cls(**data)
