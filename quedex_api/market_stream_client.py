from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol

pubkey = None


class MarketStreamClientProtocol(WebSocketClientProtocol):

  def onMessage(self, payload, isbinary):
    self.market_stream.on_message(payload)

  def onClose(self, wasClean, code, reason):
    self.market_stream.on_error(Exception('WebSocket closed - %s : %s' % (code, reason)))


class MarketStreamClientFactory(WebSocketClientFactory):
  protocol = MarketStreamClientProtocol

  def __init__(self, market_stream):
    super(MarketStreamClientFactory, self).__init__(market_stream.market_stream_url)
    MarketStreamClientProtocol.market_stream = market_stream
