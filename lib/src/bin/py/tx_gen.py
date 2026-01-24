import argparse
import uuid
from pathlib import Path
from lib.src.types.py.crypto import PrivateKey
from lib.src.types.py.transaction import Transaction, TransactionOutput
from lib.src.types.py.block import INITIAL_REWARD


def main():
    parser = argparse.ArgumentParser(description="Generate a new transaction and save it to a file.")
    parser.add_argument("-f", "--tx-file", type=Path, help="Path to save the transaction")
    args = parser.parse_args()

    private_key = PrivateKey.new_key()
    transaction = Transaction(
        inputs=[],
        outputs=[TransactionOutput(
            unique_id=uuid.uuid4(),
            value=INITIAL_REWARD * 10**8,
            public_key=private_key.public_key()
        )]
    )

    transaction.save(args.tx_file)
    print("Tx saved")


if __name__ == "__main__":
    main()
