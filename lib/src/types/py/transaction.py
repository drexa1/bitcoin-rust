import json
from dataclasses import dataclass
from typing import List
from uuid import UUID
from pydantic import BaseModel
from lib.src.types.py.crypto import Signature, PublicKey, Hash
from lib.src.types.py.util import CBORSerializable


@dataclass
class TransactionInput:
    prev_transaction_output_hash: Hash
    signature: Signature


class TransactionOutput(BaseModel):
    value: int
    unique_id: UUID
    public_key: PublicKey

    model_config = {
        "arbitrary_types_allowed": True
    }

    def hash(self) -> Hash:
        return Hash.hash(self)

class Transaction(BaseModel, CBORSerializable):
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]

    def hash(self) -> Hash:
        return Hash.hash(self)

    def __str__(self):
        return json.dumps(self.model_dump(), indent=4, default=str)
