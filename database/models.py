from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String

Base = declarative_base()


class TotalDistributionEvent(Base):

    __tablename__ = 'total_distribution_events'

    id = Column(Integer, primary_key=True)
    block_number = Column(BigInteger)
    transaction_hash = Column(String)
    block_timestamp = Column(BigInteger)
    input_aix_amount = Column(BigInteger)
    distributed_aix_amount = Column(BigInteger)
    swapped_eth_amount = Column(BigInteger)
    distributed_eth_amount = Column(BigInteger)


class Subscriber(Base):

    __tablename__ = 'subscribers'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
