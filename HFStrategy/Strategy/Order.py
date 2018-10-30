
class Order:
  def __init__(self, symbol, price):
    self.symbol = symbol
    self.priceAvg = price
  
  def __str__(self):
    ''' Allow us to print the Position object in a pretty format '''
    return "Order '{0}'".format(self.symbol)
