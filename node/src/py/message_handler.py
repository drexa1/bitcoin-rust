import uuid
from asyncio import StreamReader, StreamWriter
from datetime import datetime, timezone
import node.src.py.util as util
from lib.src.types.py.block import Block, BlockHeader
from lib.src.types.py.crypto import Hash, MerkleRoot
from lib.src.types.py.transaction import Transaction, TransactionOutput
from lib.src.types.py.network import (
    UTXOs, Template, Difference, TemplateValidity, NodeList,
    FetchBlock, DiscoverNodes, AskDifference, FetchUTXOs, NewBlock,
    NewTransaction, ValidateTemplate, SubmitTemplate, SubmitTransaction,
    FetchTemplate, send_message, receive_message
)

# Maximum of transactions allowed in a block
BLOCK_TRANSACTION_CAP = 20

async def handle(reader: StreamReader, writer: StreamWriter):
    try:
        while True:
            # Read a message from the socket
            try:
                message = await receive_message(reader)
            except Exception as e:
                print(f"Invalid message from peer: {e}, closing connection")
                return

            match message:

                case UTXOs() | Template() | Difference() | TemplateValidity() | NodeList():
                    print("I am neither a miner nor a wallet! Goodbye")
                    writer.close()
                    await writer.wait_closed()
                    return

                case FetchBlock(height=height):
                    blockchain = util.BLOCKCHAIN
                    try:
                        block = blockchain.blocks[height]
                        response = NewBlock(block=block)
                        await send_message(writer, response)
                    except IndexError:
                        return

                case DiscoverNodes():
                    nodes = list(util.NODES.keys())
                    response = NodeList(nodes=nodes)
                    await send_message(writer, response)

                case AskDifference(height=height):
                    blockchain = util.BLOCKCHAIN
                    count = len(blockchain.blocks) - height
                    response = Difference(diff=count)
                    await send_message(writer, response)

                case FetchUTXOs(public_key=public_key):
                    print("Received request to fetch UTXOs")
                    blockchain = util.BLOCKCHAIN
                    utxos = []
                    for _, (marked, tx_out) in blockchain.utxos.items():
                        if tx_out.public_key == public_key:
                            utxos.append((tx_out, marked))
                    response = UTXOs(utxos=utxos)
                    await send_message(writer, response)

                case NewBlock(block=block):
                    blockchain = util.BLOCKCHAIN
                    print("Received new block")
                    try:
                        blockchain.add_block(block)
                    except Exception as e:
                        print(f"Block rejected: {e}")

                case NewTransaction(transaction=transaction):
                    blockchain = util.BLOCKCHAIN
                    print("Received transaction from friend")
                    try:
                        blockchain.add_to_mempool(transaction)
                    except Exception as e:
                        print(f"Transaction rejected, closing connection: {e}")
                        writer.close()
                        await writer.wait_closed()
                        return

                case ValidateTemplate(block=block):
                    blockchain = util.BLOCKCHAIN
                    last_block_hash = blockchain.blocks[-1].hash() if blockchain.blocks else Hash.zero()
                    status = block.header.prev_hash == last_block_hash
                    response = TemplateValidity(valid=status)
                    await send_message(writer, response)

                case SubmitTemplate(block=block):
                    print("Received allegedly mined template")
                    blockchain = util.BLOCKCHAIN
                    try:
                        blockchain.add_block(block)
                    except Exception as e:
                        print(f"Block rejected: {e}, closing connection")
                        writer.close()
                        await writer.wait_closed()
                        return
                    blockchain.rebuild_utxos()
                    print("Block looks good, broadcasting")
                    
                    # Send block to all friend nodes
                    nodes = list(util.NODES.keys())
                    for node in nodes:
                        _, node_writer = util.NODES[node]
                        response = NewBlock(block=block)
                        try:
                            await send_message(node_writer, response)
                        except Exception as e:
                            print(f"failed to send block to {node}: {e}")

                case SubmitTransaction(transaction=transaction):
                    print("Submit tx")
                    blockchain = util.BLOCKCHAIN
                    try:
                        blockchain.add_to_mempool(transaction)
                    except Exception as e:
                        print(f"transaction rejected, closing connection: {e}")
                        writer.close()
                        await writer.wait_closed()
                        return
                    
                    print("Added transaction to mempool")
                    # Send transaction to all friend nodes
                    nodes = list(util.NODES.keys())
                    for node in nodes:
                        print(f"sending to friend: {node}")
                        _, node_writer = util.NODES[node]
                        response = NewTransaction(transaction=transaction)
                        try:
                            await send_message(node_writer, response)
                        except Exception as e:
                            print(f"failed to send transaction to {node}: {e}")
                    print("transaction sent to friends")

                case FetchTemplate(public_key=public_key):
                    blockchain = util.BLOCKCHAIN
                    transactions = []
                    # Insert transactions from mempool
                    transactions.extend([tx for _, tx in blockchain.mempool[:BLOCK_TRANSACTION_CAP]])
                    # Insert coinbase tx with the public key
                    coinbase_tx = Transaction(
                        inputs=[],
                        outputs=[TransactionOutput(
                            public_key=public_key,
                            unique_id=uuid.uuid4(),
                            value=0
                        )]
                    )
                    transactions.insert(0, coinbase_tx)
                    merkle_root = MerkleRoot.calculate(transactions)
                    last_block_hash = blockchain.blocks[-1].hash() if blockchain.blocks else Hash.zero()
                    block = Block(
                        header=BlockHeader(
                            timestamp=datetime.now(timezone.utc),
                            prev_hash=last_block_hash,
                            nonce=0,
                            target=blockchain.target,
                            merkle_root=merkle_root
                        ),
                        transactions=transactions
                    )
                    try:
                        miner_fees = block.calculate_miner_fees(blockchain.utxos)
                    except Exception as e:
                        print(f"{e}")
                        return
                    # Reward calculation: 50 * 10^8 / 2^(height / 210)
                    predicted_height = len(blockchain.blocks)
                    reward = (50 * 10**8) // (2**(predicted_height // 210))
                    # Update coinbase tx with reward
                    block.transactions[0].outputs[0].value = reward + miner_fees
                    # Recalculate merkle root
                    block.header.merkle_root = MerkleRoot.calculate(block.transactions)
                    response = Template(block=block)
                    await send_message(writer, response)
    finally:
        writer.close()
        await writer.wait_closed()
