from dotenv import load_dotenv
from xian_blockchain_agent.utils.block import BlockReader
from xian_blockchain_agent.utils.tx import TXReader
from xian_blockchain_agent.utils.contract import ContractReader
load_dotenv()
import aiohttp
import asyncio
import os
import re

class Agent:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.block_reader = BlockReader(os.getenv('NODE'))
        self.tx_reader = TXReader(os.getenv('NODE'))
        self.contract_reader = ContractReader(os.getenv('NODE'))

        self.model = "gpt-4o-mini"
        self.default_messages = [
            {
                "role": "system",
                "content": '''
                Guidelines:
                - You are interacting with the Xian blockchain.
                - ALWAYS respond with specific function calls for blockchain actions.
                - Available functions:
                    - `read_block_by_height(height)`
                    - `read_block_by_hash(hash)`
                    - `read_tx_by_hash(hash)`
                    - `read_contract_by_name(contract_name)`
                    - `read_hash_key_value(contract_name, hash, *keys)`
                    - `read_variable_value(contract_name, variable_name)`
                - Your responses should:
                    - Start with the natural language explanation of what you're doing.
                    - Include the exact function to call for the requested action, using the appropriate parameters.
                - Example response:
                    User: How much balance does 13ca9a62... have in the contract "currency"?
                    AI: I will fetch the balance for the address `13ca9a62...` from the "currency" contract.
                        Function: `read_hash_key_value("currency", "balances", "13ca9a62...")`
                '''
            }
        ]
        self.conversation_history = []

    async def ask_ai(self, message: str):
        self.conversation_history.append({"role": "user", "content": message})
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    }, json={
                        "model": self.model,
                        "messages": self.default_messages + self.conversation_history,
                        "temperature": 0.7,
                    }) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        answer = response_json['choices'][0]['message']['content']

                        # Extract function calls
                        match = re.search(r'Function: `(.*?)`', answer)
                        if match:
                            function_call = match.group(1)
                            print(f"Executing function: {function_call}")
                            await self.handle_command(function_call)
                            # Append to history only after successful execution
                            self.conversation_history.append({"role": "assistant", "content": answer})
                            return "Function executed successfully."

                        # No function to execute, print the response
                        self.conversation_history.append({"role": "assistant", "content": answer})
                        return answer
                    else:
                        return f"Error: {response.status}, {await response.text()}"
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"An error occurred: {e}"



    async def handle_command(self, message: str):
        """
        Parses the AI response to identify and execute blockchain commands.
        """
        try:
            # Match the function call and extract parameters
            match = re.search(r'(read_variable_value|read_hash_key_value|read_contract_by_name|read_tx_by_hash|read_block_by_height|read_block_by_hash)\((.*?)\)', message)
            if match:
                command, param_string = match.groups()
                param_parts = re.split(r',\s*(?![^()]*\))', param_string)
                params = [eval(part) for part in param_parts]  # Convert parameter string into values

                if command == "read_contract_by_name":
                    contract_name = params[0]
                    contract = await self.contract_reader.read_contract_by_name(contract_name)
                    print(f"Contract fetched: {contract}")
                
                elif command == "read_variable_value":
                    contract_name, variable_name = params[:2]
                    contract = await self.contract_reader.read_contract_by_name(contract_name)
                    if variable_name not in contract["variable_orm"]:
                        print(f"Variable '{variable_name}' does not exist in contract '{contract_name}'.")
                        return
                    value = await self.contract_reader.read_variable_value(contract_name, variable_name)
                    print(f"Variable value fetched: {value}")
                
                elif command == "read_hash_key_value":
                    contract_name, hash_name, *keys = params
                    contract = await self.contract_reader.read_contract_by_name(contract_name)
                    if hash_name not in contract["hash_orm"]:
                        print(f"Hash '{hash_name}' does not exist in contract '{contract_name}'.")
                        return
                    value = await self.contract_reader.read_hash_key_value(contract_name, hash_name, *keys)
                    if value is None:
                        print(f"Error fetching hash key value for {contract_name}.{hash_name} with keys {keys}.")
                    else:
                        print(f"Value fetched: {value}")
                elif command == "read_tx_by_hash":
                    tx_hash = params[0]
                    tx = await self.tx_reader.read_tx_by_hash(tx_hash)
                    print(f"Transaction fetched: {tx}")
                elif command == "read_block_by_height":
                    block_height = params[0]
                    block = await self.block_reader.read_block_by_height(block_height)
                    print(f"Block fetched: {block}")
            else:
                print("Invalid function call format.")
        except Exception as e:
            print(f"Error executing command: {e}")
       
    async def loop(self):
        print("Agent initialized. Type 'exit' to quit.")
        while True:
            question = input("What do you want to ask? ").strip()
            if question.lower() == "exit":
                print("Exiting... Goodbye!")
                break
            elif not question:
                print("Please enter a valid question.")
                continue

            answer = await self.ask_ai(question)
            print(f"AI: {answer}")
            print("\n")

    def run(self):
        asyncio.run(self.loop())


if __name__ == "__main__":

    agent = Agent()
    agent.run()
