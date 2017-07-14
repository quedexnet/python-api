

class Exchange(object):
  def __init__(self, public_key, api_url):
    self.public_key = public_key
    self.api_url = api_url

  @property
  def market_stream_url(self):
    return self.api_url + '/market_stream'
