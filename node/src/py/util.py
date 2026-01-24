import asyncio
from asyncio import StreamReader, StreamWriter
from datetime import datetime, timezone
from typing import Dict, Tuple
from lib.src.types.py.blockchain import Blockchain
from lib.src.types.py.network import (
    DiscoverNodes, NodeList, AskDifference, Difference,
    FetchBlock, NewBlock, send_message, receive_message
)

# Global state similar to Rust static variables
BLOCKCHAIN = Blockchain()
NODES: Dict[str, Tuple[StreamReader, StreamWriter]] = {}


async def load_blockchain(blockchain_file: str) -> None:
    """ Load blockchain from file and rebuild UTXOs. """
    print("Blockchain file exists, loading...")
    new_blockchain = Blockchain.load(blockchain_file)
    print("Blockchain loaded")
    global BLOCKCHAIN
    BLOCKCHAIN = new_blockchain
    print("Rebuilding UTXOs...")
    BLOCKCHAIN.rebuild_utxos()
    print("Checking if target needs to be adjusted...")
    print(f"Current target: {BLOCKCHAIN.target}")
    BLOCKCHAIN.try_adjust_target()
    print(f"New target: {BLOCKCHAIN.target}")
    print("Initialization complete")


async def populate_connections(nodes: list[str]) -> None:
    """ Connect to other nodes and discover more nodes. """
    print("Trying to connect to other nodes...")
    for node in nodes:
        print(f"Connecting to {node}")
        reader, writer = await asyncio.open_connection(node.split(':')[0], int(node.split(':')[1]))
        message = DiscoverNodes()
        await send_message(writer, message)
        print(f"Sent 'DiscoverNodes' to {node}")
        response = await receive_message(reader)
        if isinstance(response, NodeList):
            print(f"Received 'NodeList' from {node}")
            for child_node in response.nodes:
                print(f"Adding node {child_node}")
                child_reader, child_writer = await asyncio.open_connection(child_node.split(':')[0], int(child_node.split(':')[1]))
                NODES[child_node] = (child_reader, child_writer)
        else:
            print(f"Unexpected message from {node}")
        NODES[node] = (reader, writer)


async def find_longest_chain_node() -> Tuple[str, int]:
    """ Find the node with the longest blockchain. """
    print("Finding nodes with the highest blockchain length...")
    longest_name = ""
    longest_count = 0
    all_nodes = list(NODES.keys())
    for node in all_nodes:
        print(f"Asking {node} for blockchain length")
        reader, writer = NODES[node]
        message = AskDifference(height=0)
        await send_message(writer, message)
        print(f"Sent 'AskDifference' to {node}")
        response = await receive_message(reader)
        if isinstance(response, Difference):
            print(f"Received 'Difference' from {node}")
            if response.diff > longest_count:
                print(f"New longest blockchain: {response.diff} blocks from {node}")
                longest_count = response.diff
                longest_name = node
        else:
            print(f"Unexpected message from {node}: {response}")
    return longest_name, longest_count


async def download_blockchain(node: str, count: int) -> None:
    """ Download blocks from a node. """
    reader, writer = NODES[node]
    for i in range(count):
        message = FetchBlock(height=i)
        await send_message(writer, message)
        response = await receive_message(reader)
        if isinstance(response, NewBlock):
            global BLOCKCHAIN
            BLOCKCHAIN.add_block(response.block)
        else:
            print(f"Unexpected message from {node}")


async def cleanup() -> None:
    """ Periodically clean up old transactions from mempool. """
    while True:
        await asyncio.sleep(30)
        now = datetime.now(timezone.utc)
        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')}> Cleaning mempool old transactions")
        global BLOCKCHAIN
        BLOCKCHAIN.cleanup_mempool()


async def save(blockchain_file: str) -> None:
    """ Periodically save blockchain to disk. """
    while True:
        await asyncio.sleep(15)
        now = datetime.now(timezone.utc)
        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')}> Saving blockchain to disk...")
        global BLOCKCHAIN
        BLOCKCHAIN.save(blockchain_file)