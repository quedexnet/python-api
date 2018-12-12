import json

import pgpy

from enum import Enum

class UserStreamListener(object):
  def on_ready(self):
    """
    Called when UserStream is ready to start receiving messages and sending commands. Immediately
    after this method is called you will receive a "welcome pack" of messages to this listener which
    will consist of order_placed messages for every pending order, open_position for every open
    position and an initial account_state (see on_order_placed, on_open_position, on_account_state
    methods, respectively).
    """
    pass

  def on_message(self, message):
    """
    Called on every received message.
    """
    pass

  def on_account_state(self, account_state):
    """
    :param account_state: a dict of the following format:
      {
        "type": "account_state",
        "balance": "<decimal as string>",
        "free_balance": "<decimal as string>",
        "total_initial_margin": "<decimal as string>",
        "total_maintenance_margin": "<decimal as string>",
        "total_unsettled_pnl": "<decimal as string>",
        "total_locked_for_orders": "<decimal as string>",
        "total_pending_withdrawal": "<decimal as string>",
        "account_status": "active"/"margin_call"/"liquidation",
      }
    """
    pass

  def on_open_position(self, open_position):
    """
    :param open_position: a dict of the following format:
      {
        "type": "open_position",
        "instrument_id": "<string id of the instrument>",
        "pnl": "<decimal as string>", // futures only
        "maintenance_margin": "<decimal as string>",
        "initial_margin": "<decimal as string>",
        "side": "long"/"short",
        "quantity": <integer>,
        "average_opening_price": "<decimal as string>",
      }
    """
    pass

  def on_order_placed(self, order_placed):
    """
    :param order_placed: a dict of the following format:
      {
        "type": "order_placed",
        "client_order_id": "<string id>",
        "instrument_id": "<string id of the instrument>",
        "limit_price": "<decimal as string>",
        "side": "buy"/"sell",
        "quantity": <integer>,
      }
    """
    pass

  def on_order_place_failed(self, order_place_failed):
    """
    :param order_place_failed: a dict of the following format:
      {
        "client_order_id": "<string id>",
      }
    """
    pass

  def on_order_cancelled(self, order_cancelled):
    """
    :param order_cancelled: a dict of the following format:
      {
        "client_order_id": "<string id>",
      }
    """
    pass

  def on_order_forcefully_cancelled(self, order_forcefully_cancelled):
    """
        :param order_forcefully_cancelled: a dict of the following format:
          {
            "client_order_id": "<string id>",
            "cause": "liquidation"/"settlement",
          }
        """
    pass

  def on_order_cancel_failed(self, order_cancel_failed):
    """
    :param order_cancel_failed: a dict of the following format:
      {
        "client_order_id": "<string id>",
      }
    """
    pass

  def on_all_orders_cancelled(self, all_orders_cancelled):
    """
    :param all_orders_cancelled: dummy parameter, reserved for future extensions
    """
    pass


  def on_cancel_all_orders_failed(self, cancel_all_orders_failed):
    """
    :param cancel_all_orders_failed: a dict of the following format:
      {
        "cause": "session_not_active",
      }
    """
    pass

  def on_order_modified(self, order_modified):
    """
    :param order_modified: a dict of the following format:
      {
        "client_order_id": "<string id>",
      }
    """
    pass

  def on_order_modification_failed(self, order_modification_failed):
    """
    :param order_cancel_failed: a dict of the following format:
      {
        "client_order_id": "<string id>",
      }
    """
    pass

  def on_order_filled(self, order_filled):
    """
    :param order_filled: a dict of the following format:
      {
        "client_order_id": "<string id>",
        "trade_price": "<decimal as string>",
        "trade_quantity": <integer>,
        "leaves_order_quantity": <integer>,
      }
    """
    pass

  def on_timer_added(self, timer_added):
    """
    :param timer_added: a dict of the following format:
      {
        "timer_id": "<string id>",
      }
    """
    pass

  def on_timer_rejected(self, timer_rejected):
    """
    :param timer_rejected: a dict of the following format:
      {
        "timer_id": "<string id>",
        "cause": "too_many_active_timers"/"timer_already_expired"/"timer_already_exists",
      }
    """
    pass

  def on_timer_expired(self, timer_expired):
    """
    :param timer_expired: a dict of the following format:
      {
        "timer_id": "<string id>",
      }
    """
    pass

  def on_timer_triggered(self, timer_triggered):
    """
    :param timer_triggered: a dict of the following format:
      {
        "timer_id": "<string id>",
      }
    """
    pass

  def on_timer_updated(self, timer_updated):
    """
    :param timer_updated: a dict of the following format:
      {
        "timer_id": "<string id>",
      }
    """
    pass

  def on_timer_update_failed(self, timer_update_failed):
    """
    :param timer_update_failed: a dict of the following format:
      {
        "timer_id": "<string id>",
        "cause": "not_found"/"timer_execution_interval_broken",
      }
    """
    pass

  def on_timer_cancelled(self, timer_cancelled):
    """
    :param timer_cancelled: a dict of the following format:
      {
        "timer_id": "<string id>",
      }
    """
    pass

  def on_timer_cancel_failed(self, timer_cancel_failed):
    """
    :param timer_cancel_failed: a dict of the following format:
      {
        "timer_id": "<string id>",
        "cause": "not_found",
      }
    """
    pass

  def on_error(self, error):
    """
    Called when an error with market stream occurs (data parsing, signature verification, webosocket
    error). This means a serious problem, which should be investigated (cf. on_disconnect).

    :type error: subtype of Exception
    """
    pass

  def on_disconnect(self, message):
    """
    Called when market stream disconnects cleanly (exchange going down for maintenance, network
    problem, etc.). The client should reconnect in such a case.

    :param message: string message with reason of the disconnect
    """
    pass


