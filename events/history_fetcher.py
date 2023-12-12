import asyncio

from utils.utils import create_event_filter, handle_event, logger
from settings.settings import START_BLOCK_ID


class HistoryFetcher:
    def __init__(self, start_block):
        self.start_block = start_block

    async def fetch_history(self):
        event_filter = create_event_filter(self.start_block, 'latest')
        events = event_filter.get_all_entries()
        logger.info(f"Fetched {len(events)} events")

        if not events:
            logger.info("No new events to fetch.")
            return

        for event in events:
            handle_event(event)


async def main():
    fetcher = HistoryFetcher(START_BLOCK_ID)
    await fetcher.fetch_history()


if __name__ == '__main__':
    asyncio.run(main())
