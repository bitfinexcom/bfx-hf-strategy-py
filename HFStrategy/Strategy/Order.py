import time

def now_in_mills():
  return int(round(time.time() * 1000))

class Order:
  def __init__(self, symbol, price, mtsCreate=now_in_mills()):
    self.symbol = symbol
    self.priceAvg = price
    self.mtsCreate = mtsCreate
  
  def __str__(self):
    ''' Allow us to print the Order object in a pretty format '''
    return "Order <'{0}'>".format(self.symbol)
