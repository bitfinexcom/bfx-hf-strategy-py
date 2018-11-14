import time

def now_in_mills():
  return int(round(time.time() * 1000))

class Order:
  def __init__(self, symbol, amount, price, mtsCreate=now_in_mills()):
    self.symbol = symbol
    self.priceAvg = price
    self.mtsCreate = mtsCreate
    self.amount = amount
  
  def __str__(self):
    ''' Allow us to print the Order object in a pretty format '''
    return "Order <'{0}' mtsCreate={1}>".format(self.symbol, self.mtsCreate)