class UserStream(object):
  """
  Use this class to connect to the user stream at Quedex, i.e. to the stream of private, realtime
  data for your account with order confirmations, funds updates, etc.; the stream also
  allows sending commands to the exchange such as placing, cancelling orders, etc. The data is
  exchanged in the form of PGP-encrypted JSON messages - all parsing, decryption/encryption and
  verification/signing is handled internally and the client receives and sends Python objects (dicts
  with data).

  To use this class, implement your own UserStreamListener (you may inherit from the base class,
  but that's not necessary) and add an instance via add_listener method. Methods of listener will
  be called when respective objects arrive on the market stream. For the format of the data see
  comments on UserStreamListener. To send commands to the exchange call respective methods of this
  class - see their comments for the format of the data.
  """

  class BatchMode(Enum):
    STANDARD = 1
    TIME_TRIGGERED_CREATE = 2
    TIME_TRIGGERED_UPDATE = 3

  def __init__(self, exchange, trader, nonce_group=5):
    """
    :param nonce_group: value between 0 and 9, has to be different for every WebSocket connection
                        opened to the exchange (e.g. browser and trading bot); our webapp uses
                        nonce_group=0
    """
    super(UserStream, self).__init__()
    self.send_message = None
    self.user_stream_url = exchange.user_stream_url

    self._exchange = exchange
    self._trader = trader

    self._listeners = []
    self._nonce_group = nonce_group
    self._nonce = None
    self._initialized = False
    self._batch = None
    self._batch_mode = None
    self._time_triggered_batch_command = None

  def add_listener(self, listener):
    self._listeners.append(listener)

  def remove_listener(self, listener):
    self._listeners.remove(listener)

  def place_order(self, place_order_command):
    """
    :param place_order_command: a dict of the following format:
      {
        "client_order_id": <positive integer id unique among orders>,
        "instrument_id": "<string id of the instrument>",
        "order_type": "limit",
        "limit_price": "<decimal as string>",
        "side": "buy"/"sell",
        "quantity": <integer>,
        "post_only": <bool, optional field, True means order placement will fail
                      if it would cause immediate fill, absence has the same
                      effect as False>
      }
    """
    self._check_if_initialized()
    place_order_command['type'] = 'place_order'
    check_place_order(place_order_command)
    self._set_nonce_account_id(place_order_command)
    if self._batch_mode:
      self._batch.append(place_order_command)
    else:
      self._encrypt_send(place_order_command)

  def cancel_order(self, cancel_order_command):
    """
    :param cancel_order_command: a dict of the following format:
      {
        "client_order_id": <positive integer id of the order to cancel>,
      }
    """
    self._check_if_initialized()
    check_cancel_order(cancel_order_command)
    cancel_order_command['type'] = 'cancel_order'
    self._set_nonce_account_id(cancel_order_command)
    if self._batch_mode:
      self._batch.append(cancel_order_command)
    else:
      self._encrypt_send(cancel_order_command)

  def cancel_all_orders(self):
    self._check_if_initialized()
    cancel_all_orders_command = {'type': 'cancel_all_orders'}
    self._set_nonce_account_id(cancel_all_orders_command)
    if self._batch_mode:
      self._batch.append(cancel_all_orders_command)
    else:
      self._encrypt_send(cancel_all_orders_command)

  def modify_order(self, modify_order_command):
    """
    :param modify_order_command: a dict with following contents:
    Mandatory key "client_order_id":
      {
        "client_order_id": <positive integer id of the order to modify>
      }
    At lest one of keys: "new_price", "new_quantity":
      {
        "new_price": "<decimal as string>",
        "new_quantity": <integer>,
      }
    Optional key "post_only" (absence has the same effect as False):
      {
        "post_only": <bool, True means modification will fail if it would cause immediate fill>
      }
    """
    self._check_if_initialized()
    check_modify_order(modify_order_command)
    modify_order_command['type'] = 'modify_order'
    self._set_nonce_account_id(modify_order_command)
    if self._batch_mode:
      self._batch.append(modify_order_command)
    else:
      self._encrypt_send(modify_order_command)

  def batch(self, order_commands):
    """
    :param order_commands: a list with a number of commands where the following are possible:
     [
      {
        "type": "place_order",
        // for the rest of the fields see place_order method
      },
      {
        "type": "cancel_order",
        // for the rest of the fields see cancel_order method
      },
      {
        "type": "modify_order",
        // for the rest of the fields see modify_order method
      },
      {
        "type": "cancel_all_orders",
      },
      ...
     ]
    """
    self._verify_batch_commands_and_set_nonces_and_account_id(order_commands)
    self._send_batch_no_checks(order_commands)

  def start_batch(self):
    """
    After this method is called all calls to place_order, cancel_order, modify_order result in
    caching of the commands which are then sent once send_batch is called.
    """
    if self._batch_mode == self.BatchMode.TIME_TRIGGERED_CREATE:
      raise Exception('Cannot start another batch. Currently creating time triggered batch')
    if self._batch_mode == self.BatchMode.TIME_TRIGGERED_UPDATE:
      raise Exception('Cannot start another batch. Currently updating time triggered batch')
    self._batch = []
    self._batch_mode = self.BatchMode.STANDARD

  def send_batch(self):
    """
    Sends batch created from calling place_order, cancel_order, modify_order after calling
    start_batch.
    """
    if not (self._batch_mode == self.BatchMode.STANDARD):
      raise Exception('send_batch called without calling start_batch first')
    if len(self._batch) == 0:
      raise ValueError("Empty batch")
    self._send_batch_no_checks(self._batch)
    self._batch = None
    self._batch_mode = None

  def time_triggered_batch(self, timer_id, execution_start_timestamp, execution_expiration_timestamp, order_commands):
    """
    Sends a time triggered batch with the given list of order commands to the exchange.
    When a time triggered batch is received by the exchange engine, a new timer is registered.
    Based on the timer configuration, at some point in the future (between executionStartTimestamp and executionExpirationTimestamp),
    all the carried order commands are processed, one by one, in the creation order.

    Please refer to the API documentation for a detailed explanation of creating timers.

    :param timer_id: a user defined timer identifier, can be used to cancel or update batch
    :param execution_start_timestamp: the defined batch will not be executed before this timestamp
    :param execution_expiration_timestamp: the defined batch will not be executed after this timestamp
    :param order_commands: a list with a number of commands where the following are possible:
     [
      {
        "type": "place_order",
        // for the rest of the fields see place_order method
      },
      {
        "type": "cancel_order",
        // for the rest of the fields see cancel_order method
      },
      {
        "type": "modify_order",
        // for the rest of the fields see modify_order method
      },
      {
        "type": "cancel_all_orders",
      },
      ...
     ]
    """
    self._check_if_initialized()
    command = {
      'type': 'add_timer',
      'timer_id': timer_id,
      'execution_start_timestamp': execution_start_timestamp,
      'execution_expiration_timestamp': execution_expiration_timestamp
    }
    self._set_nonce_account_id(command)
    self._verify_batch_commands_and_set_nonces_and_account_id(order_commands)
    command['command'] = self._create_batch_command_no_checks(order_commands)
    self._encrypt_send(command)

  def start_time_triggered_batch(self, timer_id, execution_start_timestamp, execution_expiration_timestamp):
    """
    After this method is called all calls to place_order, cancel_order, modify_order result in
    caching of the commands which are then sent once send_time_triggered_batch is called.

    :param timer_id: a user defined timer identifier, can be used to cancel or update batch
    :param execution_start_timestamp: the defined batch will not be executed before this timestamp
    :param execution_expiration_timestamp: the defined batch will not be executed after this timestamp
    """
    self._check_if_initialized()
    if self._batch_mode == self.BatchMode.STANDARD:
      raise Exception('Cannot start another batch. Currently creating batch')
    if self._batch_mode == self.BatchMode.TIME_TRIGGERED_UPDATE:
      raise Exception('Cannot start another batch. Currently updating time triggered batch')
    self._batch = []
    self._batch_mode = self.BatchMode.TIME_TRIGGERED_CREATE
    command = {
      'type': 'add_timer',
      'timer_id': timer_id,
      'execution_start_timestamp': execution_start_timestamp,
      'execution_expiration_timestamp': execution_expiration_timestamp
    }
    self._set_nonce_account_id(command)
    self._time_triggered_batch_command = command

  def send_time_triggered_batch(self):
    """
    Sends time triggered batch created from calling place_order, cancel_order, modify_order after calling
    start_time_triggered_batch, which creates timer in exchange engine with a batch of order commands.

    When a time triggered batch is received by the exchange engine, a new timer is registered.
    Based on the timer configuration, at some point in the future (between executionStartTimestamp and executionExpirationTimestamp),
    all the carried order commands are processed, one by one, in the creation order.

    Please refer to the API documentation for a detailed explanation of creating timers.
    """
    if not (self._batch_mode == self.BatchMode.TIME_TRIGGERED_CREATE):
      raise Exception('send_time_triggered_batch called without calling start_time_triggered_batch first')
    if len(self._batch) == 0:
      raise ValueError("Empty batch")
    self._time_triggered_batch_command['command'] = self._create_batch_command_no_checks(self._batch)
    self._encrypt_send(self._time_triggered_batch_command)
    self._batch = None
    self._batch_mode = None
    self._time_triggered_batch_command = None

  def update_time_triggered_batch(self, timer_id, new_execution_start_timestamp, new_execution_expiration_timestamp, new_order_commands):
    """
    Sends the modified batch to the exchange.

    At least one of the following must be modified:
    - execution_start_timestamp
    - execution_expiration_timestamp
    - order_commands

    Please refer to the API documentation for detailed explanation of updating timers.

    :param timer_id: a user defined timer identifier, can be used to cancel or update batch
    :param new_execution_start_timestamp: new value of executionStartTimestamp (optional)
    :param new_execution_expiration_timestamp: new value of executionStartTimestamp (optional)
    :param new_order_commands: a new list with a number of commands (optional) where the following are possible:
     [
      {
        "type": "place_order",
        // for the rest of the fields see place_order method
      },
      {
        "type": "cancel_order",
        // for the rest of the fields see cancel_order method
      },
      {
        "type": "modify_order",
        // for the rest of the fields see modify_order method
      },
      {
        "type": "cancel_all_orders",
      },
      ...
     ]
    """
    self._check_if_initialized()
    command = self._create_update_timer_command(
      timer_id,
      new_execution_start_timestamp,
      new_execution_expiration_timestamp
    )
    if not new_order_commands == None and not len(new_order_commands) == 0:
      self._verify_batch_commands_and_set_nonces_and_account_id(new_order_commands)
      command['new_command'] = self._create_batch_command_no_checks(new_order_commands)
    self._validate_update_command(command)
    self._encrypt_send(command)

  def start_update_time_triggered_batch(self, timer_id, new_execution_start_timestamp, new_execution_expiration_timestamp):
    """
    This method is used to update an existing time triggered batch.

    After this method is called all calls to place_order, cancel_order, modify_order result in
    caching of the commands which are then sent once send_update_time_triggered_batch is called.
    These commands replace commands specified during the batch creation.

    At least one of the following must be modified:
    - execution_start_timestamp
    - execution_expiration_timestamp
    - order_commands (by calling methods like place_order etc.)

    Please refer to the API documentation for a detailed explanation of updating timers.

    :param timer_id: a user defined timer identifier, the same as used when creating the batch
    :param new_execution_start_timestamp: new value of executionStartTimestamp (optional)
    :param new_execution_expiration_timestamp: new value of executionStartTimestamp (optional)
    """
    self._check_if_initialized()
    if self._batch_mode == self.BatchMode.STANDARD:
      raise Exception('Cannot start another batch. Currently creating batch')
    if self._batch_mode == self.BatchMode.TIME_TRIGGERED_CREATE:
      raise Exception('Cannot start another batch. Currently creating time triggered batch')
    self._batch = []
    self._batch_mode = self.BatchMode.TIME_TRIGGERED_UPDATE
    self._time_triggered_batch_command = self._create_update_timer_command(
      timer_id,
      new_execution_start_timestamp,
      new_execution_expiration_timestamp
    )

  def send_update_time_triggered_batch(self):
    """
    Sends the modified batch to the exchange.

    At least one of the following must be modified:
    - execution_start_timestamp
    - execution_expiration_timestamp
    - order_commands (by calling place_order, cancel_order, modify_order after calling start_update_time_triggered_batch)

    Specified batch replaces the one registered during the timer creation.

    Please refer to the API documentation for a detailed explanation of updating timers.

    """
    if not (self._batch_mode == self.BatchMode.TIME_TRIGGERED_UPDATE):
      raise Exception('send_update_time_triggered_batch called without calling start_update_time_triggered_batch first')

    if not self._batch == None and not len(self._batch) == 0:
      self._time_triggered_batch_command['new_command'] = self._create_batch_command_no_checks(self._batch)
    self._validate_update_command(self._time_triggered_batch_command)
    self._encrypt_send(self._time_triggered_batch_command)
    self._batch = None
    self._batch_mode = None
    self._time_triggered_batch_command = None

  def cancel_time_triggered_batch(self, timer_id):
    """
    Cancels an existing time triggered batch.

    :param timer_id: a user defined timer identifier, the same as used when creating the batch
    """
    self._check_if_initialized()
    command = {
      'type': 'cancel_timer',
      'timer_id': timer_id
    }
    self._set_nonce_account_id(command)
    self._encrypt_send(command)

  def _create_update_timer_command(self, timer_id, new_execution_start_timestamp, new_execution_expiration_timestamp):
    command = {
      'type': 'update_timer',
      'timer_id': timer_id,
      'new_execution_start_timestamp': new_execution_start_timestamp,
      'new_execution_expiration_timestamp': new_execution_expiration_timestamp
    }
    self._set_nonce_account_id(command)
    return command

  def _validate_update_command(self, update_timer_command):
    if (update_timer_command.get('new_command') == None
        and update_timer_command['new_execution_start_timestamp'] == None
        and update_timer_command['new_execution_expiration_timestamp'] == None):
      raise ValueError('Update at least one: order_commands, execution_start_timestamp, execution_expiration_timestamp')

  def _send_batch_no_checks(self, order_commands):
    self._encrypt_send(
      self._create_batch_command_no_checks(order_commands)
    )

  def _create_batch_command_no_checks(self, order_commands):
    return {
      'type': 'batch',
      'account_id': self._trader.account_id,
      'batch': order_commands,
    }

  def _verify_batch_commands_and_set_nonces_and_account_id(self, order_commands):
    if len(order_commands) == 0:
      raise ValueError("Empty batch")
    for command in order_commands:
      type = command['type']
      if type == 'place_order':
        check_place_order(command)
      elif type == 'cancel_order':
        check_cancel_order(command)
      elif type == 'modify_order':
        check_modify_order(command)
      elif type == 'cancel_all_orders':
        check_cancel_all_orders(command)
      else:
        raise ValueError('Unsupported command type: ' + type)
      self._set_nonce_account_id(command)

  def initialize(self):
    self._encrypt_send({
      'type': 'get_last_nonce',
      'nonce_group': self._nonce_group,
      'account_id': self._trader.account_id,
    })

  def on_message(self, message_wrapper_str):
    try:

      message_wrapper = json.loads(message_wrapper_str)
      message_type = message_wrapper['type']

      if message_type == 'keepalive':
        return
      elif message_type == 'error':
        self.process_error(message_wrapper)
      elif message_type == 'data':
        self.process_data(message_wrapper)
      else:
        # no-op
        return
    except Exception as e:
      self.on_error(e)

  def process_error(self, message_wrapper):
    # error_code == maintenance accompanies exchange engine going down for maintenance which
    # causes graceful disconnect of the WebSocket, handled by MarketStreamListener.on_disconnect
    if message_wrapper['error_code'] != 'maintenance':
      self.on_error(Exception('WebSocket error: ' + message_wrapper['error_code']))

  def process_data(self, message_wrapper):
    for entity in self._decrypt(message_wrapper['data']):
      if entity['type'] == 'last_nonce' and entity['nonce_group'] == self._nonce_group:
        self._nonce = entity['last_nonce']
        self._encrypt_send(self._set_nonce_account_id({'type': 'subscribe'}))
        return
      elif entity['type'] == 'subscribed' and entity['message_nonce_group'] == self._nonce_group:
        self._initialized = True
        self._call_listeners('on_ready')
        continue

      self._call_listeners('on_message', entity)
      self._call_listeners('on_' + entity['type'], entity)

  def on_error(self, error):
    self._call_listeners('on_error', error)

  def on_disconnect(self, message):
    self._call_listeners('on_disconnect', message)

  def _set_nonce_account_id(self, entity):
    self._nonce += 1
    entity['nonce'] = self._nonce
    entity['nonce_group'] = self._nonce_group
    entity['account_id'] = self._trader.account_id
    return entity

  def _encrypt_send(self, entity):
    message = pgpy.PGPMessage.new(json.dumps(entity))
    message |= self._trader.private_key.sign(message)
    # explicit encode for Python 3 compatibility
    self.send_message(str(self._exchange.public_key.encrypt(message)).encode('utf8'))

  def _decrypt(self, encrypted_str):
    encrypted = pgpy.PGPMessage().from_blob(encrypted_str)
    decrypted = self._trader.private_key.decrypt(encrypted)
    if not self._exchange.public_key.verify(decrypted):
      raise AssertionError('Verification failed for message: ' + decrypted)
    return json.loads(decrypted.message)

  def _call_listeners(self, method_name, *args, **kwargs):
    for listener in self._listeners:
      if hasattr(listener, method_name):
        getattr(listener, method_name)(*args, **kwargs)

  def _check_if_initialized(self):
    if not self._initialized:
      raise Exception('UserStream not initialized, wait until UserStreamListener.on_ready is called.')

