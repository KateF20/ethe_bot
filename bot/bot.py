import telebot
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.utils import logger, get_distributor_balance, start_event_listener, start_history_fetcher
from settings.settings import BOT_TOKEN, DISTRIBUTOR_WALLET
from database.database import get_last_event, get_first_event, get_start_of_24hr_period_timestamp, \
    get_24hr_sums, get_total_sums, is_subscribed, add_subscriber, remove_subscriber, get_all_subscribers

bot = telebot.TeleBot(BOT_TOKEN)

is_listening = False


class TelegramLogHandler(logging.Handler):
    def emit(self, record):
        try:
            chat_id = record.args[0]
            log_entry = self.format(record)
            bot.send_message(chat_id, log_entry)
        except Exception as e:
            print(e)


handler = TelegramLogHandler()
logger.addHandler(handler)


def make_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Total", callback_data="total"),
               InlineKeyboardButton("Today", callback_data="today"),
               InlineKeyboardButton("Subscribe", callback_data="subscribe"),
               InlineKeyboardButton("Unsubscribe", callback_data="unsubscribe")
               )

    return markup


def make_welcome_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Start", callback_data="start"))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "start":
        bot.send_message(chat_id,
                         "What do you need? Total statistics or all the info for today?",
                         reply_markup=make_menu_keyboard())
    elif call.data == "total":
        fetch_and_send_stats(chat_id, include_distributor_info=False, is_total=True)

    elif call.data == "today":
        fetch_and_send_stats(chat_id, include_distributor_info=True)

    elif call.data == "subscribe":
        if is_subscribed(chat_id):
            bot.send_message(chat_id, "You're already subscribed to hourly updates.")
        else:
            add_subscriber(chat_id)
            bot.send_message(chat_id, "You've subscribed to hourly updates.")

    elif call.data == "unsubscribe":
        if is_subscribed(chat_id):
            remove_subscriber(chat_id)
            bot.send_message(chat_id, "You've unsubscribed from hourly updates.")
        else:
            bot.send_message(chat_id, "You are not currently subscribed.")


def start_async_loop(chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(start_history_fetcher())
    loop.run_until_complete(start_event_listener())
    loop.close()


def fetch_and_send_stats(chat_id, include_distributor_info=False, is_total=False):
    if get_last_event() is None:
        last_tx_timestamp = (datetime.now() - timedelta(days=1)).timestamp()
    else:
        last_tx_timestamp = get_last_event().block_timestamp

    try:
        if is_total:
            if get_first_event() is None:
                first_tx_timestamp = (datetime.now() - timedelta(days=1)).timestamp()
            else:
                first_tx_timestamp = get_first_event().block_timestamp

            sums = get_total_sums()
        else:
            first_tx_timestamp = get_start_of_24hr_period_timestamp()
            sums = get_24hr_sums()

        send_stats(chat_id, *sums, include_distributor_info=include_distributor_info,
                   first_tx_timestamp=first_tx_timestamp, last_tx_timestamp=last_tx_timestamp,
                   is_total=is_total)

    except Exception as e:
        logger.error(f"Error in fetch_and_send_stats: {e}")
        bot.send_message(chat_id, "An error occurred while fetching the stats.")


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days} days, {hours} hours ago"
    else:
        return f"{hours} hours, {minutes} minutes ago"


