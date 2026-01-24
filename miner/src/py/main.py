import asyncio
import argparse
from lib.src.types.py.crypto import PublicKey
from miner.src.py.miner import Miner


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", required=True, help="Node address (host:port)")
    parser.add_argument("-p", "--public_key_file", required=True, help="Path to public key file")
    args = parser.parse_args()

    try:
        public_key = PublicKey.load_from_file(args.public_key_file)
    except Exception as e:
        raise RuntimeError(f"Error reading public key: {e}")

    miner = await Miner.connect(args.address.split(":")[0], int(args.address.split(":")[1]), public_key)
    await miner.run()


if __name__ == "__main__":
    asyncio.run(main())