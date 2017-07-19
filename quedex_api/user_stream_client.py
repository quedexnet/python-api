from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol


class UserStreamClientProtocol(WebSocketClientProtocol):
  def __init__(self):
    super(UserStreamClientProtocol, self).__init__()
    self.factory.user_stream.send_message = self.sendMessage

  def onOpen(self):
    self.factory.user_stream.initialize()

  def onMessage(self, payload, isbinary):
    self.factory.user_stream.on_message(payload)

  def onClose(self, wasclean, code, reason):
    if not wasclean:
      self.factory.user_stream.on_error(
        Exception('WebSocket closed with error - %s : %s' % (code, reason))
      )
    else:
      self.factory.user_stream.on_disconnect('WebSocket closed cleanly - %s : %s' % (code, reason))


class UserStreamClientFactory(WebSocketClientFactory):
  protocol = UserStreamClientProtocol

  def __init__(self, user_stream):
    super(UserStreamClientFactory, self).__init__(user_stream.user_stream_url)
    self.user_stream = user_stream
