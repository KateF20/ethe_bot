import telebot
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from utils.utils import logger
from events.event_listener import EventListener
from settings.settings import BOT_TOKEN, CHAT_ID, START_BLOCK_ID
from events.history_fetcher import HistoryFetcher
from database.database import get_last_event_timestamp, get_24hr_sums

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

    fetcher = HistoryFetcher(START_BLOCK_ID)
    loop.run_until_complete(fetcher.fetch_history())

    listener = EventListener()
    loop.run_until_complete(listener.listen_for_event())
    loop.close()


def fetch_and_send_stats():
    try:
        sums = get_24hr_sums()
        send_stats(*sums)

    except Exception as e:
        logger.error(f"Error in fetch_and_send_stats: {e}")
        bot.send_message(CHAT_ID, "An error occurred while fetching the stats.")


def send_stats(input_aix, aix_distributed, swapped_eth, distributed_eth):
    message = (
        "$AIX stats since inception:\n"
        f" - AIX processed: {input_aix}\n"
        f" - AIX distributed: {aix_distributed}\n"
        f" - ETH swapped: {swapped_eth}\n"
        f" - ETH distributed: {distributed_eth}"
    )
    bot.send_message(CHAT_ID, message)


@bot.message_handler(commands=['start'])
def start_command(message):
    last_event_timestamp = get_last_event_timestamp()
    # if last_event_timestamp and last_event_timestamp != (datetime.now() - timedelta(days=1)).timestamp():
    #     bot.reply_to(message, "History is up to date.")
    # else:
    bot.reply_to(message, "History is not up to date. Fetching history...")
    threading.Thread(target=start_async_loop).start()


@bot.message_handler(commands=['total'])
def total_command(message):
    fetch_and_send_stats()


def scheduled_task():
    fetch_and_send_stats()


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', hours=1)
    scheduler.start()

    bot.infinity_polling()
