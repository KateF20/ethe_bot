from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, BigInteger, String

from settings.settings import DB_USERNAME, DB_PASSWORD, DB_NAME, START_BLOCK_ID

Base = declarative_base()


class TotalDistributionEvent(Base):

    __tablename__ = 'total_distribution_events'

    id = Column(Integer, primary_key=True)
    transaction_hash = Column(String)
    block_number = Column(BigInteger)
    input_aix_amount = Column(BigInteger)
    distributed_aix_amount = Column(BigInteger)
    swapped_eth_amount = Column(BigInteger)
    distributed_eth_amount = Column(BigInteger)


engine = create_engine(f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def insert_event_into_database(block_number, transaction_hash, input_aix_amount, distributed_aix_amount, swapped_eth_amount, distributed_eth_amount):
    new_event = TotalDistributionEvent(
        block_number=block_number,
        transaction_hash=transaction_hash,
        input_aix_amount=input_aix_amount,
        distributed_aix_amount=distributed_aix_amount,
        swapped_eth_amount=swapped_eth_amount,
        distributed_eth_amount=distributed_eth_amount
    )

    session = Session()
    session.add(new_event)
    session.commit()
    session.close()


def get_last_processed_block_from_database():
    session = Session()
    last_block = session.query(TotalDistributionEvent).order_by(TotalDistributionEvent.block_number.desc()).first()
    session.close()
    return last_block.block_number if last_block else START_BLOCK_ID
