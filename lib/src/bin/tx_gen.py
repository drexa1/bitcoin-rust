import sys
import uuid
from crypto import PrivateKey
from ..types.transaction import Transaction, TransactionOutput
from ..types.block import INITIAL_REWARD


def main():
    if len(sys.argv) != 1:
        print("Usage: tx_gen <tx_file>")
        sys.exit(1)
    path = sys.argv[1]
    private_key = PrivateKey.new_key()
    transaction = Transaction(
        inputs=[],
        outputs=[TransactionOutput(INITIAL_REWARD * 10**8, uuid.uuid4(), private_key.public_key())]
    )
    transaction.save_to_file(path)


if __name__ == "__main__":
    main()
