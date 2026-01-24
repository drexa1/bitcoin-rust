import asyncio
import queue
import copy
from asyncio import StreamReader, StreamWriter
from threading import Thread, Lock, Event
from typing import Optional
from lib.src.types.py.crypto import PublicKey
from lib.src.types.py.block import Block
from lib.src.types.py.network import (
    send_message,
    receive_message,
    FetchTemplate,
    Template,
    ValidateTemplate,
    TemplateValidity,
    SubmitTemplate,
)

MINING_STEPS=10_000


class Miner:
    def __init__(self, reader: StreamReader, writer: StreamWriter, public_key: PublicKey,):
        self.public_key = public_key
        self.node_reader  = reader
        self.node_writer  = writer
        self._template_lock = Lock()  # shared state between async loop and mining thread
        self.mining = Event()
        self.current_template: Optional[Block] = None
        self.mined_blocks: queue.Queue[Block] = queue.Queue()
        self._start_mining_thread()

    @classmethod
    async def connect(cls, address: str, port: int, public_key: PublicKey) -> "Miner":
        reader, writer = await asyncio.open_connection(address, port)
        return cls(reader, writer, public_key)

    async def run(self) -> None:
        """ Main loop. """
        await asyncio.gather(self._template_loop(), self._submit_loop())

    async def _template_loop(self) -> None:
        while True:
            if not self.mining.is_set():
                # If not mining, fetch a new template block from the node
                await self._fetch_template()
            else:
                # If mining, check if the template block is still valid
                # - another miner already mined a block
                # - transactions change (double spend, replaced fee, ...)
                # - consensus may invalidate blocks after rules updates
                await self._validate_template()
            await asyncio.sleep(5)

    async def _submit_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            # Wait for a mined block, then submit it
            block = await loop.run_in_executor(None, self.mined_blocks.get, True, None)
            await self._submit_block(block)

    def _start_mining_thread(self) -> None:
        """ Mining thread. """
        def worker():
            while True:
                self.mining.wait()  # Wait until receiving a request to start mining
                with self._template_lock:
                    template = self.current_template
                if template is None:
                    continue
                block = copy.deepcopy(template)
                print(f"Mining block with target: {block.header.target}")
                if block.header.mine(steps=MINING_STEPS):
                    print(f"Block mined: {block.hash()}")
                    self.mined_blocks.put(block)
                    self.mining.clear()
        Thread(target=worker, daemon=True).start()

    async def _fetch_template(self) -> None:
        print("Fetching new template")
        await send_message(self.node_writer, FetchTemplate(public_key=self.public_key))
        msg = await receive_message(self.node_reader)
        if not isinstance(msg, Template):
            raise RuntimeError("Unexpected message while fetching template")
        print(f"Received new template with target: {msg.block.header.target}")
        with self._template_lock:
            self.current_template = msg.block
        self.mining.set()  # Start!

    async def _validate_template(self) -> None:
        with self._template_lock:
            template = self.current_template
        if template is None:
            return
        await send_message(self.node_writer, ValidateTemplate(block=template), )
        msg = await receive_message(self.node_reader)
        if not isinstance(msg, TemplateValidity):
            raise RuntimeError("Unexpected message while validating template")
        if not msg.valid:
            print("Template invalidated")
            with self._template_lock:
                self.current_template = None
            self.mining.clear()  # Done!
        else:
            print("Template still valid")

    async def _submit_block(self, block: Block) -> None:
        print("Submitting new block!")
        await send_message(self.node_writer, SubmitTemplate(block=block))
        self.mining.clear()
