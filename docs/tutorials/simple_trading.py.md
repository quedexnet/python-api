# Tutorial: Simple Futures Trading

In this tutorial you will learn the basics of how to use our Python API. It will cover:
* subscribing to our realtime WebSocket market stream with public trading data (order books, trades, etc.)
* connecting to our realtime WebSocket user stream to subscribe to your private data (your account changes, order 
  updates, etc.) and to send commands to the exchange (place/cancel orders, etc.)
* making basic trading decisions in reaction to received data

## 1. Imports

In order to use Quedex API, we need to import basic data structures, stream factories 
and twisted reactor.

```python
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

from twisted.internet import reactor

from time import time
```

## 2. Trading Strategy

Next, we will define user-supplied listeners which will be later passed to `UserStream` and `MarketStream` and which
will receive messages that arrive on the WebSockets. For the sake of example, our `MarketStreamListener` will implement
a dummy trading strategy which will trade the first futures instrument it finds (cf. `on_instrument_data`) and will
place a sell order whenever the ask is higher than 0.001 BTC per USD (cf. `on_order_book`; remember that the contracts 
have USD as underyling and prices are expressed in BTC! i.e. this corresponds to buying when BTCUSD is lower than 1000).

// TODO: really? what about threading? does twister guarantee that? 
Notice that we are guaranteed to know the `selected_instrument_id` before we receive any order book - `instrument_data`
is the first message that arrives on market stream (cf. documentation of `MarketStreamListener`).

`user_stream` is used here to place orders which will be defined later.

```python
//:: user_stream_listener :://

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
    if bids and (not bids[0] or float(bids[0][0]) > sell_threshold):
      user_stream.place_order({
        'instrument_id': selected_futures_id, 
        'client_order_id':  int(time() * 1000000),
        'side': 'sell',
        'quantity': 1000,
        'limit_price': bids[0][0],
        'order_type': 'limit',
      })
```

We've implemented only two methods of `MarketStreamListener`, but we could implement more, if we wanted to make decisions
based on different data (e.g. `on_quotes`, `on_trade`, cf. `MarketStreamListener` documentation).

## 3. Risk Control

Tight risk control is essential in every algo strategy. We will now define `UserStreamListener` which will record
every open position (cf. `on_open_position`) and throw them on the market if balance of our account falls bellow
3.1415927 BTC (cf. `on_account_state`).

```python
//== user_stream_listener ==//

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
       self.user_stream.batch(orders)
```

Again, we've implemented only two methods of `UserStreamListener`, but in a real-life scenario we would also have to
control which of our orders get placed (cf. `on_order_placed`/`on_order_place_failed`), which get filled (cf. 
`on_order_filled`), etc.

## 4. Exchange, Trader

```python
quedex_public_key = open("quedex-public-key.asc", "r").read()
exchange = Exchange(quedex_public_key, 'wss://api.quedex.net')

trader_private_key = open("trader-private-key.asc", "r").read()
account_id = open("account-id", "r").read()
trader = Trader(trader_private_key, '83745263748')
trader.decrypt_private_key('s3cret')
```

## 5. Setting up streams

```python

user_stream = UserStream(exchange, trader, SimpleUserListener)
market_stream = MarketStream(exchange, SimpleMarketListener)
```

## 6. Run the Strategy

```python
reactor.run()
```

## 7. Disclaimer

This tutorial does not constitute any investment advice. By running the code presented here you are not guaranteed to
earn any bitcoins (rather the opposite).
