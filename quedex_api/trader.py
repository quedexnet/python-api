import itertools

import pgpy


class Trader(object):
  def __init__(self, account_id, private_key_str):
    self.account_id = account_id
    self._private_key_str = private_key_str
    self._private_key = None

  def decrypt_private_key(self, passphrase):
    if not self._private_key:
      self._parse_key()

    # this is what happens internally in PGPKey.unlock, but we want to leave the key decrypted not
    # only within a context manager as PGPKey.unlock does
    for subkey in itertools.chain([self._private_key], self._private_key.subkeys.values()):
      subkey._key.unprotect(passphrase)

  @property
  def private_key(self):
    if not self._private_key:
      self._parse_key()
    return self._private_key

  def _parse_key(self):
    self._private_key = pgpy.PGPKey()
    self._private_key.parse(self._private_key_str)
