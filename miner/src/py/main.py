import copy
import sys
from pathlib import Path
from lib.src.types.py.block import Block, BlockHeader


def main():
    # Parse block path and steps count arguments
    if len(sys.argv) != 3:
        print("Usage: miner <block_file> <steps>", file=sys.stderr)
        sys.exit(1)
    else:
        path = Path(sys.argv[1])
        steps = int(sys.argv[2])
    og_block: Block = Block.load(path)
    block: Block = copy.deepcopy(og_block)
    while not block.header.mine(steps):
        print(f"mining... nonce={block.header.nonce}")
    # Print original block and its hash
    print("original:", repr(og_block))
    print("hash:", og_block.header.hash())
    # Print mined block and its hash
    print("final:", repr(block))
    print("hash:", block.header.hash())


if __name__ == "__main__":
    main()
