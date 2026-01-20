import sys
from ..types.block import Block


def main():
    if len(sys.argv) != 1:
        print("Usage: block_print <block_file>")
        sys.exit(1)
    path = sys.argv[1]
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        print("Failed to open block file")
        sys.exit(1)
    try:
        block = Block.parse(raw)
    except Exception as e:
        print(f"Failed to load block: {e}")
        sys.exit(1)
    print(block)


if __name__ == "__main__":
    main()
