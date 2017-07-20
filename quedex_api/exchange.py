import pgpy


class Exchange(object):
  def __init__(self, public_key_str, api_url):
    self._public_key_str = public_key_str
    self.api_url = api_url

  @property
  def market_stream_url(self):
    return self.api_url + '/market_stream'

  @property
  def user_stream_url(self):
    return self.api_url + '/user_stream'

  @property
  def public_key(self):
    public_key = pgpy.PGPKey()
    public_key.parse(self._public_key_str)
    return public_key
