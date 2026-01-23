from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple
import cbor2
from pydantic import BaseModel, Field
from lib.src.types.py.error import InvalidTransaction, InvalidBlock, InvalidMerkleRoot
from lib.src.types.py.block import Block
from lib.src.types.py.crypto import Hash, MerkleRoot
from lib.src.types.py.transaction import TransactionOutput, Transaction

MIN_TARGET = 2**239  # Moderate
DIFFICULTY_UPDATE_INTERVAL = 10
IDEAL_BLOCK_TIME = 600
MAX_MEMPOOL_TRANSACTION_AGE = 3600


class Blockchain(BaseModel):
    utxos: dict[Hash, Tuple[bool, TransactionOutput]] = Field(default_factory=dict)
    target: int = MIN_TARGET
    blocks: list[Block] = Field(default_factory=list)
    mempool: list[tuple[datetime, Transaction]] = Field(default_factory=list)

    def add_to_mempool(self, tx: Transaction):
        # Check inputs
        known_inputs = set()
        for tx_in in tx.inputs:
            if tx_in.prev_transaction_output_hash not in self.utxos:
                raise InvalidTransaction()
            if tx_in.prev_transaction_output_hash in known_inputs:
                raise InvalidTransaction()
            known_inputs.add(tx_in.prev_transaction_output_hash)
            # Handle UTXOs already marked in mempool
            marked, _ = self.utxos[tx_in.prev_transaction_output_hash]
            if marked:
                # find the transaction that references it
                for idx, (_, mtx) in enumerate(self.mempool):
                    if any(o.hash() == tx_in.prev_transaction_output_hash for o in mtx.outputs):
                        # unmark all its inputs
                        for mi in mtx.inputs:
                            self.utxos[mi.prev_transaction_output_hash] = (False, self.utxos[mi.prev_transaction_output_hash][1])
                        self.mempool.pop(idx)
                        break
                else:
                    self.utxos[tx_in.prev_transaction_output_hash] = (False, self.utxos[tx_in.prev_transaction_output_hash][1])

        # Check inputs vs outputs
        total_input = sum(self.utxos[i.prev_transaction_output_hash][1].value for i in tx.inputs)
        total_output = sum(o.value for o in tx.outputs)
        if total_input < total_output:
            raise InvalidTransaction()
        # Mark inputs as used
        for tx_in in tx.inputs:
            self.utxos[tx_in.prev_transaction_output_hash] = (True, self.utxos[tx_in.prev_transaction_output_hash][1])
        # Add to mempool
        self.mempool.append((datetime.now(timezone.utc), tx))
        # Sort by miner fee descending
        self.mempool.sort(key=lambda pair: sum(self.utxos[i.prev_transaction_output_hash][1].value for i in pair[1].inputs) - sum(o.value for o in pair[1].outputs), reverse=True)

    def cleanup_mempool(self):
        now = datetime.now(timezone.utc)
        to_unmark = []
        new_mempool = []
        for ts, tx in self.mempool:
            if (now - ts).total_seconds() > MAX_MEMPOOL_TRANSACTION_AGE:
                to_unmark.extend(i.prev_transaction_output_hash for i in tx.inputs)
            else:
                new_mempool.append((ts, tx))
        self.mempool = new_mempool
        for h in to_unmark:
            marked, out = self.utxos[h]
            self.utxos[h] = (False, out)

    def add_block(self, block: Block):
        if not self.blocks:
            if block.header.prev_hash != Hash.zero():
                raise InvalidBlock()
        else:
            last_block = self.blocks[-1]
            if block.header.prev_hash != last_block.hash():
                raise InvalidBlock()
            # check target
            if block.header.hash().matches_target(block.header.target):
                raise InvalidBlock()
            # merkle root check
            calculated_merkle_root = MerkleRoot.calculate(block.transactions)
            if calculated_merkle_root != block.header.merkle_root:
                raise InvalidMerkleRoot()
            if block.header.timestamp <= last_block.header.timestamp:
                raise InvalidBlock()
            block.verify_transactions(len(self.blocks), self.utxos)
        # Remove from mempool
        block_tx_hashes = {tx.hash() for tx in block.transactions}
        self.mempool = [(ts, tx) for ts, tx in self.mempool if tx.hash() not in block_tx_hashes]
        self.blocks.append(block)
        self.try_adjust_target()

    def try_adjust_target(self):
        if not self.blocks or len(self.blocks) % DIFFICULTY_UPDATE_INTERVAL != 0:
            return
        start_time = self.blocks[-DIFFICULTY_UPDATE_INTERVAL].header.timestamp
        end_time = self.blocks[-1].header.timestamp
        time_diff_sec = (end_time - start_time).total_seconds()
        target_time = IDEAL_BLOCK_TIME * DIFFICULTY_UPDATE_INTERVAL
        new_target = int(Decimal(self.target) * Decimal(time_diff_sec) / Decimal(target_time))
        new_target = max(self.target // 4, min(self.target * 4, new_target))
        self.target = min(new_target, MIN_TARGET)

    def rebuild_utxos(self):
        self.utxos.clear()
        for block in self.blocks:
            for tx in block.transactions:
                for inp in tx.inputs:
                    self.utxos.pop(inp.prev_transaction_output_hash, None)
                for out in tx.outputs:
                    self.utxos[out.hash()] = (False, out)

    def save(self, filename: str):
        with open(filename, "wb") as f:
            cbor2.dump(self.model_dump(), f)

    @classmethod
    def load(cls, filename: str) -> "Blockchain":
        with open(filename, "rb") as f:
            data = cbor2.load(f)
        return cls(**data)
