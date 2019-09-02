from unittest import TestCase
import json

import pgpy

from quedex_api import UserStream, UserStreamListener, Trader, Exchange


class TestUserStream(TestCase):
  # maxDiff = None

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

  def test_receiving_open_position_forcefully_closed(self):
    open_position_forcefully_closed = {
      'type': 'open_position_forcefully_closed',
      'instrument_id': 100,
      'side': 'long',
      'closed_quantity': 5,
      'remaining_quantity': 95,
      'close_price': '0.00011000',
      'cause': 'deleveraging'

    }
    self.user_stream.on_message(self.serialize_to_trader([open_position_forcefully_closed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.open_position_forcefully_closed, open_position_forcefully_closed)
    self.assertEqual(self.listener.message, open_position_forcefully_closed)

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

  def test_receiving_all_orders_cancelled(self):
    all_orders_cancelled = {'type': 'all_orders_cancelled'}
    self.user_stream.on_message(self.serialize_to_trader([all_orders_cancelled]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.all_orders_cancelled, all_orders_cancelled)
    self.assertEqual(self.listener.message, all_orders_cancelled)

  def test_receiving_cancel_all_orders_failed(self):
    cancel_all_orders_failed = {
      'type': 'cancel_all_orders_failed',
      'cause': 'session_not_active'
    }
    self.user_stream.on_message(self.serialize_to_trader([cancel_all_orders_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.cancel_all_orders_failed, cancel_all_orders_failed)
    self.assertEqual(self.listener.message, cancel_all_orders_failed)

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

  def test_receiving_timer_added(self):
    timer_added = {'type': 'timer_added', 'timer_id': 1}
    self.user_stream.on_message(self.serialize_to_trader([timer_added]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_added, timer_added)
    self.assertEqual(self.listener.message, timer_added)

  def test_receiving_timer_rejected(self):
    timer_rejected = {'type': 'timer_rejected', 'timer_id': 1, 'cause': 'too_many_active_timers'}
    self.user_stream.on_message(self.serialize_to_trader([timer_rejected]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_rejected, timer_rejected)
    self.assertEqual(self.listener.message, timer_rejected)

  def test_receiving_timer_expired(self):
    timer_expired = {'type': 'timer_expired', 'timer_id': 1}
    self.user_stream.on_message(self.serialize_to_trader([timer_expired]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_expired, timer_expired)
    self.assertEqual(self.listener.message, timer_expired)

  def test_receiving_timer_triggered(self):
    timer_triggered = {'type': 'timer_triggered', 'timer_id': 1}
    self.user_stream.on_message(self.serialize_to_trader([timer_triggered]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_triggered, timer_triggered)
    self.assertEqual(self.listener.message, timer_triggered)

  def test_receiving_timer_updated(self):
    timer_updated = {'type': 'timer_updated', 'timer_id': 1}
    self.user_stream.on_message(self.serialize_to_trader([timer_updated]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_updated, timer_updated)
    self.assertEqual(self.listener.message, timer_updated)

  def test_receiving_timer_update_failed(self):
    timer_update_failed = {'type': 'timer_update_failed', 'timer_id': 1, 'cause': 'not_found'}
    self.user_stream.on_message(self.serialize_to_trader([timer_update_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_failed, timer_update_failed)
    self.assertEqual(self.listener.message, timer_update_failed)

  def test_receiving_timer_cancelled(self):
    timer_cancelled = {'type': 'timer_cancelled', 'timer_id': 1}
    self.user_stream.on_message(self.serialize_to_trader([timer_cancelled]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_cancelled, timer_cancelled)
    self.assertEqual(self.listener.message, timer_cancelled)

  def test_receiving_timer_cancel_failed(self):
    timer_cancel_failed = {'type': 'timer_cancel_failed', 'timer_id': 1, 'cause': 'not_found'}
    self.user_stream.on_message(self.serialize_to_trader([timer_cancel_failed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.timer_failed, timer_cancel_failed)
    self.assertEqual(self.listener.message, timer_cancel_failed)

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

  def test_receiving_internal_transfer_received(self):
    internal_transfer_received = {
      'type': 'internal_transfer_received',
      'source_account_id': 1,
      'amount': '1.2',
    }
    self.user_stream.on_message(self.serialize_to_trader([internal_transfer_received]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.internal_transfer_received, internal_transfer_received)
    self.assertEqual(self.listener.message, internal_transfer_received)

  def test_internal_transfer_executed(self):
    internal_transfer_executed = {
      'type': 'internal_transfer_executed',
      'destination_account_id': 1,
      'amount': '1.2',
    }
    self.user_stream.on_message(self.serialize_to_trader([internal_transfer_executed]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.internal_transfer_executed, internal_transfer_executed)
    self.assertEqual(self.listener.message, internal_transfer_executed)

  def test_internal_transfer_rejected(self):
    internal_transfer_rejected = {
      'type': 'internal_transfer_rejected',
      'destination_account_id': 1,
      'amount': '1.2',
      'cause': 'forbidden',
    }
    self.user_stream.on_message(self.serialize_to_trader([internal_transfer_rejected]))

    self.assertEqual(self.listener.error, None)
    self.assertEqual(self.listener.internal_transfer_rejected, internal_transfer_rejected)
    self.assertEqual(self.listener.message, internal_transfer_rejected)

  def test_receives_error_on_data_parsing_error(self):
    self.user_stream.on_message('not json')

    # cannot test message equality because python 2 and 3 give different message
    self.assertNotEqual(self.listener.error, None)

  def test_receives_error_from_outside(self):
    self.user_stream.on_error(Exception('extern4l 3rror'))

    self.assertEqual(str(self.listener.error), 'extern4l 3rror')

  def test_maintenance_error_code_is_ignored(self):
    self.user_stream.on_message(json.dumps({'type': 'error', 'error_code': 'maintenance'}))

    self.assertEqual(self.listener.error, None)

  def test_receives_error_on_non_maintenance_error_code(self):
    self.user_stream.on_message(json.dumps({'type': 'error', 'error_code': 'ERRORR'}))

    self.assertEqual(str(self.listener.error), 'WebSocket error: ERRORR')

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

  def test_placing_order_with_post_only(self):
    self.initialize()

    self.user_stream.place_order({
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
      'post_only': True,
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
      'post_only': True,
    })

  def test_placing_order_with_invalid_post_only(self):
    self.initialize()

    exception_caught = False

    try:
      self.user_stream.place_order({
        'price': '9.87',
        'client_order_id': 15,
        'instrument_id': '76',
        'quantity': 6,
        'side': 'buy',
        'order_type': 'limit',
        'limit_price': '4.5',
        'post_only': 0,
      })
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

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

  def test_cancelling_all_orders(self):
    self.initialize()

    self.user_stream.cancel_all_orders()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'cancel_all_orders',
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_modifying_order_with_new_price(self):
    self.initialize()

    self.user_stream.modify_order({'client_order_id': 15, 'new_price': '0.0001'})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'modify_order',
      'account_id': '123456789',
      'client_order_id': 15,
      'new_price': '0.0001',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_modifying_order_with_new_quantity(self):
    self.initialize()

    self.user_stream.modify_order({'client_order_id': 15, 'new_quantity': 1000})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'modify_order',
      'account_id': '123456789',
      'client_order_id': 15,
      'new_quantity': 1000,
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_modifying_order_with_new_quantity_and_new_price(self):
    self.initialize()

    self.user_stream.modify_order({'client_order_id': 15, 'new_price': '0.0001', 'new_quantity': 1000})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'modify_order',
      'account_id': '123456789',
      'client_order_id': 15,
      'new_quantity': 1000,
      'new_price': '0.0001',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_modifying_order_with_post_only(self):
    self.initialize()

    self.user_stream.modify_order({'client_order_id': 789, 'new_price': '1001.1', 'post_only': True})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'modify_order',
      'account_id': '123456789',
      'client_order_id': 789,
      'new_price': '1001.1',
      'post_only': True,
      'nonce': 7,
      'nonce_group': 5
    })

  def test_modifying_orders_without_order_id(self):
    self.initialize()

    exception_caught = False
    try:
      self.user_stream.modify_order({'new_price': '1001.1'})
    except:
      exception_caught = True

    self.assertTrue(exception_caught)


  def test_modifying_orders_without_new_quantity_nor_new_price(self):
    self.initialize()

    exception_caught = False
    try:
      self.user_stream.modify_order({'client_order_id': 789})
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_modifying_orders_with_invalid_post_only(self):
    self.initialize()

    exception_caught = False

    try:
      self.user_stream.modify_order({'client_order_id': 789, 'new_price': '1001.1', 'post_only': 0})
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_batch(self):
    self.initialize()

    self.user_stream.batch([
      {
        'type': 'cancel_all_orders',
      },
      {
        'type': 'modify_order',
        'new_price': '9.87',
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
          'type': 'cancel_all_orders',
          'account_id': '123456789',
          'nonce': 7,
          'nonce_group': 5,
        },
        {
          'type': 'modify_order',
          'new_price': '9.87',
          'client_order_id': 23,
          'account_id': '123456789',
          'nonce': 8,
          'nonce_group': 5,
        },
        {
          'type': 'cancel_order',
          'account_id': '123456789',
          'client_order_id': 22,
          'nonce': 9,
          'nonce_group': 5,
        }
      ]
    })

  def test_empty_batch(self):
    self.initialize()

    exception_caught = False

    try:
      self.user_stream.batch([])
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_start_send_batch(self):
    self.initialize()

    self.user_stream.start_batch()
    self.user_stream.cancel_all_orders()
    self.user_stream.modify_order({'new_price': '9.87', 'client_order_id': 23,})
    self.user_stream.cancel_order({'client_order_id': 22})
    self.user_stream.send_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'batch',
      'account_id': '123456789',
      'batch': [
        {
          'type': 'cancel_all_orders',
          'account_id': '123456789',
          'nonce': 7,
          'nonce_group': 5,
        },
        {
          'type': 'modify_order',
          'new_price': '9.87',
          'client_order_id': 23,
          'account_id': '123456789',
          'nonce': 8,
          'nonce_group': 5,
        },
        {
          'type': 'cancel_order',
          'account_id': '123456789',
          'client_order_id': 22,
          'nonce': 9,
          'nonce_group': 5,
        }
      ]
    })

  def test_start_send_empty_batch(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_batch()
    try:
      self.user_stream.send_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_batch_when_start_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.start_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_batch_when_start_update_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.start_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_time_triggered_batch_when_start_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_batch()
    try:
      self.user_stream.start_time_triggered_batch(1, 100, 200)
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_time_triggered_batch_when_start_update_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.start_time_triggered_batch(1, 100, 200)
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_update_time_triggered_batch_when_start_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_batch()
    try:
      self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_start_update_time_triggered_batch_when_start_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_send_batch_when_start_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.send_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_send_batch_when_start_update_time_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.send_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_send_triggered_batch_when_start_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_batch()
    try:
      self.user_stream.send_time_triggered_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_send_triggered_batch_when_start_update_timer_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.send_time_triggered_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)


  def test_cannot_send_update_triggered_batch_when_start_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_batch()
    try:
      self.user_stream.send_update_time_triggered_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_cannot_send_update_triggered_batch_when_start_timer_triggered_batch_has_been_called(self):
    self.initialize()

    exception_caught = False

    self.user_stream.start_time_triggered_batch(1, 100, 200)
    try:
      self.user_stream.send_update_time_triggered_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_start_send_time_triggered_batch(self):
    self.initialize()

    self.user_stream.start_time_triggered_batch(1, 100, 200)
    self.user_stream.cancel_all_orders()
    self.user_stream.place_order({
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
      'post_only': True,
    })
    self.user_stream.send_time_triggered_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'add_timer',
      'timer_id': 1,
      'execution_start_timestamp': 100,
      'execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_time_triggered_batch(self):
    self.initialize()

    self.user_stream.time_triggered_batch(
      1,
      100,
      200,
      [{
        'type': 'cancel_all_orders',
      }, {
        'type': 'place_order',
        'price': '9.87',
        'client_order_id': 15,
        'instrument_id': '76',
        'quantity': 6,
        'side': 'buy',
        'order_type': 'limit',
        'limit_price': '4.5',
        'post_only': True,
      }],
    )

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'add_timer',
      'timer_id': 1,
      'execution_start_timestamp': 100,
      'execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_start_send_update_time_triggered_batch(self):
    self.initialize()

    self.user_stream.start_update_time_triggered_batch(1, 100, 200)
    self.user_stream.cancel_all_orders()
    self.user_stream.place_order({
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
      'post_only': True,
    })
    self.user_stream.send_update_time_triggered_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': 100,
      'new_execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'new_command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_update_time_triggered_batch(self):
    self.initialize()

    self.user_stream.update_time_triggered_batch(
      1,
      100,
      200,
      [{
        'type': 'cancel_all_orders',
      }, {
        'type': 'place_order',
        'price': '9.87',
        'client_order_id': 15,
        'instrument_id': '76',
        'quantity': 6,
        'side': 'buy',
        'order_type': 'limit',
        'limit_price': '4.5',
        'post_only': True,
      }],
    )

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': 100,
      'new_execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'new_command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_update_time_triggered_batch_when_no_changes(self):
    self.initialize()

    exception_caught = False

    try:
      self.user_stream.update_time_triggered_batch(
        1,
        None,
        None,
        None,
      )
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_update_time_triggered_batch_when_only_start_timestamp_is_modified(self):
    self.initialize()

    self.user_stream.update_time_triggered_batch(
      1,
      100,
      None,
      None,
    )

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': 100,
      'new_execution_expiration_timestamp': None,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_update_time_triggered_batch_when_only_expiration_time_is_modified(self):
    self.initialize()

    self.user_stream.update_time_triggered_batch(
      1,
      None,
      200,
      None,
    )

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': None,
      'new_execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_update_time_triggered_batch_when_only_commands_are_modified(self):
    self.initialize()

    self.user_stream.update_time_triggered_batch(
      1,
      None,
      None,
      [{
        'type': 'cancel_all_orders',
      }, {
        'type': 'place_order',
        'price': '9.87',
        'client_order_id': 15,
        'instrument_id': '76',
        'quantity': 6,
        'side': 'buy',
        'order_type': 'limit',
        'limit_price': '4.5',
        'post_only': True,
      }],
    )

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': None,
      'new_execution_expiration_timestamp': None,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'new_command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_start_send_update_time_triggered_batch_when_no_changes(self):
    self.initialize()

    exception_caught = False

    try:
      self.user_stream.start_update_time_triggered_batch(1, None, None)
      self.user_stream.send_update_time_triggered_batch()
    except:
      exception_caught = True

    self.assertTrue(exception_caught)

  def test_start_send_update_time_triggered_batch_when_only_start_timestamp_is_modified(self):
    self.initialize()

    self.user_stream.start_update_time_triggered_batch(1, 100, None)
    self.user_stream.send_update_time_triggered_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': 100,
      'new_execution_expiration_timestamp': None,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_start_send_update_time_triggered_batch_when_only_expiration_timestamp_is_modified(self):
    self.initialize()

    self.user_stream.start_update_time_triggered_batch(1, None, 200)
    self.user_stream.send_update_time_triggered_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': None,
      'new_execution_expiration_timestamp': 200,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_start_send_update_time_triggered_batch_when_only_commands_are_modified(self):
    self.initialize()

    self.user_stream.start_update_time_triggered_batch(1, None, None)
    self.user_stream.cancel_all_orders()
    self.user_stream.place_order({
      'price': '9.87',
      'client_order_id': 15,
      'instrument_id': '76',
      'quantity': 6,
      'side': 'buy',
      'order_type': 'limit',
      'limit_price': '4.5',
      'post_only': True,
    })
    self.user_stream.send_update_time_triggered_batch()

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'update_timer',
      'timer_id': 1,
      'new_execution_start_timestamp': None,
      'new_execution_expiration_timestamp': None,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'new_command': {
        'type': 'batch',
        'account_id': '123456789',
        'batch': [
          {
            'type': 'cancel_all_orders',
            'account_id': '123456789',
            'nonce': 8,
            'nonce_group': 5,
          },
          {
            'type': 'place_order',
            'account_id': '123456789',
            'nonce': 9,
            'nonce_group': 5,
            'price': '9.87',
            'client_order_id': 15,
            'instrument_id': '76',
            'quantity': 6,
            'side': 'buy',
            'order_type': 'limit',
            'limit_price': '4.5',
            'post_only': True,
          }
        ]
      }
    })

  def test_cancel_time_triggered_batch(self):
    self.initialize()

    self.user_stream.cancel_time_triggered_batch(1)

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'cancel_timer',
      'timer_id': 1,
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
    })

  def test_executing_internal_transfer(self):
    self.initialize()

    self.user_stream.execute_internal_transfer({'destination_account_id': 1234, 'amount': '0.001'})

    self.assertEqual(self.decrypt_from_trader(self.sent_message), {
      'type': 'internal_transfer',
      'account_id': '123456789',
      'nonce': 7,
      'nonce_group': 5,
      'destination_account_id': 1234,
      'amount': '0.001'
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

  def test_is_not_initialized_after_receiving_subscribed_for_foreign_nonce_group(self):
    self.user_stream.initialize()
    self.user_stream.on_message(self.serialize_to_trader([{
        'type': 'subscribed',
        'nonce': 5,
        'message_nonce_group': 6,
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
    self.open_position_forcefully_closed = None
    self.error = None
    self.disconnect_message = None
    self.order_placed = None
    self.order_cancelled = None
    self.all_orders_cancelled = None
    self.cancel_all_orders_failed = None
    self.order_forcefully_cancelled = None
    self.order_filled = None
    self.timer_added = None
    self.timer_rejected = None
    self.timer_expired = None
    self.timer_triggered = None
    self.timer_updated = None
    self.timer_failed = None
    self.timer_cancelled = None
    self.timer_failed = None
    self.internal_transfer_received = None
    self.internal_transfer_executed = None
    self.internal_transfer_rejected = None
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

  def on_all_orders_cancelled(self, all_orders_cancelled):
    self.all_orders_cancelled = all_orders_cancelled

  def on_cancel_all_orders_failed(self, cancel_all_orders_failed):
    self.cancel_all_orders_failed = cancel_all_orders_failed

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

  def on_open_position_forcefully_closed(self, open_position_forcefully_closed):
    self.open_position_forcefully_closed = open_position_forcefully_closed

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

  def on_timer_added(self, timer_added):
    self.timer_added = timer_added

  def on_timer_rejected(self, timer_rejected):
    self.timer_rejected = timer_rejected

  def on_timer_expired(self, timer_expired):
    self.timer_expired = timer_expired

  def on_timer_triggered(self, timer_triggered):
    self.timer_triggered = timer_triggered

  def on_timer_updated(self, timer_updated):
    self.timer_updated = timer_updated

  def on_timer_update_failed(self, timer_update_failed):
    self.timer_failed = timer_update_failed

  def on_timer_cancelled(self, timer_cancelled):
    self.timer_cancelled = timer_cancelled

  def on_timer_cancel_failed(self, timer_cancel_failed):
    self.timer_failed = timer_cancel_failed

  def on_internal_transfer_received(self, internal_transfer_received):
    self.internal_transfer_received = internal_transfer_received

  def on_internal_transfer_executed(self, internal_transfer_executed):
    self.internal_transfer_executed = internal_transfer_executed

  def on_internal_transfer_rejected(self, internal_transfer_rejected):
    self.internal_transfer_rejected = internal_transfer_rejected

def sign_encrypt(entity, private_key, public_key):
  message = pgpy.PGPMessage.new(json.dumps(entity))
  message |= private_key.sign(message)
  return str(public_key.encrypt(message))


def decrypt_verify(message, private_key, public_key):
  decrypted = private_key.decrypt(pgpy.PGPMessage.from_blob(message))
  if not public_key.verify(decrypted):
    raise AssertionError('Verification failed for message: ' + decrypted)
  return json.loads(decrypted.message)
