from threading import Event, Thread
from unittest import TestCase
from multiprocessing import Process
import json

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import Data
import pgpy

exchange_key = pgpy.PGPKey()
exchange_key.parse(open('keys/quedex-private-key.asc', 'r').read())
trader_key = pgpy.PGPKey()
trader_key.parse(open('keys/trader-public-key.asc', 'r').read())
messages = []
client_messages_received_lock = Event()
user_stream_sender = None


class TestApiEndToEnd(TestCase):

  def setUp(self):
    market_factory = WebSocketServerFactory('ws://localhost:8080/market_stream')
    user_factory = WebSocketServerFactory('ws://localhost:8080/user_stream')
    market_factory.protocol = MarketStreamServerProtocol
    user_factory.protocol = UserStreamServerProtocol
    market_factory.startFactory()
    user_factory.startFactory()
    root = Data('', 'text/plain')
    root.putChild(b'market_stream', WebSocketResource(market_factory))
    root.putChild(b'user_stream', WebSocketResource(user_factory))
    site = Site(root)
    reactor.listenTCP(8080, site)
    def run_server():
      reactor.run(installSignalHandlers=False)
    Thread(target=run_server).start()

    def run_client():
      from examples import simple_trading
    self.client_process = Process(target=run_client)
    self.client_process.start()

  def tearDown(self):
    self.client_process.terminate()
    reactor.callFromThread(reactor.stop)

  def test_interaction_with_client(self):
    if not client_messages_received_lock.wait(3):
      self.fail('Timed out waiting for the client')

    self.assertEqual(messages[0], {
      'nonce': 1,
      'nonce_group': 5,
      'instrument_id': '71',
      'client_order_id': 1,
      'side': 'sell',
      'quantity': 1000,
      'limit_price': '0.002',
      'order_type': 'limit',
    })
    self.assertEqual(messages[1], {
      'nonce': 2,
      'nonce_group': 5,
      'instrument_id': '71',
      'client_order_id': 2,
      'side': 'sell',
      'quantity': 1000,
      'limit_price': '0.003',
      'order_type': 'limit',
    })
    self.assertEqual(messages[2], {
      'nonce': 3,
      'nonce_group': 5,
      'instrument_id': '71',
      'client_order_id': 3,
      'side': 'buy',
      'quantity': 999,
      'limit_price': '100000',
      'order_type': 'limit',
    })


class UserStreamServerProtocol(WebSocketServerProtocol):
  def __init__(self):
    super(UserStreamServerProtocol, self).__init__()
    global user_stream_sender
    user_stream_sender = self.sendMessage

  def onMessage(self, payload, is_binary):
    messages.append(decrypt_verify(payload))
    if len(messages) == 3:
      client_messages_received_lock.set()


class MarketStreamServerProtocol(WebSocketServerProtocol):
  def onOpen(self):
    self.sendMessage(sign({
      'type': 'instrument_data',
      'data': {'71': {'type': 'futures', 'instrument_id': '71'}},
    }))
    self.sendMessage(sign({
      'type': 'order_book',
      'instrument_id': '71',
      'bids': [['0.00041667', 10]],
      'asks': [],
    }))
    self.sendMessage(sign({
      'type': 'order_book',
      'instrument_id': '71',
      'bids': [['0.002', 10]],
      'asks': [['0.00042016', 10]],
    }))
    self.sendMessage(sign({
      'type': 'order_book',
      'instrument_id': '71',
      'bids': [['0.003', 10]],
      'asks': [['0.00042016', 10]],
    }))

    # send messages on user stream here, to maintain the order of events
    user_stream_sender(sign_encrypt({
      'type': 'last_nonce',
      'last_nonce': 0,
    }))
    user_stream_sender(sign_encrypt({
      'type': 'open_position',
      'instrument_id': '71',
      'quantity': 123,
      'side': 'short',
    }))
    user_stream_sender(sign_encrypt({
      'type': 'account_state',
      'balance': '9999',
    }))
    user_stream_sender(sign_encrypt({
      'type': 'account_state',
      'balance': '3.13',
    }))


def sign(object):
  message = pgpy.PGPMessage.from_blob(json.dumps(object))
  message |= exchange_key.sign(message)
  return str(message)


def sign_encrypt(object):
  message = pgpy.PGPMessage.from_blob(json.dumps(object))
  message |= exchange_key.sign(message)
  return str(trader_key.encrypt(message))


def decrypt_verify(message):
  decrypted = exchange_key.decrypt(message)
  if not trader_key.verify(decrypted):
    raise AssertionError('Verification failed for message: ' + decrypted)
  return json.loads(str(decrypted))
