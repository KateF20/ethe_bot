import time
import logging
import threading
from web3 import Web3

from database.database import insert_event_into_database, event_exists, get_last_event
from settings.settings import PROVIDER_URL, CONTRACT_ADDRESS, CONTRACT_ABI, DISTRIBUTOR_WALLET, START_BLOCK_ID

web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def handle_event(event):
    logger.info(f"Processing event: {event}")

    block_number = event['blockNumber']
    transaction_hash = event['transactionHash'].hex()
    if event_exists(transaction_hash):
        return

    block = web3.eth.get_block(block_number)
    block_timestamp = block['timestamp']

    input_aix_amount = event['args']['inputAixAmount'] / 10**18
    distributed_aix_amount = event['args']['distributedAixAmount'] / 10**18
    swapped_eth_amount = event['args']['swappedEthAmount'] / 10**18
    distributed_eth_amount = event['args']['distributedEthAmount'] / 10**18

    insert_event_into_database(block_number, transaction_hash, block_timestamp,
                               input_aix_amount, distributed_aix_amount,
                               swapped_eth_amount, distributed_eth_amount)


async def start_history_fetcher():
    logger.info('started fetching history')
    last_processed_block = get_last_event().block_number if get_last_event() else START_BLOCK_ID

    event_filter = contract.events.TotalDistribution.create_filter(fromBlock=START_BLOCK_ID)
    events = event_filter.get_all_entries()
    latest_block_number = events[-1]['blockNumber']

    if int(last_processed_block) < int(latest_block_number):
        events_to_process = fetch_events(last_processed_block, latest_block_number)
        logger.info(f'last block in DB: {last_processed_block}, last block on contract: {latest_block_number}')

        for event in events_to_process:
            logger.info(f'event to handle: {event}')
            handle_event(event)
        logger.info(f"Processed historical events up to block {latest_block_number}")


def fetch_events(start_block, end_block):
    event_filter = contract.events.TotalDistribution.create_filter(fromBlock=start_block, toBlock=end_block)
    logger.info(f'there some events {event_filter.get_all_entries()}')

    return event_filter.get_all_entries()


async def start_event_listener():
    event_filter = contract.events.TotalDistribution.create_filter(fromBlock='latest')
    logger.info("Staked event filter created successfully.")

    while True:
        try:
            logger.info('started listening to new events')
            events = event_filter.get_new_entries()
            for event in events:
                handle_event(event)
            if events:
                logger.info(f"Processed {len(events)} new events.")

            time.sleep(60)

        except Exception as e:
            logger.error(f"Error processing new events: {e}")


def get_distributor_balance():
    balance = web3.eth.get_balance(DISTRIBUTOR_WALLET) / 10 ** 18
    return balance


if __name__ == '__main__':
    history_thread = threading.Thread(target=start_history_fetcher)
    listener_thread = threading.Thread(target=start_event_listener)

    history_thread.start()
    listener_thread.start()

    history_thread.join()
    listener_thread.join()
