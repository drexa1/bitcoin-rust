import sys
import uuid
from timeit_decorator import timeit_sync
from crypto import PrivateKey
from lib.src.types.transaction import Transaction, TransactionOutput
from lib.src.types.block import INITIAL_REWARD


@timeit_sync(runs=5, workers=2)
def main():
    if len(sys.argv) != 2:
        print("Usage: tx_gen <tx_file>")
        sys.exit(1)
    path = sys.argv[1]
    private_key = PrivateKey.new_key()
    transaction = Transaction(
        inputs=[],
        outputs=[TransactionOutput(
            unique_id=uuid.uuid4(),
            value=INITIAL_REWARD * 10**8,
            public_key=private_key.public_key()
        )]
    )
    transaction.save(path)
    print("Done")


if __name__ == "__main__":
    main()
