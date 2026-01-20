import sys
from pathlib import Path
from lib.src.types.py.transaction import Transaction


def main():
    if len(sys.argv) < 2:
        print("Usage: tx_print <tx_file>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = Path(__file__).parent / path
    try:
        tx = Transaction.load(path)
    except Exception:
        raise RuntimeError("Failed to load transaction")
    print(tx)


if __name__ == "__main__":
    main()