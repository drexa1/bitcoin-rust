import sys
from uuid import uuid4
from datetime import datetime, timezone
from crypto import Hash, MerkleRoot, PrivateKey
from ..types.blockchain import MIN_TARGET
from ..types.transaction import Transaction, TransactionOutput
from ..types.block import INITIAL_REWARD, Block, BlockHeader


def main():
    if len(sys.argv) != 1:
        print("Usage: block_gen <block_file>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    private_key = PrivateKey.new_key()
    transactions = [Transaction(
        inputs=[],
        outputs=[TransactionOutput(
            unique_id=uuid4(),
            value=INITIAL_REWARD * (10 ** 8),
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
    block.save_to_file(path)


if __name__ == "__main__":
    main()
