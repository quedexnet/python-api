"""
This file maybe changed or deleted with the subsequent releases of the API.
"""
import json

from trader import Trader


def load_trader_from_props(props_str):
  account = json.loads(props_str)['exchangeAccount']
  return Trader(account['accountId'], account['privateKey'])
