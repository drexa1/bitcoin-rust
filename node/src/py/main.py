import asyncio
import argparse
import os
import node.src.py.util as util
import node.src.py.message_handler as message_handler

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=9000, help="Port to listen on")
    parser.add_argument("-f", "--blockchain-file", type=str, help="Path to blockchain file")
    parser.add_argument("nodes", nargs="*", help="Known nodes to connect to")
    args = parser.parse_args()
    port = args.port
    blockchain_file = args.blockchain_file
    nodes = args.nodes

    await util.populate_connections(nodes)
    print(f"Known nodes: {len(util.NODES)}")
    # Check if the blockchain_file exists
    if os.path.exists(blockchain_file):
        await util.load_blockchain(blockchain_file)
    else:
        print("Blockchain file does not exist!")
        if not nodes:
            print("No nodes provided, starting as a seed node")
        else:
            longest_name, longest_count = await util.find_longest_chain_node()
            if longest_name:
                # Request the blockchain from the node with the longest blockchain
                await util.download_blockchain(longest_name, longest_count)
                print(f"blockchain downloaded from {longest_name}")
                # Rebuild UTXOs and adjust target
                util.BLOCKCHAIN.rebuild_utxos()
                util.BLOCKCHAIN.try_adjust_target()
            else:
                print("Could not find any nodes to download blockchain from")

    # Start the listener
    server = await asyncio.start_server(message_handler.handle, "0.0.0.0", port)
    print(f"Listening on 0.0.0.0:{port}")
    # Start background tasks
    asyncio.create_task(util.cleanup())
    asyncio.create_task(util.save(blockchain_file))
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
