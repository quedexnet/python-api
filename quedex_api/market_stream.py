import json

import pgpy

type_to_listener_method = {
  'order_book': 'on_order_book',
  'trade': 'on_trade',
  'quotes': 'on_quotes',
  'session_state': 'on_session_state',
  'instrument_data': 'on_instrument_data',
}


class MarketStream(object):
  def __init__(self, exchange, market_stream_listener):
    self.exchange = exchange
    self.market_stream_listener = market_stream_listener
    self.quedex_key = pgpy.PGPKey()
    self.quedex_key.parse(exchange.public_key)

  def on_message(self, message_wrapper_str):
    try:
      if message_wrapper_str == 'keepalive':
        return

      message_wrapper = json.loads(message_wrapper_str)

      if message_wrapper['type'] == 'error':
        self.market_stream_listener.on_error(Exception('WebSocket error: ' + message_wrapper['error_code']))
        return

      clearsigned_message_str = message_wrapper['data']

      clearsigned_message = pgpy.PGPMessage().from_blob(clearsigned_message_str)
      if not self.quedex_key.verify(clearsigned_message):
        self.market_stream_listener.on_error(
          Exception('Signature verification failed on message: %s' % clearsigned_message_str)
        )

      self._parse_message(clearsigned_message.message)
    except Exception as e:
      self.market_stream_listener.on_error(e)

  def _parse_message(self, message_str):
    message = json.loads(message_str)
    type = message['type']
    if type in type_to_listener_method:
      listener_name = type_to_listener_method[message['type']]
      getattr(self.market_stream_listener, listener_name)(message)

    self.market_stream_listener.on_message(message)

  @property
  def market_stream_url(self):
    return self.exchange.market_stream_url


class MarketStreamListener(object):
  def on_message(self, message):
    pass

  def on_instrument_data(self, instrument_data):
    """
    :param instrument_data: a dict of the following format:
      {
        "type": "instrument_data",
        "data": {
          "<string id of the instrument>": {
            "type": "instrument_data",
            "instrument_id": "<string id of the instrument>",
            "symbol": "<string>",
            "type": "futures"/"option",
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
        "open_interest": <integer>,
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
    """
    pass

  def on_session_state(self, session_state):
    """
    :param session_state: a dict of the following format:
      {
        "type": "session_state",
        "state: "opening_auction"/"continuous"/"auction"/"closing_auction"/"no_trading"
    """
    pass

  def on_error(self, error):
    pass
