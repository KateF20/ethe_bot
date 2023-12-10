from database.database import Session, TotalDistributionEvent


def fetch_data_from_database(block_number):
    session = Session()
    event = session.query(TotalDistributionEvent).filter_by(block_number=block_number).first()
    session.close()

    if event:
        return {
            'blockNumber': event.block_number,
            'transactionHash': event.transaction_hash,
            'inputAixAmount': event.input_aix_amount,
            'distributedAixAmount': event.distributed_aix_amount,
            'swappedEthAmount': event.swapped_eth_amount,
            'distributedEthAmount': event.distributed_eth_amount
        }
    else:
        return None
