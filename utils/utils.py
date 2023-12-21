import logging
from web3 import Web3

from database.database import insert_event_into_database, event_exists
from settings.settings import PROVIDER_URL, CONTRACT_ADDRESS, CONTRACT_ABI, DISTRIBUTOR_WALLET

web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

event_signature = "TotalDistribution(uint256,uint256,uint256,uint256)"
event_signature_hash = Web3.keccak(text=event_signature).hex()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_event_filter(from_block, to_block):
    logger.info(f"Creating event filter from {from_block} to {to_block}")

    if isinstance(from_block, int):
        from_block = hex(from_block)

    if isinstance(to_block, int):
        to_block = hex(to_block)

    event_filter = web3.eth.filter({
        'address': CONTRACT_ADDRESS,
        'fromBlock': from_block,
        'toBlock': to_block,
        'topics': [event_signature_hash]
    })

    logger.info("Event filter created")
    return event_filter


def handle_event(event):
    logger.info(f"Processing event: {event}")
    decoded_data = contract.events.TotalDistribution().process_log(event)
    logger.info(f"Decoded data: {decoded_data}")

    block_number = event['blockNumber']
    transaction_hash = event['transactionHash'].hex()
    if event_exists(transaction_hash):
        return
    block = web3.eth.get_block(block_number)
    block_timestamp = block['timestamp']

    input_aix_amount = decoded_data.args.inputAixAmount / 10**18
    distributed_aix_amount = decoded_data.args.distributedAixAmount / 10**18
    swapped_eth_amount = decoded_data.args.swappedEthAmount / 10**18
    distributed_eth_amount = decoded_data.args.distributedEthAmount / 10**18

    insert_event_into_database(block_number, transaction_hash, block_timestamp,
                               input_aix_amount, distributed_aix_amount,
                               swapped_eth_amount, distributed_eth_amount)


def get_distributor_balance():
    balance = web3.eth.get_balance(DISTRIBUTOR_WALLET) / 10 ** 18
    return balance
