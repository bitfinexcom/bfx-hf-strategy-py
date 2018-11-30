class PriceUpdate:
  TRADE = 'trade'
  CANDLE = 'candle'

  def __init__(self, price, symbol, mts, pType, trade=None, candle=None,):
    self.price = price
    self.symbol = symbol
    self.mts = mts
    self.trade = trade
    self.candle = candle
    self.type = pType
    self.iv = {}

  def is_trade(self):
    return self.type == PriceUpdate.TRADE

  def is_candle(self):
    return self.type == PriceUpdate.CANDLE

  def get_indicator_values(self):
    return self.iv

  def set_indicator_values(self, iv):
    self.iv = iv

  def __str__(self):
    return "PriceUpdate <price='{}' symbol='{}' mts='{}' type={}>".format(
      self.price, self.symbol, self.mts, self.type
    )
