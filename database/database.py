import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from sqlalchemy import create_engine

from settings.settings import DB_USERNAME, DB_PASSWORD, DB_NAME
from .models import TotalDistributionEvent, Base, Subscriber


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


engine = create_engine(f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@db:5432/{DB_NAME}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def insert_event_into_database(block_number, transaction_hash, block_timestamp,
                               input_aix, distributed_aix, swapped_eth, distributed_eth):
    logger.info(f"Inserting event into database: {transaction_hash}")

    session = Session()
    existing_event = session.query(TotalDistributionEvent).filter_by(block_number=block_number,
                                                                     transaction_hash=transaction_hash).first()
    if existing_event:
        session.close()
        return

    try:
        new_event = TotalDistributionEvent(
            block_number=block_number,
            transaction_hash=transaction_hash,
            block_timestamp=block_timestamp,
            input_aix_amount=input_aix,
            distributed_aix_amount=distributed_aix,
            swapped_eth_amount=swapped_eth,
            distributed_eth_amount=distributed_eth
        )

        session.add(new_event)
        session.commit()

    except Exception as e:
        logger.error(f"Error inserting event into database: {e}")
    finally:
        session.close()


def get_first_event():
    session = Session()
    first_event = session.query(TotalDistributionEvent).order_by(TotalDistributionEvent.block_timestamp.asc()).first()
    session.close()
    return first_event if first_event else None


def get_last_event():
    session = Session()
    last_event = session.query(TotalDistributionEvent).order_by(TotalDistributionEvent.block_timestamp.desc()).first()
    session.close()
    return last_event if last_event else None


def get_start_of_24hr_period_timestamp():
    session = Session()
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    first_event = session.query(TotalDistributionEvent).filter(
        TotalDistributionEvent.block_timestamp >= twenty_four_hours_ago.timestamp()
    ).order_by(TotalDistributionEvent.block_timestamp.asc()).first()
    session.close()

    return first_event.block_timestamp if first_event else None


def get_24hr_sums():
    session = Session()
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    sums = session.query(
        func.sum(TotalDistributionEvent.input_aix_amount),
        func.sum(TotalDistributionEvent.distributed_aix_amount),
        func.sum(TotalDistributionEvent.swapped_eth_amount),
        func.sum(TotalDistributionEvent.distributed_eth_amount)
    ).filter(
        TotalDistributionEvent.block_timestamp >= twenty_four_hours_ago.timestamp()
    ).one()

    session.close()
    return sums


def get_total_sums():
    session = Session()
    sums = session.query(
        func.sum(TotalDistributionEvent.input_aix_amount),
        func.sum(TotalDistributionEvent.distributed_aix_amount),
        func.sum(TotalDistributionEvent.swapped_eth_amount),
        func.sum(TotalDistributionEvent.distributed_eth_amount)
    ).one()
    session.close()
    return sums


def event_exists(transaction_hash):
    logger.info(f"Checking if event exists in database: {transaction_hash}")

    session = Session()
    exists = session.query(TotalDistributionEvent).filter_by(transaction_hash=transaction_hash).first() is not None
    logger.info(f"event exists: {exists}")
    session.close()
    return exists


def is_subscribed(chat_id):
    session = Session()
    exists = session.query(Subscriber).filter_by(chat_id=chat_id).first() is not None
    session.close()
    return exists


def add_subscriber(chat_id):
    session = Session()
    new_subscriber = Subscriber(chat_id=chat_id)
    session.add(new_subscriber)
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Error adding subscriber: {e}")
        session.rollback()
    finally:
        session.close()


def remove_subscriber(chat_id):
    session = Session()
    subscriber = session.query(Subscriber).filter_by(chat_id=chat_id).first()
    if subscriber:
        try:
            session.delete(subscriber)
            session.commit()
        except Exception as e:
            logger.error(f"Error removing subscriber: {e}")
            session.rollback()
    session.close()


def get_all_subscribers():
    session = Session()
    all_subscribers = session.query(Subscriber).all()
    subscriber_ids = [subscriber.chat_id for subscriber in all_subscribers]
    session.close()

    return subscriber_ids
