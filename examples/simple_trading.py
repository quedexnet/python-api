from quedex_api import (
  Exchange,  
  MarketStream, 
  MarketStreamListener, 
  MarketStreamClientFactory,
  Trader,
  UserStream,
  UserStreamListener,
  UserStreamClientFactory,
)

from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import connectWS

from time import time
quedex_public_key = open("quedex-public-key.asc", "r").read()
exchange = Exchange(quedex_public_key, 'wss://api.quedex.net')

trader_private_key = open("trader-private-key.asc", "r").read()
account_id = open("account-id", "r").read()
trader = Trader(trader_private_key, '83745263748')
trader.decrypt_private_key('s3cret')
user_stream = UserStream(exchange, trader)
market_stream = MarketStream(exchange)
selected_futures_id = None
sell_threshold = 0.001

class SimpleMarketListener(MarketStreamListener):
  def on_instrument_data(self, instrument_data):
    global selected_futures_id
    futures = [instrument for instrument in instrument_data['data'].values() if instrument['type'] == 'futures'][0]
    selected_futures_id = futures['instrument_id']

  def on_order_book(self, order_book):
    if order_book['instrument_id'] != selected_futures_id:
      return 
    bids = order_book['bids']
    if bids and (not bids[0] or bids[0][0] > sell_threshold):
      user_stream.place_order({
        'instrument_id': selected_futures_id, 
        'client_order_id':  int(time() * 1000000),
        'side': 'sell',
        'quantity': 1000,
        'limit_price': bids[0][0],
        'order_type': 'limit',
      })
market_stream.add_listener(SimpleMarketListener())
open_positions = {}
balance_threshold = 3.1415927

class SimpleUserListener(UserStreamListener):
  def on_open_position(self, open_position):
    open_positions[open_position['instrument_id']] = open_position

  def on_account_state(self, account_state):
    if account_state['balance'] < balance_threshold:
       # panic
       orders = []
       for open_position in open_positions.values():
        order_side = 'buy' if open_position['side'] == 'short' else 'sell'
        orders.append({
          'type': 'place_order',
          'instrument_id': open_position['instrument_ud'], 
          'client_order_id':  int(time() * 1000000),
          'side': order_side,
          'quantity': open_position['quantity'],
          'limit_price': '0.00000001' if order_side == 'sell' else '100000',
          'order_type': 'limit',
        })
        # use batch whenever a number of orders is placed at once
        user_stream.batch(orders)
user_stream.add_listener(SimpleUserListener())
connectWS(MarketStreamClientFactory(market_stream), ssl.ClientContextFactory())
connectWS(UserStreamClientFactory(user_stream), ssl.ClientContextFactory())
reactor.run()
