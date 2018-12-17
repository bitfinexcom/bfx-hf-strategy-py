import datetime

class ExitType:
  LIMIT = 'LIMIT'
  MARKET = 'MARKET'

class ExitOrder(object):

  def __init__(self, amount, target=None, stop=None, stop_type=ExitType.MARKET,
      target_type=ExitType.MARKET):
    self.target = target
    self.stop = stop
    self.stop_type = stop_type
    self.target_type = target_type
    self.amount = amount
    self.order = None

  def set_order(self, order):
    self.order = order

  def is_target_limit(self):
    return self.target and self.target_type == ExitType.LIMIT

  def is_target_market(self):
    return self.target and self.target_type == ExitType.MARKET

  def is_stop_limit(self):
    return self.stop and self.stop_type == ExitType.LIMIT

  def is_stop_market(self):
    return self.stop and self.stop == ExitType.MARKET

  def is_equal_to(self, exit_order):
    if not exit_order:
      return False
    return (
      self.stop == exit_order.stop and
      self.target == exit_order.target and
      self.stop_type == exit_order.stop_type and
      self.target_type == exit_order.target_type and
      self.amount == exit_order.amount
    )

  def __str__(self):
    mainStr = "ExitOrder <amount={} stop={} target={} stop_type='{}' target_type='{}'>".format(
      self.amount, self.stop, self.target, self.stop_type, self.target_type)
    return mainStr

class Position(object):
  ExitType = ExitType()

  def __init__(self, symbol, stop=None, stop_type=ExitType.MARKET,
      target=None, target_type=ExitType.MARKET, tag=''):
    self.symbol = symbol
    self.stop = stop
    self.stop_type = stop_type
    self.target_type = target_type
    self.target = target
    self.tag = tag
    self.date = datetime.datetime.now()

    self.price = 0
    self.profitLoss = 0
    self.netProfitLoss = 0
    self.amount = 0
    self.totalFees = 0
    self.volume = 0
    # self.orders = []
    self.orders = {}
    self.exit_order = ExitOrder(0, None, None)
    self.pending_exit_order = None

    self._isOpen = True

  def has_reached_stop(self, price_update):
    price = price_update.price
    if not self.exit_order:
      return False
    if not self.exit_order.stop:
      return False
    if self.amount > 0 and price <= self.exit_order.stop:
      return True
    elif self.amount < 0 and price >= self.exit_order.stop:
      return True
    return False

  def has_reached_target(self, price_update):
    price = price_update.price
    if not self.exit_order:
      return False
    if not self.exit_order.target:
      return False
    if self.amount > 0 and price >= self.exit_order.target:
      return True
    elif self.amount < 0 and price <= self.exit_order.target:
      return True
    return False

  def process_order_update(self, order):
    if order.id in self.orders:
      self._update_with_order(order)
    else:
      self._add_new_order(order)

  def _add_new_order(self, order):
    self.orders[order.id] = order
    # re-calculate position stats
    self._recalculate_position_stats()

  def _update_with_order(self, order):
    old_order = self.orders[order.id]
    if order.mtsUpdate < old_order.mtsUpdate:
      # order is older then existing
      return
    # otherwise replace order with newest
    order.tag = old_order.tag
    self.orders[order.id] = order
    # re-calculate position stats
    self._recalculate_position_stats()

  def _recalculate_position_stats(self):
    price_avg = 0
    pos_amount = 0
    pos_nv = 0
    total_fees = 0
    volume = 0
    profit_loss = 0
    for order in list(self.orders.values()):
      # get filled amount
      o_amount = order.amountOrig - order.amount
      order_nv = o_amount * order.priceAvg
      fee = order.fee
      total_fees += fee
      volume += abs(order_nv)

      if o_amount < 0:
        profit_loss = abs(order_nv) - abs(pos_nv)
      else:
        profit_loss = abs(pos_nv) - abs(order_nv)
      
      if pos_amount == 0:
        price_avg = 0
        pos_amount = 0
      else:
        price_avg = (pos_nv + order_nv) / pos_amount

      pos_amount += o_amount
      pos_nv += order_nv

    self.price = price_avg
    self.amount = pos_amount
    self.totalFees = total_fees
    self.volume = volume
    self.profitLoss = profit_loss
    self.netProfitLoss = profit_loss - total_fees

  def add_order(self, order):
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

