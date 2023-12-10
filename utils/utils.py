import logging
from web3 import Web3

from database.database import insert_event_into_database
from settings.settings import PROVIDER_URL, CONTRACT_ADDRESS

web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
contract_address = CONTRACT_ADDRESS
event_signature = "TotalDistribution(uint256,uint256,uint256,uint256)"
event_signature_hash = Web3.keccak(text=event_signature).hex()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_event_filter(from_block, to_block):
    if isinstance(from_block, int):
        from_block = hex(from_block)

    return web3.eth.filter({
        'address': contract_address,
        'fromBlock': from_block,
        'toBlock': to_block,
        'topics': [event_signature_hash]
    })


def handle_event(event):
    block_number = event['blockNumber']
    transaction_hash = event['transactionHash'].hex()
    data = event['data']

    if isinstance(data, bytes):
        data = data.hex()

    input_aix_amount = int(data[0:64], 16)
    distributed_aix_amount = int(data[64:128], 16)
    swapped_eth_amount = int(data[128:192], 16)
    distributed_eth_amount = int(data[192:256], 16)

    insert_event_into_database(block_number, transaction_hash,
                               input_aix_amount, distributed_aix_amount,
                               swapped_eth_amount, distributed_eth_amount)
