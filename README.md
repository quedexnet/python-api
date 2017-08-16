# Quedex Official Python API

> The best way to communicate with [Quedex Bitcoin Derivatives Exchange](https://quedex.net)
using Python.

## Show Me Some Code

Go straight to our [Simple Trading Tutorial][simple_trading.py.md].

## Why Is This Cool?

 * The API hides all technical concerns (transmission, encryption, serialization,
   threading and connection) from the user so that all programming efforts may be
   **concentrated on trading logic**.
 * We provide classes for easy integration with [Twisted][twisted] which is one of the best
   frameworks for programming network communication in Python. Twisted uses asynchronuous
   input/output which makes our API quite fast.
 * [Simple Trading Tutorial][simple_trading.py.md] is written in literate programming style
   and translates to [simple_trading.py][simple_trading.py] script which is a&nbsp;ready-to-run
   example of using the API. The same file is also used in API's end-to-end test.

## Important!

* All **prices (offers, trades, quotes) are expressed in BTC per USD** rather than the opposite
  (which is the case on&nbsp;most of the other exchanges and our web application). For details,
  see [Inverse Notation][inverse-notation-docs] on our website.
* Quedex Exchange uses an innovative [schedule of session states][faq-session-schedule]. Some
  session states employ different order matching model - namely, [Auction][faq-what-is-auction].
  Please consider this when placing orders.

## Getting the API

To use the API in your Python project include the following in your requirements file
(when installing with `pip`):

```
-e git+https://github.com/quedexnet/python-api.git@664e7db#egg=quedex_api
-e git+https://github.com/SecurityInnovation/PGPy.git@e183c68#egg=PGPy
```
PGPy has to be temporarily included as a commit from the master branch and is not included
as a dependency of the API, because the current version 4.0.1 does not deliver all the required
functionality.

## Documentation

The fastest way of getting to know the API is by looking at the
[Simple Trading Tutorial][simple_trading.py.md]. It shows how to set everything up using
[Autobahn][autobahn] on top of [Twisted][twisted], listen for exchange events
and how to send trading commands.
If you prefer working with bare code, you can take a look at
[examples/simple_trading.py][simple_trading.py] (it is generated from the tutorial).

**Documentation of the API** can be found in [the code][code] (mostly in
[`MarketStream`][market_stream.py] and [`UserStream`][user_stream.py] classes).
Integration with Twisted is implemented in [`UserStreamClientProtocol`][user_stream_client.py]
and [`MarketStreamClientProtocol`][market_stream_client.py] classes.

The API is designed to be flexible and may be used with various implementations of WebSockets
(other than Twisted). To&nbsp;this end, use [`MarketStream`][market_stream.py] and
[`UserStream`][user_stream.py] with the WebSockets library of your choice.
[`UserStreamClientProtocol`][user_stream_client.py] and [`MarketStreamClientProtocol`][
market_stream_client.py] can be used as a reference on how to integrate [`MarketStream`][
market_stream.py] and [`UserStream`][user_stream.py] classes with a WebSockets library.

## Getting Credentials

You'll need to create an instance of `Trader` to use the API (for details see 
[Simple Trading Tutorial][simple_trading.py.md]). `Trader` needs to be provided with your account id
and encrypted private key - you may find them in our web  application - on the trading dashboard 
select the dropdown menu with your email address in the upper right corner and go to User Profile 
(equivalent to visiting https://quedex.net/webapp/profile when logged in).

The `Exchange` entity needs to be provided with the URL of our API, which is `wss://api.quedex.net`
and our public key which for your convenience is bundled with the API - just import it like so
`from quedex_api import quedex_public_key`.

## Contributing Guide

Default channel for submitting **questions regarding the API** is [opening new issues][new-issue].
In cases when information disclosure is&nbsp;not possible, you can contact us at support@quedex.net.

In case you need to add a feature to the API, please [submit an issue][new-issue]
containing change proposal before submitting a PR.

Pull requests containing bugfixes are wery welcome!

## License

Copyright &copy; 2017 Quedex Ltd. API is released under [Apache License Version 2.0](LICENSE).

[autobahn]: https://github.com/crossbario/autobahn-python
[twisted]: https://www.twistedmatrix.com/
[simple_trading.py.md]: docs/tutorials/simple_trading.py.md
[simple_trading.py]: examples/simple_trading.py
[code]: quedex_api
[user_stream.py]: quedex_api/user_stream.py
[market_stream.py]: quedex_api/market_stream.py
[user_stream_client.py]: quedex_api/user_stream.py
[market_stream_client.py]: quedex_api/market_stream.py
[inverse-notation-docs]: https://quedex.net/doc/inverse_notation
[faq-session-schedule]: https://quedex.net/faq#session_schedule
[faq-what-is-auction]: https://quedex.net/faq#what_is_auction
[new-issue]: https://github.com/quedexnet/python-api/issues/new

