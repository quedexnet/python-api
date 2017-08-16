# Tutorial: Simple Futures Trading

In this tutorial you will learn the basics of how to use our Python API. It will cover:
* subscribing to our realtime WebSocket market stream with public trading data (order books, trades,
  etc.)
* connecting to our realtime WebSocket user stream to subscribe to your private data (your account
  changes, order updates, etc.) and to send commands to the exchange (place/cancel orders, etc.)
* making basic trading decisions in reaction to received data

## 1. Imports

In order to use Quedex API, we need to import basic data structures, stream factories and utilities
from twisted and autobahn.

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

from twisted.internet import reactor, ssl
from autobahn.twisted.websocket import connectWS
```

## 2. Setting up streams

Next, we will create basic entities required to connect to Quedex - `Exchange` and `Trader`. These
are provided with the public PGP key of Quedex and your encrypted PGP private key, which are read
from files and hardcoded API url and account id. Please read 
[Getting Credentials](../README.md#getting-credentials) to learn where to take your credentials from.

```python
quedex_public_key = open("keys/quedex-public-key.asc", "r").read()
exchange = Exchange(quedex_public_key, 'wss://api.quedex.net')

trader_private_key = open("keys/trader-private-key.asc", "r").read()
trader = Trader('83745263748', trader_private_key)
trader.decrypt_private_key('aaa') 
```

Now we may create the streams, which will be used to communicate with the exchange.

```python
user_stream = UserStream(exchange, trader)
market_stream = MarketStream(exchange)
```

## 3. Trading Strategy

In this step, we will define user-supplied listeners which will be later attached to `UserStream`
and `MarketStream` and which will receive messages that arrive on the WebSockets. For the sake of
example, our `MarketStreamListener` will implement a dummy trading strategy which will trade the
first futures instrument it finds (see `on_instrument_data`) and will place a sell order whenever
the ask price is higher than 0.001 BTC per USD (see `on_order_book`; please remember that the
contracts have USD as underlying and prices are expressed in BTC! i.e. this corresponds to buying
when BTCUSD is lower than 1000).

Notice that we are guaranteed to know the `selected_instrument_id` before we receive any order
book -`instrument_data` is the first message that arrives on market stream (see documentation of
`MarketStreamListener`) and processing of this event will finish before any other starts, thanks to
Twisted's threading model.

```python
selected_futures_id = None
sell_threshold = 0.001
order_id = 0

def get_order_id():
  global order_id
  order_id += 1
  return order_id

class SimpleMarketListener(MarketStreamListener):
  def on_instrument_data(self, instrument_data):
    global selected_futures_id
    futures = [instrument for instrument in instrument_data['data'].values() if instrument['type'] == 'futures'][0]
    selected_futures_id = futures['instrument_id']

  def on_order_book(self, order_book):
    if order_book['instrument_id'] != selected_futures_id:
      return
    bids = order_book['bids']
    # if there are any buy orders and best price is MARKET or above threshold
    if bids and (not bids[0][0] or float(bids[0][0]) > sell_threshold):
      user_stream.place_order({
        'instrument_id': selected_futures_id,
        'client_order_id':  get_order_id(),
        'side': 'sell',
        'quantity': 1000,
        'limit_price': bids[0][0],
        'order_type': 'limit',
      })
```
Once defined, we add the listener to `market_stream`.

```python
market_stream.add_listener(SimpleMarketListener())
```

We've implemented only two methods of `MarketStreamListener`, but we could implement more, if we
wanted to make decisions based on different data (e.g. `on_quotes`, `on_trade`, see
`MarketStreamListener` documentation).

## 4. Risk Control

Tight risk control is essential in every algo strategy. We will now define `UserStreamListener`
which records every open position (see `on_open_position`) and tries to close positions by throwing
orders at market prices if balance of our account falls bellow 3.1415927 BTC (see `on_account_state`).

```python
open_positions = {}
balance_threshold = 3.1415927

class SimpleUserListener(UserStreamListener):
  def on_open_position(self, open_position):
    open_positions[open_position['instrument_id']] = open_position

  def on_account_state(self, account_state):
    if float(account_state['balance']) < balance_threshold:
       # panic
       orders = []
       for open_position in open_positions.values():
        order_side = 'buy' if open_position['side'] == 'short' else 'sell'
        orders.append({
          'type': 'place_order',
          'instrument_id': open_position['instrument_id'],
          'client_order_id':  get_order_id(),
          'side': order_side,
          'quantity': open_position['quantity'],
          'limit_price': '0.00000001' if order_side == 'sell' else '100000',
          'order_type': 'limit',
        })
        # use batch whenever a number of orders is placed at once
        user_stream.batch(orders)
```

And the defined listener is added to `user_stream`.

```python
user_stream.add_listener(SimpleUserListener())
```

Again, we've implemented only two methods of `UserStreamListener`, but in a real-life scenario we
would also have to control which of our orders get placed (see `on_order_placed`/
`on_order_place_failed`), which get filled (see `on_order_filled`), etc.

## 5. Connecting to WebSocket and running the strategy

Once we've created the streams and defined our domain logic, we are ready to connect to the
WebSockets. Please notice that we must wait for `UserStream` to be initialized before we start
receiving messages on `MarketStream`, because we want to send orders on `UserStream` when events
on `MarketStream` arrive - this is achieved by connecting `MarketStream` when
`UserStreamListener.on_ready` callback is called.

```python
class ReadyStateUserListener(UserStreamListener):
  def on_ready(self):
    connectWS(MarketStreamClientFactory(market_stream), ssl.ClientContextFactory())
user_stream.add_listener(ReadyStateUserListener())

connectWS(UserStreamClientFactory(user_stream), ssl.ClientContextFactory())
```

And finally, let's run all the components with Twisted's reactor.

```python
reactor.run()
```

## 6. Not covered in this tutorial

The following topics haven't been covered in this tutorial for clarity, but should be handled in a
real-world scenario:
* error handling - `on_error` methods of both `UserStreamListener` and `MarketStreamListener` should
  be implemented (see their documentation for details); you might also want to employ defensive
  programming when handling events that arrive on the WebSockets,
* reconnecting - the WebSockets may get disconnected due to networking problems or the exchange
  temporarily going down for maintenance (e.g. during updates); you should reconnect them in such
  a case; this may be done in one of the following ways:
  * calling `connectWS()` in `on_disconnect` methods of `UserStreamListener` and
   `MarketStreamListener`,
  * implementing your own `WebSocketClientClientFactory` which also inherits from Twisted's
   `ReconnectingClientFactory` as shown in
   [Autobahn's example](https://github.com/crossbario/autobahn-python/blob/master/examples/twisted/websocket/reconnecting/client.py).

## 7. Disclaimer

This tutorial does not constitute any investment advice. By running the code presented here,
you are not guaranteed to earn any bitcoins (rather the opposite).

