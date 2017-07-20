import json

import pgpy


class UserStreamListener(object):
  def on_ready(self):
    """
    Called when UserStream is ready to start receiving messages and sending commands.
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

  def on_order_cancel_failed(self, order_cancel_failed):
    """
    :param order_cancel_failed: a dict of the following format:
      {
        "client_order_id": "<string id>",
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

  def __init__(self, exchange, trader, nonce_group=5):
    super(UserStream, self).__init__()
    self.send_message = None
    self.user_stream_url = exchange.user_stream_url

    self._exchange = exchange
    self._trader = trader

    self._listeners = []
    self._nonce_group = nonce_group
    self._nonce = None
    self._initialized = False

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
      }
    """
    if not self._initialized:
      raise Exception('UserStream not initialized, wait until UserStreamListener.on_read is called')
    place_order_command['type'] = 'place_order'
    check_place_order(place_order_command)
    self._encrypt_send(self._set_nonce_account_id(place_order_command))

  def cancel_order(self, cancel_order_command):
    """
    :param cancel_order_command: a dict of the following format:
      {
        "client_order_id": <positive integer id of the order to cancel>,
      }
    """
    if not self._initialized:
      raise Exception('UserStream not initialized, wait until UserStreamListener.on_read is called')
    check_cancel_order(cancel_order_command)
    cancel_order_command['type'] = 'cancel_order'
    self._encrypt_send(self._set_nonce_account_id(cancel_order_command))

  def modify_order(self, modify_order_command):
    """
    :param modify_order_command: a dict of the following format:
      {
        "client_order_id": <positive integer id of the order to modify>,
        "new_limit_price": "<decimal as string>",
        "new_quantity": <integer>,
      }
    """
    if not self._initialized:
      raise Exception('UserStream not initialized, wait until UserStreamListener.on_read is called')
    check_modify_order(modify_order_command)
    modify_order_command['type'] = 'modify_order'
    self._encrypt_send(self._set_nonce_account_id(modify_order_command))

  def batch(self, order_commands):
    """
    :param order_commands: a list with the number of commands where the following are possible:
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
      ...
     ]
    """
    if not self._initialized:
      raise Exception('UserStream not initialized, wait until UserStreamListener.on_read is called')
    for command in order_commands:
      type = command['type']
      if type == 'place_order':
        check_place_order(command)
      elif type == 'cancel_order':
        check_cancel_order(command)
      elif type == 'modify_order':
        check_modify_order(command)
      else:
        raise ValueError('Unsupported command type: ' + type)
      self._set_nonce_account_id(command)
    self._encrypt_send({
      'type': 'batch',
      'batch': order_commands,
    })

  def initialize(self):
    self._encrypt_send({
      'type': 'get_last_nonce',
      'nonce_group': self._nonce_group,
      'account_id': self._trader.account_id
    })

  def on_message(self, message_wrapper_str):
    try:
      if message_wrapper_str == 'keepalive':
        return

      message_wrapper = json.loads(message_wrapper_str)

      if message_wrapper['type'] == 'error':
        # error_code == maintenance accompanies exchange engine going down for maintenance which
        # causes graceful disconnect of the WebSocket, handled by MarketStreamListener.on_disconnect
        if message_wrapper['error_code'] != 'maintenance':
          self.on_error(Exception('WebSocket error: ' + message_wrapper['error_code']))
        return

      entity = self._decrypt(message_wrapper['data'])

      if entity['type'] == 'last_nonce':
        self._nonce = entity['last_nonce']
        self._encrypt_send(self._set_nonce_account_id({'type': 'subscribe'}))
        return
      elif entity['type'] == 'subscribed':
        self._initialized = True
        self._call_listeners('on_ready')
        return

      self._call_listeners('on_message', entity)
      self._call_listeners('on_' + entity['type'], entity)
    except Exception as e:
      self.on_error(e)

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
    self.send_message(str(self._exchange.public_key.encrypt(message)))

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


def check_cancel_order(cancel_order):
  check_positive_int(cancel_order, 'client_order_id')


def check_modify_order(modify_order):
  check_positive_int(modify_order, 'client_order_id')
  if 'new_limit_price' in modify_order:
    check_positive_decimal(modify_order, 'new_limit_price')
  if 'new_quantity' in modify_order:
    check_positive_int(modify_order, 'new_quantity')
  if 'new_limit_price' not in modify_order and 'new_quantity' not in modify_order:
    raise ValueError('modify_order should have new_limit_price or new_quantity')


def check_positive_decimal(_dict, field_name):
  number = _dict[field_name]
  if not float(number) > 0:
    raise ValueError('%s=%s should be greater than 0' % (field_name, number))


def check_positive_int(_dict, field_name):
  _id = _dict[field_name]
  if not int(_id) > 0:
    raise ValueError('%s=%s should be greater than 0' % (field_name, _id))
