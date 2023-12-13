import asyncio

from settings.settings import START_BLOCK_ID
from utils.utils import create_event_filter, handle_event, logger
from database.database import get_last_processed_block


class HistoryFetcher:
    def __init__(self):
        self.from_block = get_last_processed_block()
        if self.from_block is None:
            self.from_block = START_BLOCK_ID
        else:
            self.from_block += 1

    async def fetch_history(self):
        event_filter = create_event_filter(START_BLOCK_ID, 'latest')
        events = event_filter.get_all_entries()
        logger.info(f"Fetched {len(events)} events")

        if not events:
            logger.info("No new events to fetch.")
            return

        for event in events:
            handle_event(event)


async def main():
    fetcher = HistoryFetcher()
    await fetcher.fetch_history()


if __name__ == '__main__':
    asyncio.run(main())
