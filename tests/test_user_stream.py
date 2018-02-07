from unittest import TestCase
import json

import pgpy

from quedex_api import UserStream, UserStreamListener, Trader, Exchange


class TestUserStream(TestCase):
  def setUp(self):
    self.quedex_private_key = pgpy.PGPKey()
    self.quedex_private_key.parse(open('keys/quedex-private-key.asc', 'r').read())
    self.trader_public_key = pgpy.PGPKey()
    self.trader_public_key.parse(open('keys/trader-public-key.asc', 'r').read())

    trader = Trader('123456789', open('keys/trader-private-key.asc', 'r').read())
    trader.decrypt_private_key('aaa')
    exchange = Exchange(open('keys/quedex-public-key.asc', 'r').read(), 'wss://url')
    self.listener = TestListener()
    self.user_stream = UserStream(exchange, trader)
    self.user_stream.add_listener(self.listener)

    self.sent_message = None
    def set_sent_message(message):
      self.sent_message = message
    self.user_stream.send_message = set_sent_message

  def test_initialization(self):
    self.user_stream.initialize()
    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'get_last_nonce',
      'account_id': '123456789',
      'nonce_group': 5,
    })

    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'last_nonce',
      'last_nonce': 5,
      'nonce_group': 5,
    }]))
    self.assertFalse(self.user_stream._initialized)
    self.assertEqual(self.user_stream._nonce, 6)
    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'subscribe',
      'account_id': '123456789',
      'nonce': 6,
      'nonce_group': 5,
    })

    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'subscribed',
      'nonce': 5,
      'message_nonce_group': 5,
    }]))
    self.assertTrue(self.user_stream._initialized)
    self.assertTrue(self.listener.ready)
    self.assertEqual(self.listener.error, None)

  def test_receiving_account_state(self):
    account_state = {'type': 'account_state', 'balance': '3.1416'}
    self.user_stream.on_message(self.serialize_to_trader([account_state]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.account_state, account_state)
    self.assertEqual(self.listener.message, account_state)

  def test_receiving_open_position(self):
    open_position = {'type': 'open_position', 'initial_margin': '2.5'}
    self.user_stream.on_message(self.serialize_to_trader([open_position]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.open_position, open_position)
    self.assertEqual(self.listener.message, open_position)

  def test_receiving_order_placed(self):
    order_placed = {'type': 'order_placed', 'side': 'buy'}
    self.user_stream.on_message(self.serialize_to_trader([order_placed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_placed, order_placed)
    self.assertEqual(self.listener.message, order_placed)

  def test_receiving_order_place_failed(self):
    order_place_failed = {'type': 'order_place_failed', 'side': 'buy'}
    self.user_stream.on_message(self.serialize_to_trader([order_place_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_place_failed, order_place_failed)
    self.assertEqual(self.listener.message, order_place_failed)

  def test_receiving_order_cancelled(self):
    order_cancelled = {'type': 'order_cancelled', 'client_order_id': '123'}
    self.user_stream.on_message(self.serialize_to_trader([order_cancelled]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_cancelled, order_cancelled)
    self.assertEqual(self.listener.message, order_cancelled)

  def test_receiving_order_forcefully_cancelled(self):
    order_forcefully_cancelled = {
      'type': 'order_forcefully_cancelled',
      'client_order_id': '123',
      'cause': 'settlement'
    }
    self.user_stream.on_message(self.serialize_to_trader([order_forcefully_cancelled]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_forcefully_cancelled, order_forcefully_cancelled)
    self.assertEqual(self.listener.message, order_forcefully_cancelled)

  def test_receiving_order_cancel_failed(self):
    order_cancel_failed = {'type': 'order_cancel_failed', 'cause': 'insufficient_funds'}
    self.user_stream.on_message(self.serialize_to_trader([order_cancel_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_cancel_failed, order_cancel_failed)
    self.assertEqual(self.listener.message, order_cancel_failed)

  def test_receiving_order_modified(self):
    order_modified = {'type': 'order_modified', 'new_limit_price': '1.2'}
    self.user_stream.on_message(self.serialize_to_trader([order_modified]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_modified, order_modified)
    self.assertEqual(self.listener.message, order_modified)

  def test_receiving_order_modification_failed(self):
    order_modification_failed = {'type': 'order_modification_failed', 'cause': 'margin_call'}
    self.user_stream.on_message(self.serialize_to_trader([order_modification_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_modification_failed, order_modification_failed)
    self.assertEqual(self.listener.message, order_modification_failed)

  def test_receiving_order_filled(self):
    order_filled = {'type': 'order_filled', 'leaves_quantity': 4}
    self.user_stream.on_message(self.serialize_to_trader([order_filled]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.order_filled, order_filled)
    self.assertEqual(self.listener.message, order_filled)

  def test_receives_batch(self):
    filled1 = {'type': 'order_filled', 'leaves_quantity': 4}
    filled2 = {'type': 'order_filled', 'leaves_quantity': 5}
    self.user_stream.on_message(json.dumps({
      'type': 'data',
      'data': sign_encrypt([filled1, filled2], self.quedex_private_key, self.trader_public_key),
    }))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.messages[0], filled1)
    self.assertEqual(self.listener.messages[1], filled2)

  def test_receives_error_on_data_parsing_error(self):
    self.user_stream.on_message('not json')

    self.assertEqual(self.listener.error.message, 'No JSON object could be decoded')

  def test_receives_error_from_outside(self):
    self.user_stream.on_error(Exception('extern4l 3rror'))

    self.assertEqual(self.listener.error.message, 'extern4l 3rror')

  def test_maintenance_error_code_is_ignored(self):
    self.user_stream.on_message(json.dumps({'type': 'error', 'error_code': 'maintenance'}))

    self.assertEqual(self.listener.error, None)

  def test_receives_error_on_non_maintenance_error_code(self):
    self.user_stream.on_message(json.dumps({'type': 'error', 'error_code': 'ERRORR'}))

    self.assertEqual(self.listener.error.message, 'WebSocket error: ERRORR')

  def test_does_not_call_removed_listener(self):
    self.user_stream.remove_listener(self.listener)

    self.user_stream.on_message(self.serialize_to_trader([{'type': 'order_filled', 'leaves_quantity': 4}]))

    self.assertEqual(self.listener.order_filled, None)

  def test_keepalive_is_ignored(self):
    self.user_stream.on_message(json.dumps({'type': 'keepalive', 'timestamp': 1506958410894}))

    self.assertEqual(self.listener.message, None)
    self.assertEqual(self.listener.error, None)

  def test_unknown_is_ignored(self):
    self.user_stream.on_message(json.dumps({'type': 'unknown'}))

    self.assertEqual(self.listener.message, None)
    self.assertEqual(self.listener.error, None)

  def test_calls_multiple_added_listeners(self):
    listener2 = TestListener()
    self.user_stream.add_listener(listener2)

    order_filled = {'type': 'order_filled', 'leaves_quantity': 4}
    self.user_stream.on_message(self.serialize_to_trader([order_filled]))

    self.assertEquals(self.listener.order_filled, order_filled)
    self.assertEquals(listener2.order_filled, order_filled)

  def test_listener_without_all_methods_implemented(self):
    # listener that does not inherit from MarketStreamListener
    class Listener(object):
      def __init__(self):
        self.order_filled = None
      def on_order_filled(self, order_filled):
        self.order_filled = order_filled

    listener = Listener()
    self.user_stream.add_listener(listener)

    self.user_stream.on_message(self.serialize_to_trader([{'type': 'order_filled', 'leaves_quantity': 4}]))
    # does not crash when receiving something it does not have a listener method for
    self.user_stream.on_message(self.serialize_to_trader([{'type': 'order_placed', 'side': 'buy'}]))

    self.assertNotEquals(listener.order_filled, None)

  def test_disconnect(self):
    self.user_stream.on_disconnect('maintenance')

    self.assertEqual(self.listener.disconnect_message, 'maintenance')

  def test_placing_order(self):
    self.initialize()

    self.user_stream.place_order({
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
    })

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'place_order',
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
    })

  def test_cancelling_order(self):
    self.initialize()

    self.user_stream.cancel_order({'client_order_id': 15})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'cancel_order',
      'account_id': '123456789',
      'client_order_id': 15,
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_modifying_order(self):
    self.initialize()

    self.user_stream.modify_order({'client_order_id': 15, 'new_limit_price': '0.0001'})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'modify_order',
      'account_id': '123456789',
      'client_order_id': 15,
      'new_limit_price': '0.0001',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_batch(self):
    self.initialize()

    self.user_stream.batch([
      {
        'type': 'modify_order',
        'new_limit_price': '9.87',
        'client_order_id': 23,
      },
      {
        'type': 'cancel_order',
        'client_order_id': 22,
      }
    ])

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'batch',
      'account_id': '123456789',
      'batch': [
        {
          'type': 'modify_order',
          'new_limit_price': '9.87',
          'client_order_id': 23,
          'account_id': '123456789',
          'nonce': 7,
          'nonce_group': 5,
        },
        {
          'type': 'cancel_order',
          'account_id': '123456789',
          'client_order_id': 22,
          'nonce': 8,
          'nonce_group': 5,
        }
      ]
    })

  def test_start_send_batch(self):
    self.initialize()

    self.user_stream.start_batch()
    self.user_stream.modify_order({'new_limit_price': '9.87', 'client_order_id': 23,})
    self.user_stream.cancel_order({'client_order_id': 22})
    self.user_stream.send_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'batch',
      'account_id': '123456789',
      'batch': [
        {
          'type': 'modify_order',
          'new_limit_price': '9.87',
          'client_order_id': 23,
          'account_id': '123456789',
          'nonce': 7,
          'nonce_group': 5,
        },
        {
          'type': 'cancel_order',
          'account_id': '123456789',
          'client_order_id': 22,
          'nonce': 8,
          'nonce_group': 5,
        }
      ]
    })

  def test_receives_welcome_pack_with_with_account_state(self):
    self.user_stream.initialize()
    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'last_nonce',
      'last_nonce': 5,
      'nonce_group': 5,
    }]))
    account_state = {'type': 'account_state', 'balance': '3.1416'}
    self.user_stream.on_message(self.serialize_to_trader([
      {
        'type': 'subscribed',
        'nonce': 5,
        'message_nonce_group': 5,
      },
      account_state
    ]))

    self.assertTrue(self.listener.ready)
    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.account_state, account_state)
    self.assertEqual(self.listener.message, account_state)

  def test_does_not_process_last_nonce_for_foreign_nonce_group(self):
    self.user_stream.initialize()
    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'last_nonce',
      'last_nonce': 5,
      'nonce_group': 6,
    }]))
    self.assertEqual(self.user_stream._nonce, None)

  def test_is_not_initialized_after_receiving_subscribed_for_foreign_nonce_grup(self):
    self.user_stream.initialize()
    self.user_stream.on_message(self.serialize_to_trader([{
        'type': 'subscribed',
        'nonce': 5,
        'nonce_group': 6,
    }]))
    self.assertFalse(self.user_stream._initialized)
    self.assertFalse(self.listener.ready)

  def serialize_to_trader(self, entity):
    return json.dumps({
      'type': 'data',
      'data': sign_encrypt(entity, self.quedex_private_key, self.trader_public_key),
    })

  def decrypt_from_trader(self, message):
    return decrypt_verify(message, self.quedex_private_key, self.trader_public_key)

  def initialize(self):
    self.user_stream.initialize()
    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'last_nonce',
      'last_nonce': 5,
      'nonce_group': 5,
    }]))
    self.user_stream.on_message(self.serialize_to_trader([{
      'type': 'subscribed',
      'nonce': 5,
      'message_nonce_group': 5,
    }]))


