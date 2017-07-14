from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol

pubkey = None


class MarketStreamClientProtocol(WebSocketClientProtocol):

  def onMessage(self, payload, isbinary):
    self.factory.market_stream.on_message(payload)

  def onClose(self, wasclean, code, reason):
    if not wasclean:
      self.factory.market_stream.on_error(Exception('WebSocket closed with error - %s : %s' % (code, reason)))
    else:
      self.factory.market_stream.on_disconnect('WebSocket closed cleanly - %s : %s' % (code, reason))


class MarketStreamClientFactory(WebSocketClientFactory):
  protocol = MarketStreamClientProtocol

  def __init__(self, market_stream):
    super(MarketStreamClientFactory, self).__init__(market_stream.market_stream_url)
    self.market_stream = market_stream