def send_stats(chat_id,
               input_aix, aix_distributed, swapped_eth, distributed_eth,
               include_distributor_info=False,
               first_tx_timestamp=None, last_tx_timestamp=None,
               is_total=False):
    current_time = datetime.now()

    first_tx_time = "N/A" if first_tx_timestamp is None else format_timedelta(
        current_time - datetime.fromtimestamp(first_tx_timestamp))
    last_tx_time = "N/A" if last_tx_timestamp is None else format_timedelta(
        current_time - datetime.fromtimestamp(last_tx_timestamp))

    if is_total:
        message = "$AIX stats since inception:\n\n"
    else:
        message = "Daily $AIX stats:\n\n"

    message += (
        f" - AIX processed: {input_aix:.2f}\n"        
        f" - AIX distributed: {aix_distributed:.2f}\n"
        f" - ETH swapped: {swapped_eth:.2f}\n"
        f" - ETH distributed: {distributed_eth:.2f}\n\n"
        f"FirstTx: at {first_tx_time}\n"
        f"LastTx: at {last_tx_time}"
    )

    if include_distributor_info:
        distributor_balance = get_distributor_balance()
        message += (
            f"\n\nDistributor wallet: {DISTRIBUTOR_WALLET}\n"
            f"Distributor balance: {round(distributor_balance, 2)} ETH"
        )

    bot.send_message(chat_id, message)


def send_periodic_updates():
    subscribers_list = get_all_subscribers()

    for chat_id in subscribers_list:
        try:
            last_tx_timestamp = get_last_event().block_timestamp
            first_tx_timestamp = get_start_of_24hr_period_timestamp()

            sums = get_24hr_sums()
            logger.info(f"sums: {sums}")
            send_stats(chat_id, *sums, include_distributor_info=True,
                       first_tx_timestamp=first_tx_timestamp, last_tx_timestamp=last_tx_timestamp)

        except Exception as e:
            logger.error(f"Error sending update to {chat_id}: {e}")


@bot.message_handler(commands=['start'])
def start_command(message):
    global is_listening

    chat_id = message.chat.id

    if not is_listening:
        last_event_timestamp = get_last_event().block_timestamp

        if last_event_timestamp and last_event_timestamp != (datetime.now() - timedelta(days=1)).timestamp():
            bot.reply_to(message,
                         "Welcome to the AIX stats bot! History is up to date.",
                         reply_markup=make_welcome_keyboard())
        else:
            bot.reply_to(message,
                         "Welcome to the AIX stats bot! History is not up to date. Fetching history...",
                         reply_markup=make_welcome_keyboard())
            threading.Thread(target=lambda: start_async_loop(chat_id)).start()

        is_listening = True

    else:
        bot.send_message(chat_id,
                         "Welcome back! What do you need? Total statistics or all the info for today?",
                         reply_markup=make_menu_keyboard())


@bot.message_handler(commands=['total'])
def total_command(message):
    chat_id = message.chat.id
    fetch_and_send_stats(chat_id, include_distributor_info=False, is_total=True)


@bot.message_handler(commands=['today'])
def today_command(message):
    chat_id = message.chat.id
    fetch_and_send_stats(chat_id, include_distributor_info=True)


@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    chat_id = message.chat.id
    if is_subscribed(chat_id):
        logging.info(f'user with chat id: {chat_id} subscribed, nothing changed')
        bot.send_message(chat_id, "You're already subscribed to hourly updates.")
    else:
        add_subscriber(chat_id)
        logging.info(f'user with chat id: {chat_id} subscribed')
        bot.send_message(chat_id, "You've subscribed to hourly updates.")


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    chat_id = message.chat.id
    if is_subscribed(chat_id):
        remove_subscriber(chat_id)
        logging.info(f'user with chat id: {chat_id} unsubscribed')
        bot.send_message(chat_id, "You've unsubscribed from hourly updates.")
    else:
        logging.info(f'user with chat id: {chat_id} unsubscribed, nothing changed')
        bot.send_message(chat_id, "You are not currently subscribed.")


def initialize_event_processes():
    def start_fetcher():
        asyncio.run(start_history_fetcher())

    def start_listener():
        asyncio.run(start_event_listener())

    threading.Thread(target=start_fetcher).start()
    threading.Thread(target=start_listener).start()


if __name__ == '__main__':
    initialize_event_processes()
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_periodic_updates, 'interval', hours=1)
    scheduler.start()
    bot.infinity_polling()
