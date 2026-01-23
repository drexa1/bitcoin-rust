import argparse
import copy
from pathlib import Path
from lib.src.types.py.block import Block


# @timeit_sync(runs=5, workers=2)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("block_file", type=Path, help="Path to the block file")
    parser.add_argument("steps", type=int, help="Number of mining steps")
    args = parser.parse_args()

    orig_block: Block = Block.load(args.block_file)
    print("Original block:", orig_block)
    print("Hash:", orig_block.header.hash())

    block: Block = copy.deepcopy(orig_block)
    while not block.header.mine(args.steps):
        print(f"mining... nonce={block.header.nonce}")

    print("Final block:", block)
    print("Hash:", block.header.hash())


if __name__ == "__main__":
    main()