def check_place_order(place_order):
  check_positive_int(place_order, 'client_order_id')
  check_positive_decimal(place_order, 'limit_price')
  check_positive_int(place_order, 'quantity')
  check_positive_int(place_order, 'instrument_id')
  side = place_order['side']
  if side.lower() != 'buy' and side.lower() != 'sell':
    raise ValueError('side has to be either "buy" or "sell", got: %s' % side)
  order_type = place_order['order_type']
  if order_type.lower() != 'limit':
    raise ValueError('The only supported order_type is limit currently')
  if 'post_only' in place_order:
    check_boolean(place_order, 'post_only')


def check_cancel_order(cancel_order):
  check_positive_int(cancel_order, 'client_order_id')


def check_modify_order(modify_order):
  check_positive_int(modify_order, 'client_order_id')
  if 'new_price' in modify_order:
    check_positive_decimal(modify_order, 'new_price')
  if 'new_quantity' in modify_order:
    check_positive_int(modify_order, 'new_quantity')
  if 'new_price' not in modify_order and 'new_quantity' not in modify_order:
    raise ValueError('modify_order should have new_price or new_quantity')
  if 'post_only' in modify_order:
    check_boolean(modify_order, 'post_only')

def check_cancel_all_orders(cancel_all_orders):
  pass

def check_positive_decimal(_dict, field_name):
  number = _dict[field_name]
  if not float(number) > 0:
    raise ValueError('%s=%s should be greater than 0' % (field_name, number))


def check_positive_int(_dict, field_name):
  _id = _dict[field_name]
  if not int(_id) > 0:
    raise ValueError('%s=%s should be greater than 0' % (field_name, _id))

def check_boolean(_dict, field_name):
  _id = _dict[field_name]
  if type(_id) is not bool:
    raise TypeError('%s=%s should be bool' % (field_name, _id))
