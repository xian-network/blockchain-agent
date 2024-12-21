import aiohttp
import base64
import json
import re

class ContractReader:
    def __init__(self, node):
        self.node = node

    def decode_data(self, data):
        try:
            if not data or 'result' not in data or 'response' not in data['result'] or 'value' not in data['result']['response']:
                raise ValueError("Missing or malformed response data.")
            return base64.b64decode(data['result']['response']['value']).decode('utf-8')
        except Exception as e:
            return "Nothing stored in this key."

    def find_all_hash_orm(self, contract):
        pattern = r"Hash\(.*?name='(.*?)'\)"
        return re.findall(pattern, contract)

    def find_all_variable_orm(self, contract):
        pattern = r"Variable\(.*?name='(.*?)'\)"
        return re.findall(pattern, contract)

    async def read_hash_key_value(self, contract_name, hash_name, *keys):
        built_key = f"{contract_name}.{hash_name}:{':'.join(keys)}"  # e.g., "contract_name.hash_name:key1:key2:key3"
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.node}/abci_query?path="/get/{built_key}"') as response:
                data = await response.json()
                if not data or 'result' not in data or 'response' not in data['result'] or 'value' not in data['result']['response']:
                    print(f"Key {built_key} not found or malformed response.")
                    return None
                return self.decode_data(data)


    async def read_variable_value(self, contract_name, variable_name):
        built_key = f"{contract_name}.{variable_name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.node}/abci_query?path="/get/{built_key}"') as response:
                return self.decode_data(await response.json())

    async def read_contract_by_name(self, contract_name):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.node}/abci_query?path="/contract/{contract_name}"') as response:
                contract = await response.json()
                if 'result' not in contract or 'response' not in contract['result']:
                    print("Invalid response structure:", contract)
                    return None
                code = self.decode_data(contract)
                if code is None:
                    print("Failed to decode contract data.")
                    return None
                hash_orm = self.find_all_hash_orm(code)
                variable_orm = self.find_all_variable_orm(code)
                return {"code": code, "hash_orm": hash_orm, "variable_orm": variable_orm}
