import datetime

class ExitType:
  LIMIT = 'LIMIT'
  MARKET = 'MARKET'

class ExitOrder:

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
    return self.stop and self.stop_type == ExitType.MARKET

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

def _percentage_change(previous, current):
  if current == previous:
    return 100.0
  try:
      return ((float(current)-previous)/previous)*100
  except ZeroDivisionError:
      return 0

class Position:
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
    self.profit_loss = 0
    self.profit_loss_perc = 0
    self.net_profit_loss = 0
    self.amount = 0
    self.amount_open = 0
    self.total_fees = 0
    self.volume = 0
    self.orders = {}
    self.realised_profit_loss = {}
    self.exit_order = ExitOrder(0, None, None)
    self.pending_exit_order = None

    self._is_open = True

  def get_orders(self):
    return list(self.orders.values())

  def get_filled_amount(self):
    return self.amount

  def get_profit_loss(self):
    realised = self.get_realised_profit_loss()
    return {
      'realised': realised,
      'current': self.profit_loss,
      'current_percentage': self.profit_loss_perc,
      'gross': realised + self.profit_loss,
      'net': realised + self.profit_loss - self.total_fees
    }

  def get_entry_order(self):
    orders = self.get_orders()
    if len(orders) <= 0:
      return None
    return orders[0]

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
    self.update_with_price(order.price)
    self._recalculate_position_stats()

  def _add_new_order(self, order):
    self.orders[order.id] = order
    # re-calculate position stats
    self._recalculate_position_stats()

  def _update_with_order(self, order):
    old_order = self.orders[order.id]
    if order.mts_update < old_order.mts_update:
      # order is older then existing
      return
    # otherwise replace order with newest
    order.tag = old_order.tag
    self.orders[order.id] = order

  def get_realised_profit_loss(self):
    realised_vals = list(self.realised_profit_loss.values())
    if len(realised_vals) <= 0:
      return 0
    return realised_vals[-1]

  def _recalculate_position_stats(self):
    price_avg = 0.0
    pos_amount = 0.0
    pos_nv = 0.0
    total_fees = 0.0
    volume = 0.0
    for order in list(self.orders.values()):
      # get filled amount
      o_amount = order.amount_filled
      order_nv = o_amount * order.price_avg
      fee = order.fee
      total_fees += fee
      volume += abs(order_nv)

      if pos_amount == 0:
        price_avg = 0.0
        pos_amount = 0.0
      
      if o_amount < 0 and pos_amount > 0:
        # reducing position with short
        realised_profit = (price_avg - order.price) * o_amount
        self.realised_profit_loss[order.id] = realised_profit
      if o_amount > 0 and pos_amount < 0:
        # reducing position with long
        realised_profit = (price_avg - order.price) * o_amount
        self.realised_profit_loss[order.id] = realised_profit


      pos_amount += o_amount
      pos_nv += order_nv

      if pos_amount != 0:
        price_avg = pos_nv / pos_amount

    self.price = price_avg
    self.amount = pos_amount
    self.total_fees = total_fees
    self.volume = volume

  def update_with_price(self, new_price):
    if self.amount > 0:
      self.profit_loss = (new_price - self.price) * abs(self.amount)
      self.profit_loss_perc = _percentage_change(self.price, new_price)
    else:
      prev = self.profit_loss
      self.profit_loss = (self.price - new_price) * abs(self.amount)
      self.profit_loss_perc = _percentage_change(self.price, new_price)
    self.net_profit_loss = self.profit_loss - self.total_fees

  def close(self):
    self._is_open = False

  def is_open(self):
    return self._is_open
  
  def __str__(self):
    ''' Allow us to print the Position object in a pretty format '''
    mainStr = "Position <'{}' x {} @ {} P&L={}".format(
      self.symbol, self.amount, self.price, self.profit_loss)
    if self.stop != None:
        mainStr += " stop={}".format(self.stop)
    if self.target:
        mainStr += " target={}".format(self.target)
    if self.tag:
      mainStr += " tag={}".format(self.tag)
    # format trades into string
    mainStr += " ordersCount={} is_open={}>".format(len(self.orders), self._is_open)
    return mainStr

