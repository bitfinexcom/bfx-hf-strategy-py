import logging

class Position(object):

  def close_position(self, orderParams):
    # some state usage here
    pass

  def open_position(self, orderParams):
    pass
  
  def update_position(self, orderParams):
    pass

  def openShortPositionMarket(self, params):
    sym = params.get('symbol')
    pos = self.getPosition(sym)

    if pos: # TODO: Throw exception or use logging facility
      logging.debug('position already exists for symbol %s' % (sym))
      return
    
    # TODO

    logging.info('Opened short position')
    pass

  def openLongPositionMarket(self, params):
    sym = params.get('symbol')
    pos = self.getPosition(sym)

    if pos: # TODO: Throw exception or use logging facility
      logging.debug('position already exists for symbol %s' % (sym))
      return
    
    # TODO

    logging.info('Open long position')
    pass

  def closePositionMarket(self, params):
    pass

