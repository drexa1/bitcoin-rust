import sys
from lib.src.types.py.block import Block


def main():
    # Parse block path and steps count arguments
    if len(sys.argv) != 3:
        path = sys.argv[1]
        steps = int(sys.argv[2])
    else:
        print("Usage: miner <block_file> <steps>", file=sys.stderr)
        sys.exit(1)
    og_block = Block.load_from_file(path)
    block = og_block.clone()
    while not block.header.mine(steps):
        print("mining...")
    # Print original block and its hash
    print("original:", repr(og_block))
    print("hash:", og_block.header.hash())
    # Print mined block and its hash
    print("final:", repr(block))
    print("hash:", block.header.hash())


if __name__ == "__main__":
    main()
