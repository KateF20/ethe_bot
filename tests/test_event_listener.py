import unittest
import asyncio
from unittest.mock import patch, MagicMock

from utils.utils import handle_event, logger
from events.event_listener import EventListener
from mock_db import fetch_data_from_database


class TestEventListener(unittest.TestCase):
    def test_listen_for_event(self):
        mock_event = {
            'blockNumber': 123456,
            'transactionHash': bytes.fromhex('abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'),
            'data': '0x' + '01' * 64 + '02' * 64 + '03' * 64 + '04' * 64
        }

        handle_event(mock_event)

        inserted_data = fetch_data_from_database(mock_event['blockNumber'])
        logger.info(inserted_data)

        assert inserted_data['blockNumber'] == mock_event['blockNumber']
        assert inserted_data['transactionHash'] == mock_event['transactionHash'].hex()

    async def test_main(self):
        mock_event_source = MagicMock()
        mock_event_source.get_event.return_value = asyncio.Future()
        mock_event_source.get_event.return_value.set_result('mock_event_data')

        with patch('event_listener.external_event_source', mock_event_source):
            await EventListener.listen_for_event('last_block')


if __name__ == '__main__':
    unittest.main()
