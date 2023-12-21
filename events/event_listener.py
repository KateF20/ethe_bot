import asyncio

from events.history_fetcher import HistoryFetcher
from database.database import get_last_processed_block
from utils.utils import create_event_filter, logger, handle_event, web3, contract


class EventListener:
    def __init__(self):
        self.last_block = get_last_processed_block()
        logger.info(f"EventListener initialized with last timestamp: {self.last_block}")

    async def listen_for_event(self):
        while True:
            try:
                logger.info(f"Latest block on the blockchain: {self.last_block}")

                logger.info("Listening for new events...")
                event_filter = create_event_filter(self.last_block, 'latest')
                new_entries = event_filter.get_new_entries()
                logger.info(f"Found {len(new_entries)} new events")

                for event in event_filter.get_new_entries():
                    logger.info(f"Handling event: {event}")
                    handle_event(event)

            except Exception as e:
                logger.error(f"Error in listening for event: {e}")

            await asyncio.sleep(60)


async def main():
    listener = EventListener()
    fetcher = HistoryFetcher()

    await asyncio.gather(
        listener.listen_for_event(),
        fetcher.fetch_history()
    )


if __name__ == '__main__':
    asyncio.run(main())
