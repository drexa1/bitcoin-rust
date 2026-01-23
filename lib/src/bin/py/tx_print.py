import argparse
from pathlib import Path
from lib.src.types.py.transaction import Transaction


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tx_file", type=Path, help="Path to the transaction file")
    args = parser.parse_args()
    tx = Transaction.load(args.tx_file)
    print(tx)


if __name__ == "__main__":
    main()