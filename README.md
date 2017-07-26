# Quedex Python API

A library used to communicate with [Quedex Bitcoin Derivatives Exchange](https://quedex.net). If you 
have any questions please contact support@quedex.net or open an issue in this repository.

## Using the API

A simple example of how to use the API is available in 
[Simple Trading Tutorial](docs/tutorials/simple_trading.py.md) - it shows how to set it up using
[Autobahn](http://crossbar.io/autobahn/) WebSocket implementation on top of 
[Twisted](https://www.twistedmatrix.com/). The tutorial is written in literate programming style and
translates to [simple_trading.py](examples/simple_trading.py) script which is ready to run (and is
actually run by the end-to-end tests).

The API is designed to be flexible and may be used with various implementations of WebSockets other
than Twisted - to this end, use `MarketStream` and `UserStream` to receive and send messages to the
WebSocket library of your choice.

## Requirements

To use in your Python project include the following in your requirements file (when installing with 
`pip`):

```
-e git+https://github.com/quedexnet/python-api.git@7555436#egg=quedex_api
-e git+https://github.com/SecurityInnovation/PGPy.git@e183c68#egg=PGPy
```
PGPy has to be temporarily included as a commit from the master branch and is not included as a 
dependency of the API, because the current version 4.0.1 does not deliver all the required
functionality.

## Things to remember when using the API

* **All the prices in the API are expressed in BTC per USD** rather than the opposite (which is the 
  case on most of the other exchanges and our web application) - for details see 
  [Inverse Notation](https://quedex.net/doc/inverse_notation) on our website.
* Quedex uses an innovative [schedule](https://quedex.net/faq#session_schedule) of different 
  session states which employ different order matching models - namely
  [auctions](https://quedex.net/faq#what_is_auction) next to continuous trading. Consider this when
  placing orders.
