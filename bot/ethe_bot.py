import telebot
import logging
import asyncio
import threading

from utils.utils import logger
from events.event_listener import EventListener
from settings.settings import BOT_TOKEN, CHAT_ID
from events.history_fetcher import HistoryFetcher
from database.database import get_last_processed_block_from_database

bot = telebot.TeleBot(BOT_TOKEN)


class TelegramLogHandler(logging.Handler):
    def __init__(self, chat_id):
        super().__init__()
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        bot.send_message(self.chat_id, log_entry)


handler = TelegramLogHandler(CHAT_ID)
logger.addHandler(handler)


def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    last_block = get_last_processed_block_from_database()
    fetcher = HistoryFetcher(last_block)
    loop.run_until_complete(fetcher.fetch_history())
    bot.send_message(CHAT_ID, f"History has been fetched up to block {last_block}")

    listener = EventListener()
    loop.run_until_complete(listener.listen_for_event())
    loop.close()


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Fetching history and starting to listen for events...")
    threading.Thread(target=start_async_loop).start()


if __name__ == '__main__':
    bot.infinity_polling()
