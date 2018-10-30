
class Trade:
  def __init__(self, order):
    self.order = order
  
  def __str__(self):
    ''' Allow us to print the Trade object in a pretty format '''
    return "Trade (order='{0}')".format(self.order)
