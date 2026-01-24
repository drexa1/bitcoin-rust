import asyncio
import argparse
from miner import Miner
from lib.src.types.py.crypto import PublicKey


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", required=True, help="Node address (host:port)")
    parser.add_argument("-p", "--public-key-file", required=True, help="Path to public key file")
    args = parser.parse_args()

    try:
        public_key = PublicKey.load_from_file(args.public_key_file)
    except Exception as e:
        raise RuntimeError(f"Error reading public key: {e}")

    node_host = args.address.split(":")[0]
    node_port = int(args.address.split(":")[1])
    miner = await Miner.connect(node_host, node_port, public_key)
    await miner.run()


if __name__ == "__main__":
    asyncio.run(main())