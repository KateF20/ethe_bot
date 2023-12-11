import json
from os import getenv
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / 'config' / '.env'
abi_path = Path(__file__).parent.parent / 'config' / 'abi.json'

load_dotenv(dotenv_path=env_path)

PROVIDER_URL = getenv('PROVIDER_URL')
CONTRACT_ADDRESS = getenv('CONTRACT_ADDRESS')

with abi_path.open() as abi_file:
    CONTRACT_ABI = json.load(abi_file)

BOT_TOKEN = getenv('BOT_TOKEN')
CHAT_ID = getenv('CHAT_ID')

START_BLOCK_ID = int(getenv('START_BLOCK_ID'))

DB_NAME = getenv('DB_NAME')
DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')
