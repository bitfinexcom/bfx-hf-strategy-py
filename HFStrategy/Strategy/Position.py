
class Position:
  def __init__(self, symbol, amount, price, trades=[], stop=None, target=None, tag=''):
    self.symbol = symbol
    self.price = price
    self.amount = amount
    self.trades = trades
    self.stop = stop
    self.target = target
    self.tag = tag
  
  def __str__(self):
    ''' Allow us to print the Position object in a pretty format '''
    mainStr = "Position <'{0}' x {1} @ {2}".format(self.symbol, self.amount, self.price)
    if self.stop != None:
        mainStr += " stop={}".format(self.stop)
    if self.target:
        mainStr += " target={}".format(self.target)
    if self.tag:
      mainStr += " tag={}".format(self.tag)
    # format trades into string
    mainStr += " tradeCount={}>".format(len(self.trades))
    return mainStr

