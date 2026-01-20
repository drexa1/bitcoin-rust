from datetime import datetime, timezone
from typing import Tuple
from pydantic import BaseModel
from lib.src.types.py.crypto import Hash, MerkleRoot
from lib.src.types.py.error import InvalidTransaction, InvalidSignature
from lib.src.types.py.transaction import Transaction, TransactionOutput
from lib.src.types.py.util import CBORSerializable

INITIAL_REWARD = 50
HALVING_INTERVAL = 210000

class BlockHeader(BaseModel):
    timestamp: datetime
    nonce: int
    prev_hash: Hash
    merkle_root: MerkleRoot
    target: int

    def hash(self) -> Hash:
        return Hash.hash(self)

    def mine(self, steps: int) -> bool:
        if self.hash().matches_target(self.target):
            return True
        for _ in range(steps):
            self.nonce += 1
            if self.nonce >= 2**64:
                self.nonce = 0
                self.timestamp = datetime.now(timezone.utc)
            if self.hash().matches_target(self.target):
                return True
        return False


class Block(BaseModel, CBORSerializable):
    header: BlockHeader
    transactions: list[Transaction]

    def hash(self) -> Hash:
        return Hash.hash(self)

    def verify_transactions(
            self,
            predicted_block_height: int,
            utxos: dict[Hash, Tuple[bool, TransactionOutput]]
    ) -> None:
        if not self.transactions:
            raise ValueError("InvalidTransaction: empty block")
        self.verify_coinbase_transaction(predicted_block_height, utxos)
        seen_inputs = {}
        for tx in self.transactions[1:]:
            input_value = 0
            for tx_in in tx.inputs:
                prev_output = utxos.get(tx_in.prev_transaction_output_hash)
                if not prev_output:
                    raise InvalidTransaction()
                _, prev_output = prev_output
                if tx_in.prev_transaction_output_hash in seen_inputs:
                    raise InvalidTransaction()
                if not tx_in.signature.verify(tx_in.prev_transaction_output_hash, prev_output.public_key):
                    raise InvalidSignature()
                input_value += prev_output.value
                seen_inputs[tx_in.prev_transaction_output_hash] = prev_output
            output_value = sum(o.value for o in tx.outputs)
            if input_value < output_value:
                raise InvalidTransaction()

    def verify_coinbase_transaction(
            self,
            predicted_block_height: int,
            utxos: dict[Hash, Tuple[bool, TransactionOutput]]
    ) -> None:
        coinbase_tx = self.transactions[0]
        if coinbase_tx.inputs:
            raise InvalidTransaction()
        if not coinbase_tx.outputs:
            raise InvalidTransaction()
        miner_fees = self.calculate_miner_fees(utxos)
        block_reward = INITIAL_REWARD * 10**8 // (2 ** (predicted_block_height // HALVING_INTERVAL))
        total_outputs = sum(o.value for o in coinbase_tx.outputs)
        if total_outputs != block_reward + miner_fees:
            raise InvalidTransaction()

    def calculate_miner_fees(
            self,
            utxos: dict[Hash, Tuple[bool, TransactionOutput]]
    ) -> int:
        inputs: dict[Hash, TransactionOutput] = {}
        outputs: dict[Hash, TransactionOutput] = {}
        for tx in self.transactions[1:]:
            for tx_in in tx.inputs:
                prev_output = utxos.get(tx_in.prev_transaction_output_hash)
                if not prev_output:
                    raise InvalidTransaction()
                _, prev_output = prev_output
                if tx_in.prev_transaction_output_hash in inputs:
                    raise InvalidTransaction()
                inputs[tx_in.prev_transaction_output_hash] = prev_output
            for tx_out in tx.outputs:
                h = tx_out.hash()
                if h in outputs:
                    raise InvalidTransaction()
                outputs[h] = tx_out
        total_input = sum(o.value for o in inputs.values())
        total_output = sum(o.value for o in outputs.values())
        return total_input - total_output
