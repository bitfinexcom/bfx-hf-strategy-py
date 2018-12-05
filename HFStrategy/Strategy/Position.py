import datetime

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
    self.orders = []

    self._isOpen = True

  def addOrder(self, order):
    orderNV = order.amount * order.priceAvg
    totalAmount = self.amount + order.amount
    posNV = self.amount * self.price
    fee = (order.priceAvg * abs(order.amount)) * 0.002

    self.orders += [order]
    self.totalFees += fee
    self.volume += abs(orderNV)

    if order.amount < 0:
      self.profitLoss = abs(orderNV) - abs(posNV)
    else:
      self.profitLoss = abs(posNV) - abs(orderNV)
    self.netProfitLoss = self.profitLoss - self.totalFees

    if len(self.orders) == 0:
      self.amount = order.amount
      self.price = order.price
      return

    if totalAmount == 0:
      self.price = 0
      self.amount = 0
      return

    self.price = (posNV + orderNV) / totalAmount
    self.amount += order.amount

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
    mainStr += " ordersCount={} isOpen={}>".format(len(self.orders), self._isOpen)
    return mainStr

