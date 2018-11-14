import datetime
from .Trade import Trade

class Position:
  def __init__(self, symbol, stop=None, target=None, tag=''):
    self.symbol = symbol
    self.stop = stop
    self.target = target
    self.tag = tag
    self.date = datetime.datetime.now()

    self.price = 0
    self.profitLoss = 0
    self.netProfitLoss = 0
    self.amount = 0
    self.totalFees = 0
    self.volume = 0
    self.trades = []

    self._isOpen = True

  def addTrade(self, trade):
    tradeNV = trade.amount * trade.price
    totalAmount = self.amount + trade.amount
    posNV = self.amount * self.price

    self.trades += [trade]
    self.totalFees += trade.fee
    self.volume += abs(tradeNV)

    if trade.direction == Trade.SHORT:
      self.profitLoss = abs(tradeNV) - abs(posNV)
    else:
      self.profitLoss = abs(posNV) - abs(tradeNV)
    self.netProfitLoss = self.profitLoss - self.totalFees

    if len(self.trades) == 0:
      self.amount = trade.amount
      self.price = trade.price
      return

    if totalAmount == 0:
      self.price = 0
      self.amount = 0
      return

    self.price = (posNV + tradeNV) / totalAmount
    self.amount += trade.amount

  def close(self):
    self._isOpen = False

  def isOpen(self):
    return self._isOpen
  
  def __str__(self):
    ''' Allow us to print the Position object in a pretty format '''
    mainStr = "Position <'{}' x {} @ {} P&L={}".format(
      self.symbol, self.amount, self.price, self.profitLoss)
    if self.stop != None:
        mainStr += " stop={}".format(self.stop)
    if self.target:
        mainStr += " target={}".format(self.target)
    if self.tag:
      mainStr += " tag={}".format(self.tag)
    # format trades into string
    mainStr += " tradeCount={} isOpen={}>".format(len(self.trades), self._isOpen)
    return mainStr

