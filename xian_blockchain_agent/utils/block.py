import aiohttp
import base64
import json

class BlockReader:
    def __init__(self, node):
        self.node = node

    def decode_block_txs(self, block_data):
        if len(block_data["result"]["block"]["data"]["txs"]) > 0:
            for tx in block_data["result"]["block"]["data"]["txs"]:
                tx_decoded_base64 = base64.b64decode(tx)
                tx_str = tx_decoded_base64.decode("utf-8")
                bytes_from_tx_str = bytes.fromhex(tx_str)
                tx_str = bytes_from_tx_str.decode("utf-8")
                tx_json = json.loads(tx_str)
                block_data["result"]["block"]["data"]["txs"][block_data["result"]["block"]["data"]["txs"].index(tx)] = tx_json
        return block_data

    async def read_block_by_height(self, block_height):
        url = f"{self.node}/block?height={block_height}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                block_data = await response.json()
                block_data = self.decode_block_txs(block_data)
                return block_data

    async def read_block_by_hash(self, block_hash):
        url = f"{self.node}/block_by_hash?hash=0x{block_hash}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                block_data = await response.json()
                block_data = self.decode_block_txs(block_data)
                return block_data
