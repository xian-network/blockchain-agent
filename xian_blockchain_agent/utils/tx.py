import aiohttp
import base64
import json

class TXReader:
    def __init__(self, node):
        self.node = node

    def decode_tx_data(self, tx_data):
        data = tx_data["result"]["tx_result"]["data"]
        tx_decoded_base64 = base64.b64decode(data)
        tx_str = tx_decoded_base64.decode("utf-8")
        tx_json = json.loads(tx_str)
        tx_data["result"]["tx_result"]["data"] = tx_json
        return tx_data

    async def read_tx_by_hash(self, tx_hash):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.node}/tx?hash=0x{tx_hash}") as response:
                tx = await response.json()
                return self.decode_tx_data(tx)