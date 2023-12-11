import asyncio

from events.history_fetcher import HistoryFetcher
from database.database import get_last_event_timestamp
from utils.utils import create_event_filter, logger, handle_event


class EventListener:
    def __init__(self):
        self.last_timestamp = get_last_event_timestamp()

    async def listen_for_event(self):
        while True:
            try:
                event_filter = create_event_filter(self.last_timestamp, 'latest')

                for event in event_filter.get_new_entries():
                    handle_event(event)

            except Exception as e:
                logger.error(f"Error in listening for event: {e}")

            await asyncio.sleep(10)


async def main():
    listener = EventListener()
    fetcher = HistoryFetcher()

    await asyncio.gather(
        listener.listen_for_event(),
        fetcher.fetch_history()
    )


if __name__ == '__main__':
    asyncio.run(main())
