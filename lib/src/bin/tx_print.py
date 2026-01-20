import sys
from ..types.transaction import Transaction


def main():
    if len(sys.argv) < 2:
        print("Usage: tx_print <tx_file>")
        sys.exit(1)
    path = sys.argv[1]
    try:
        tx = Transaction.load(path)
        print(tx)
    except Exception:
        raise RuntimeError("Failed to load transaction")


if __name__ == "__main__":
    main()