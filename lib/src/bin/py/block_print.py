import argparse
from pathlib import Path
from lib.src.types.py.block import Block


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--block-file", type=Path, help="Path to the block file")
    args = parser.parse_args()
    block = Block.load_from_file(args.block_file)
    print(block)

if __name__ == "__main__":
    main()
