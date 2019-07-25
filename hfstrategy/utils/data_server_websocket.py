import json
import asyncio

from bfxapi import GenericWebsocket

class DataServerWebsocket(GenericWebsocket):
  '''
  Basic websocket client that simply reads data from the DataServer. This instance
  of the websocket should only ever be used in backtest mode since it isnt capable
  of handling orders.

  Events:
    - connected: called when a connection is made
    - done: fires when the backtest has finished running
  '''
  WS_END = 'bt.end'
  WS_CANDLE = 'bt.candle'
  WS_TRADE = 'bt.trade'
  WS_START = 'bt.start'
  WS_SYNC_START = 'bt.sync.start'
  WS_SYNC_END = 'bt.sync.end'
  WS_CONNECT = 'connected'
  WS_ERROR = 'error'

  def __init__(self, eventEmmitter=None, host='ws://localhost:8899', *args, **kwargs):
    super(DataServerWebsocket, self).__init__(host, *args, **kwargs)

  def run(self, symbol, fromDate, toDate, syncTrades=True, syncCandles=True, tf='30m', syncMissing=True):
    self.fromDate = fromDate
    self.toDate = toDate
    self.tf = tf
    self.sync = syncCandles
    self.syncTrades = syncTrades
    self.syncCandles = syncCandles
    self.syncMissing = syncMissing
    self.symbol = symbol
    loop = asyncio.get_event_loop()
    loop.run_until_complete(super(DataServerWebsocket, self)._run_socket())
  
  async def on_message(self, socketId, message):
    self.logger.debug(message)
    msg = json.loads(message)
    eType = msg[0]
    if eType == self.WS_SYNC_START:
      self.logger.info("Syncing data with backtest server, please wait...")
    elif eType == self.WS_SYNC_END:
      self.logger.info("Syncing complete.")
    elif eType == self.WS_START:
      self.logger.info("Backtest data stream starting...")
    elif eType == self.WS_END:
      self.logger.info("Backtest data stream complete.")
      await self.on_close()
    elif eType == 'data.markets':
      pass
    elif eType == 'error':
      await self.on_error(msg[1])
    elif eType == self.WS_CANDLE:
      await self._on_candle(msg)
    elif eType == self.WS_TRADE:
      await self._on_trade(msg)
    elif eType == self.WS_CONNECT:
      await self.on_open(socketId)
    else:
      self.logger.warn('Unknown websocket command: {}'.format(msg[0]))
  
  def _exec_bt_string(self):
    data = '["exec.bt", ["bitfinex", {}, {}, "{}", "{}", {}, {}, {}]]'.format(
        self.fromDate, self.toDate, self.symbol, self.tf, json.dumps(self.syncCandles),
        json.dumps(self.syncTrades), json.dumps(self.sync))
    return data
  
  async def on_open(self, socketId):
    self._emit('connected')
    data = self._exec_bt_string()
    await self.get_socket(socketId).ws.send(data)
  
  async def _on_candle(self, data):
    candle = data[3]
    self._emit('new_candle', candle)
  
  async def _on_trade(self, data):
    trade = data[2]
    self._emit('new_trade', trade)