class TestListener(UserStreamListener):
  def __init__(self):
    self.order_place_failed = None
    self.order_cancel_failed = None
    self.account_state = None
    self.order_modified = None
    self.messages = []
    self.order_modification_failed = None
    self.open_position = None
    self.error = None
    self.disconnect_message = None
    self.order_placed = None
    self.order_cancelled = None
    self.order_forcefully_cancelled = None
    self.order_filled = None
    self.ready = False

  @property
  def message(self):
    return self.messages[0] if self.messages else None

  def on_ready(self):
    self.ready = True

  def on_order_place_failed(self, order_place_failed):
    self.order_place_failed = order_place_failed

  def on_order_cancel_failed(self, order_cancel_failed):
    self.order_cancel_failed = order_cancel_failed

  def on_account_state(self, account_state):
    self.account_state = account_state

  def on_order_modified(self, order_modified):
    self.order_modified = order_modified

  def on_message(self, message):
    self.messages.append(message)

  def on_order_modification_failed(self, order_modification_failed):
    self.order_modification_failed = order_modification_failed

  def on_open_position(self, open_position):
    self.open_position = open_position

  def on_error(self, error):
    self.error = error

  def on_disconnect(self, message):
    self.disconnect_message = message

  def on_order_placed(self, order_placed):
    self.order_placed = order_placed

  def on_order_cancelled(self, order_cancelled):
    self.order_cancelled = order_cancelled

  def on_order_forcefully_cancelled(self, order_forcefully_cancelled):
    self.order_forcefully_cancelled = order_forcefully_cancelled

  def on_order_filled(self, order_filled):
    self.order_filled = order_filled


def sign_encrypt(entity, private_key, public_key):
  message = pgpy.PGPMessage.new(json.dumps(entity))
  message |= private_key.sign(message)
  return str(public_key.encrypt(message))


def decrypt_verify(message, private_key, public_key):
  decrypted = private_key.decrypt(pgpy.PGPMessage.from_blob(message))
  if not public_key.verify(decrypted):
    raise AssertionError('Verification failed for message: ' + decrypted)
  return json.loads(decrypted.message)
