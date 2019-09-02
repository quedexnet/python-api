import json

import pgpy


class MarketStreamListener(object):
  def on_ready(self):
    """
    Called when MarketStream is ready to start receiving messages.
    """
    pass

  def on_message(self, message):
    """
    Called on every received message.
    """
    pass

  def on_instrument_data(self, instrument_data):
    """
    Called when data about all currently traded instruments are received on the stream - it is
    guaranteed that it will be the first message received before any other.

    :param instrument_data: a dict of the following format:
      {
        "type": "instrument_data",
        "data": {
          "<string id of the instrument>": {
            "type": "inverse_futures"/"inverse_option",
            "instrument_id": "<string id of the instrument>",
            "symbol": "<string>",
            "tick_size": <decimal>,
            "issue_date": <integer millis from epoch UTC>,
            "expiration_date": <integer millis from epoch UTC>,
            "underlying_symbol": "usd",
            "notional_amount": <integer>,
            "fee": <decimal fraction>,
            "taker_to_maker": <decimal fraction>,
            "initial_margin": <decimal fraction>,
            "maintenance_margin" <decimal fraction>,
            "strike": <decimal>, // option only
            "option_type": "call_european"/"put_european", // option only
          }
        }
      }
    """
    pass

  def on_order_book(self, order_book):
    """
    :param order_book: a dict of the following format:
      {
        "type": "order_book",
        "instrument_id": "<string id of the instrument>",
        "bids": [["<decimal price as string>", <int quantity>], ...],
        "asks": [["<decimal price as string>", <int quantity>], ...]
      }
    """
    pass

  def on_quotes(self, quotes):
    """
    :param quotes: a dict of the following format:
      {
        "type": "quotes",
        "instrument_id": "<string id of the instrument>",
        "last": "<decimal price as string>",
        "last_quantity": <integer>,
        "bid": "<decimal price as string>",
        "bid_quantity": <integer>,
        "ask": "<decimal price as string>",
        "ask_quantity": <integer>,
        "volume": <integer>,
        "open_interest": <integer>
        "tap": <decimal price as string or None>
        "lowerLimit": <decimal price as string or None>
        "upperLimit: <decimal price as string or None>
      }
    """
    pass

  def on_spot_data(self, spot_data):
    """
    :param spot_data: a dict of the following format:
    {
        "type": "spot_data",
        "update_time": <integer millis from epoch UTC>
        "spot_data": {
          "<string of the underlying>": {
            "spot_index": "<decimal price as string>",
            "spot_index_change": "<decimal price as string>",
            "settlement_index": "<decimal price as string>",
            "settlement_index_change": "<decimal price as string>",
            "constituents": <list of constituents as list of strings>,
            "spot_quotes": {
               "<constituent as string>": "<decimal price as string>"
            }
          }
        }
      }
    """
    pass

  def on_trade(self, trade):
    """
    :param trade: a dict of the following format:
      {
        "type": "trade",
        "instrument_id": "<string id of the instrument>",
        "trade_id": "<string id of the trade>",
        "timestamp": <integer millis from epoch UTC>,
        "price": "<decimal as string>",
        "quantity": <integer>,
        "liquidity_provider": "buyer"/"seller"/"auction"
      }
    """
    pass

  def on_session_state(self, session_state):
    """
    :param session_state: a dict of the following format:
      {
        "type": "session_state",
        "state": "opening_auction"/"continuous"/"auction"/"closing_auction"/"no_trading"
      }
    """
    pass

  def on_error(self, error):
    """
    Called when an error with market stream occurs (data parsing, signature verification, webosocket error). This means
    a serious problem, which should be investigated (cf. on_disconnect).

    :type error: subtype of Exception
    """
    pass

  def on_disconnect(self, message):
    """
    Called when market stream disconnects cleanly (exchange going down for maintenance, etc.). The
    client should reconnect in such a case.

    :param message: string message with reason of the disconnect
    """
    pass


class MarketStream(object):
  """
  Use this class to connect to the market stream at Quedex, i.e. to the stream of publicly
  available, realtime trading data with order books, trades, etc. The data comes in the form of
  PGP-clearsigned JSON messages - all parsing and verification is handled internally and the client
  receives Python objects (dicts with the data).

  To use this class, implement your own MarketStreamListener (you may inherit from the base class,
  but that's not necessary) and add an instance via add_listener method. Methods of listener will
  be called when respective objects arrive on the market stream. For the format of the data see
  comments on MarketStreamListener.
  """

  def __init__(self, exchange):
    self._exchange = exchange
    self._quedex_key = exchange.public_key
    self._listeners = []

  def add_listener(self, market_stream_listener):
    self._listeners.append(market_stream_listener)

  def remove_listener(self, market_stream_listener):
    self._listeners.remove(market_stream_listener)

  def on_message(self, message_wrapper_str):
    try:

      message_wrapper = json.loads(message_wrapper_str)
      message_type = message_wrapper['type']

      if message_type == 'keepalive':
        return
      elif message_type == 'error':
        self.process_error(message_wrapper)
      elif message_type == 'data':
        self.process_data(message_wrapper);
      else:
        # no-op
        return
    except Exception as e:
      self.on_error(e)

  def process_error(self, message_wrapper):
    # error_code == maintenance accompanies exchange engine going down for maintenance which causes a graceful
    # disconnect of the WebSocket, handled by MarketStreamListener.on_disconnect
    if message_wrapper['error_code'] != 'maintenance':
      self.on_error(Exception('WebSocket error: ' + message_wrapper['error_code']))

  def process_data(self, message_wrapper):
    clearsigned_message_str = message_wrapper['data']

    clearsigned_message = pgpy.PGPMessage().from_blob(clearsigned_message_str)
    if not self._quedex_key.verify(clearsigned_message):
      self.on_error(Exception('Signature verification failed on message: %s' % clearsigned_message_str))

    self._parse_message(clearsigned_message.message)

  def _parse_message(self, message_str):
    message = json.loads(message_str)
    for listener in self._listeners:
      if hasattr(listener, 'on_message'):
        listener.on_message(message)

    listener_name = 'on_' + message['type']
    for listener in self._listeners:
      if hasattr(listener, listener_name):
        getattr(listener, listener_name)(message)

  def on_error(self, error):
    for listener in self._listeners:
      if hasattr(listener, 'on_error'):
        listener.on_error(error)

  def on_disconnect(self, message):
    for listener in self._listeners:
      if hasattr(listener, 'on_disconnect'):
        listener.on_disconnect(message)

  def on_ready(self):
    for listener in self._listeners:
      if hasattr(listener, 'on_ready'):
        listener.on_ready()

  @property
  def market_stream_url(self):
    return self._exchange.market_stream_url
