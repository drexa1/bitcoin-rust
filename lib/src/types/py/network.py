import struct
from asyncio import StreamWriter, StreamReader
from typing import List, Tuple, Union
import cbor2
from pydantic import BaseModel
from crypto import PublicKey
from lib.src.types.py import Block, Transaction, TransactionOutput


class FetchUTXOs(BaseModel):
    public_key: PublicKey


class UTXOs(BaseModel):
    utxos: List[Tuple[TransactionOutput, bool]]


class SubmitTransaction(BaseModel):
    transaction: Transaction


class NewTransaction(BaseModel):
    transaction: Transaction


class FetchTemplate(BaseModel):
    public_key: PublicKey


class Template(BaseModel):
    block: Block


class ValidateTemplate(BaseModel):
    block: Block


class TemplateValidity(BaseModel):
    valid: bool


class SubmitTemplate(BaseModel):
    block: Block


class DiscoverNodes(BaseModel):
    pass


class NodeList(BaseModel):
    nodes: List[str]


class AskDifference(BaseModel):
    height: int


class Difference(BaseModel):
    diff: int


class FetchBlock(BaseModel):
    height: int


class NewBlock(BaseModel):
    block: Block


Message = Union[
    FetchUTXOs,
    UTXOs,
    SubmitTransaction,
    NewTransaction,
    FetchTemplate,
    Template,
    ValidateTemplate,
    TemplateValidity,
    SubmitTemplate,
    DiscoverNodes,
    NodeList,
    AskDifference,
    Difference,
    FetchBlock,
    NewBlock,
]

def encode_message(msg: Message) -> bytes:
    payload = { "type": msg.__class__.__name__, "data": msg.model_dump() }
    return cbor2.dumps(payload)


def decode_message(data: bytes) -> Message:
    payload = cbor2.loads(data)
    msg_type = payload["type"]
    data = payload["data"]
    cls = globals()[msg_type]
    return cls(**data)

async def send_message(writer: StreamWriter, msg: Message) -> None:
    encoded = encode_message(msg)
    writer.write(struct.pack(">Q", len(encoded)))
    writer.write(encoded)
    await writer.drain()


async def receive_message(reader: StreamReader) -> Message:
    raw_len = await reader.readexactly(8)
    (length, ) = struct.unpack(">Q", raw_len)
    data = await reader.readexactly(length)
    return decode_message(data)
