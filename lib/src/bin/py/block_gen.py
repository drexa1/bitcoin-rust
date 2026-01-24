import argparse
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from lib.src.types.py.crypto import Hash, MerkleRoot, PrivateKey
from lib.src.types.py.block import INITIAL_REWARD, Block, BlockHeader
from lib.src.types.py.blockchain import MIN_TARGET
from lib.src.types.py.transaction import Transaction, TransactionOutput


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--block-file", type=Path, help="Path to save the new block", required=True)
    args = parser.parse_args()

    private_key = PrivateKey.new_key()
    transactions = [Transaction(
        inputs=[],
        outputs=[TransactionOutput(
            unique_id=uuid4(),
            value=INITIAL_REWARD * (10 ** 8),  # Sats
            public_key=private_key.public_key()
        )]
    )]
    merkle_root = MerkleRoot.calculate(transactions)
    block = Block(header=BlockHeader(
        timestamp=datetime.now(timezone.utc),
        nonce=0,
        prev_hash=Hash.zero(),
        merkle_root=merkle_root,
        target=MIN_TARGET,
    ), transactions=transactions)

    block.save(args.block_file)
    print("Block saved")


if __name__ == "__main__":
    main()
