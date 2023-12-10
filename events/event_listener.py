import asyncio

from utils.utils import create_event_filter, logger, handle_event
from database.database import get_last_processed_block_from_database


class EventListener:
    def __init__(self):
        self.last_block = get_last_processed_block_from_database()

    async def listen_for_event(self):
        while True:
            try:
                event_filter = create_event_filter(self.last_block, 'latest')

                for event in event_filter.get_new_entries():
                    handle_event(event)

            except Exception as e:
                logger.error(f"Error in listening for event: {e}")
                await asyncio.sleep(10)


async def main():
    listener = EventListener()
    await listener.listen_for_event()


if __name__ == '__main__':
    asyncio.run(main())
