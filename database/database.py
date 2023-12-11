from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, BigInteger, String

from settings.settings import DB_USERNAME, DB_PASSWORD, DB_NAME, START_BLOCK_ID

Base = declarative_base()


class TotalDistributionEvent(Base):

    __tablename__ = 'total_distribution_events'

    id = Column(Integer, primary_key=True)
    transaction_hash = Column(String)
    block_timestamp = Column(BigInteger)
    input_aix_amount = Column(BigInteger)
    distributed_aix_amount = Column(BigInteger)
    swapped_eth_amount = Column(BigInteger)
    distributed_eth_amount = Column(BigInteger)
    block_number = Column(BigInteger)


engine = create_engine(f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def insert_event_into_database(block_number, transaction_hash, block_timestamp,
                               input_aix, distributed_aix, swapped_eth, distributed_eth):
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

        session = Session()
        session.add(new_event)
        session.flush()
        session.commit()
        session.flush()

        # logger.info("Event inserted into database")

    # except Exception as e:
    #     # logger.error(f"Error inserting event into database: {e}")
    finally:
        session.close()


def get_last_event_timestamp():
    session = Session()
    last_event = session.query(TotalDistributionEvent).order_by(TotalDistributionEvent.block_timestamp.desc()).first()
    session.close()

    return last_event.block_timestamp if last_event else (datetime.now() - timedelta(days=1)).timestamp()


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
