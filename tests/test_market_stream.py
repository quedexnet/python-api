from unittest import TestCase
import json

import market_stream_fixtures
from quedex_api import MarketStream, MarketStreamListener, Exchange


class TestMarketStream(TestCase):

  def setUp(self):
    exchange = Exchange(market_stream_fixtures.public_key_str, 'apiurl')
    self.listener = TestListener()
    self.market_stream = MarketStream(exchange)
    self.market_stream.add_listener(self.listener)

  def test_receiving_order_book(self):
    self.market_stream.on_message(market_stream_fixtures.order_book_str)

    self.assertEqual(self.listener.error, None)
    expected_order_book = {
      'type': u'order_book',
      'instrument_id': u'71',
      'bids': [[u'0.00041667', 10]],
      'asks': [[u'0.00042016', 10]]
    }
    self.assertEqual(self.listener.order_book, expected_order_book)
    self.assertEqual(self.listener.message, expected_order_book)

  def test_receiving_quotes(self):
    self.market_stream.on_message(market_stream_fixtures.quotes_str)

    self.assertEqual(self.listener.error, None)
    expected_quotes = {
      u'ask': u'0.00001868',
      u'ask_quantity': 1000,
      u'bid': u'0.00001503',
      u'bid_quantity': 1000,
      u'instrument_id': u'5095',
      u'last': u'0.00009091',
      u'last_quantity': 0,
      u'open_interest': 0,
      u'tap': None,
      u'lower_limit': None,
      u'upper_limit': None,
      u'type': u'quotes',
      u'volume': 0
    }
    self.assertEqual(self.listener.quotes, expected_quotes)
    self.assertEqual(self.listener.message, expected_quotes)

  def test_receiving_instrument_data(self):
    self.market_stream.on_message(market_stream_fixtures.instrument_data_str)

    self.assertEqual(self.listener.error, None)
    expected_instrument = {
      u'expiration_date': 1499990400000,
      u'fee': u'0.00025000',
      u'first_notice_date': 1499990400000,
      u'initial_margin': u'0.05000000',
      u'instrument_id': u'24',
      u'inverse_symbol': u'F.BTCUSD.JUL17W2',
      u'issue_date': 1498780800000,
      u'maintenance_margin': u'0.04000000',
      u'notional_amount': 1,
      u'settlement_method': u'financial',
      u'symbol': u'F.USD.JUL17W2',
      u'taker_to_maker': u'0.00075000',
      u'tick_size': u'0.00000001',
      u'type': u'futures',
      u'underlying_symbol': u'USD'
    }
    self.assertEqual(self.listener.instrument_data['data']['24'], expected_instrument)
    self.assertEqual(self.listener.message['data']['24'], expected_instrument)

  def test_receiving_trade(self):
    self.market_stream.on_message(market_stream_fixtures.trade_str)

    self.assertEqual(self.listener.error, None)
    expected_trade = {
      u'instrument_id': u'24',
      u'liquidity_provider': u'buyer',
      u'price': u'0.00041667',
      u'quantity': 1,
      u'timestamp': 1499867675414,
      u'trade_id': u'138',
      u'type': u'trade'
    }
    self.assertEqual(self.listener.trade, expected_trade)
    self.assertEqual(self.listener.message, expected_trade)

  def test_receiving_session_state(self):
    self.market_stream.on_message(market_stream_fixtures.session_state_str)

    self.assertEqual(self.listener.error, None)
    expected_session_state = { u'state': u'continuous', u'type': u'session_state' }
    self.assertEqual(self.listener.session_state, expected_session_state)
    self.assertEqual(self.listener.message, expected_session_state)

  def test_receives_error_on_data_parsing_error(self):
    self.market_stream.on_message(market_stream_fixtures.corrupt_data_str)

    # cannot test message equality because python 2 and 3 give different message
    self.assertNotEqual(self.listener.error, None)

  def test_receives_error_from_outside(self):
    self.market_stream.on_error(Exception('bomba'))

    self.assertEqual(str(self.listener.error), 'bomba')

  def test_maintenance_error_code_is_ignored(self):
    self.market_stream.on_message(market_stream_fixtures.error_maintenance_data_str)

    self.assertEqual(self.listener.error, None)

  def test_receives_error_on_non_maintenance_error_code(self):
    self.market_stream.on_message(market_stream_fixtures.error_data_str)

    self.assertEqual(str(self.listener.error), 'WebSocket error: ERROR')

  def test_does_not_call_removed_listener(self):
    self.market_stream.remove_listener(self.listener)

    self.market_stream.on_message(market_stream_fixtures.order_book_str)

    self.assertEqual(self.listener.order_book, None)

  def test_keepalive_is_ignored(self):
    self.market_stream.on_message(json.dumps({'type': 'keepalive', 'timestamp': 1506958410894}))

    self.assertEqual(self.listener.message, None)
    self.assertEqual(self.listener.error, None)

  def test_unknown_is_ignored(self):
    self.market_stream.on_message(json.dumps({'type': 'unknown'}))

    self.assertEqual(self.listener.message, None)
    self.assertEqual(self.listener.error, None)

  def test_calls_multiple_added_listeners(self):
    listener2 = TestListener()
    self.market_stream.add_listener(listener2)

    self.market_stream.on_message(market_stream_fixtures.order_book_str)

    self.assertNotEquals(self.listener.order_book, None)
    self.assertNotEquals(listener2.order_book, None)

  def test_listener_without_all_methods_implemented(self):
    # listener that does not inherit from MarketStreamListener
    class Listener(object):
      def __init__(self):
        self.order_book = None
      def on_order_book(self, order_book):
        self.order_book = order_book

    listener = Listener()
    self.market_stream.add_listener(listener)

    self.market_stream.on_message(market_stream_fixtures.order_book_str)
    # does not crash when receiving something it does not have a listener method for
    self.market_stream.on_message(market_stream_fixtures.trade_str)

    self.assertNotEquals(listener.order_book, None)

  def test_disconnect(self):
    self.market_stream.on_disconnect('maintenance')

    self.assertEqual(self.listener.disconnect_message, 'maintenance')

  def test_ready(self):
    self.market_stream.on_ready()

    self.assertTrue(self.listener.ready)


class TestListener(MarketStreamListener):
  def __init__(self):
    self.message = None
    self.instrument_data = None
    self.order_book = None
    self.quotes = None
    self.trade = None
    self.session_state = None
    self.error = None
    self.disconnect_message = None
    self.ready = False

  def on_message(self, message):
    self.message = message

  def on_instrument_data(self, instrument_data):
    self.instrument_data = instrument_data

  def on_order_book(self, order_book):
    self.order_book = order_book

  def on_quotes(self, quotes):
    self.quotes = quotes

  def on_trade(self, trade):
    self.trade = trade

  def on_session_state(self, session_state):
    self.session_state = session_state

  def on_error(self, error):
    self.error = error

  def on_disconnect(self, message):
    self.disconnect_message = message

  def on_ready(self):
    self.ready = True
