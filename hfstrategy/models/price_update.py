"""
The price update class is used to represent and update in price and contains
data such as indicator values and the price.
"""

class PriceUpdate:
  """
  Price update object contains data related to the current price
  """
  TRADE = 'trade'
  CANDLE = 'candle'

  def __init__(self, price, symbol, mts, p_type, trade=None, candle=None,):
    self.price = price
    self.symbol = symbol
    self.mts = mts
    self.trade = trade
    self.candle = candle
    self.type = p_type
    self.i_v = {}

  def is_trade(self):
    """
    Check if the price update was created due to a new TRADE or a new CANDLE.

    @return bool: True if is TRADE
    """
    return self.type == PriceUpdate.TRADE

  def is_candle(self):
    """
    Check if the price update was created due to a new TRADE or a new CANDLE.

    @return bool: True if is CANDLE
    """
    return self.type == PriceUpdate.CANDLE

  def get_indicator_values(self):
    """
    Get the indicator values"
    """
    return self.i_v

  def set_indicator_values(self, i_v):
    """
    Set the indicator values
    """
    self.i_v = i_v

  def __str__(self):
    """
    Make printing pretty
    """
    return "PriceUpdate <price='{}' symbol='{}' mts='{}' type={}>".format(
        self.price, self.symbol, self.mts, self.type)
