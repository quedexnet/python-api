import itertools

import pgpy


class Trader(object):
  def __init__(self, account_id, private_key):
    self.account_id = account_id
    self.private_key = pgpy.PGPKey()
    self.private_key.parse(private_key)

  def decrypt_private_key(self, passphrase):
    # this is what happens internally in PGPKey.unlock, but we want to leave the key decrypted not
    # only within a context manager as PGPKey.unlock does
    for subkey in itertools.chain([self.private_key], self.private_key.subkeys.values()):
      subkey._key.unprotect(passphrase)
