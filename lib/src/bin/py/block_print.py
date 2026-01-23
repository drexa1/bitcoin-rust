import json
import sys
from pathlib import Path
from lib.src.types.py.block import Block


def main():
    if len(sys.argv) != 2:
        print("Usage: block_print <block_file>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = Path(__file__).parent / path
    try:
        block = Block.load(path)
    except Exception:
        raise RuntimeError("Failed to load transaction")
    pretty_block = json.dumps(block.model_dump(), indent=4, default=str)
    print(pretty_block)


if __name__ == "__main__":
    main()
