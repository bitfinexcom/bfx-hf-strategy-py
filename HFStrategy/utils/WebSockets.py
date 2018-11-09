import websocket
import json

from .CustomLogger import CustomLogger

class GenericWebsocket(object):
  def __init__(self, host, onCandleHook=None, onTradeHook=None, onCompleteHook=None):
    websocket.enableTrace(True)
    self.ws = ws = websocket.WebSocketApp(
      host,
      on_message=self.on_message,
      on_error=self.on_error,
      on_close=self.on_close
    )
    ws.on_open = self.on_open
    self.logger = CustomLogger('HFWebSocket', logLevel='INFO')
    if not onCandleHook:
      raise KeyError("Expected `onCandleHook` in parameters.")
    if not onTradeHook:
      raise KeyError("Expected `onTradeHook` in parameters.")
    if not onCompleteHook:
      raise KeyError("Expected `onCompleteHook` in parameters.")
    self.onCandleHook = onCandleHook
    self.onTradeHook = onTradeHook
    self.onCompleteHook = onCompleteHook
    ws.run_forever()
  
  def on_error(self, error):
    self.logger.error(error)
  
  def on_close(self):
    self.logger.info("Websocket closed.")
  
  def on_open(self):
    pass

  def on_message(self, message):
    pass

class DataServerWebsocket(GenericWebsocket):
  WS_END = 'bt.end'
  WS_CANDLE = 'bt.candle'
  WS_TRADE = 'bt.trade'
  WS_START = 'bt.start'
  WS_SYNC_START = 'bt.sync.start'
  WS_SYNC_END = 'bt.sync.end'

  def __init__(self, fromDate, toDate, symbol, syncTrades=True,  syncCandles=True, tf='1m',
      candleFields='*', tradeFields='*', syncMissing=True, host='ws://localhost:8899', *args, **kwargs):
    self.fromDate = fromDate
    self.toDate = toDate
    self.symbol = symbol
    self.tf = tf
    self.sync = syncCandles
    self.syncTrades = syncTrades
    self.syncCandles = syncCandles
    self.syncMissing = syncMissing
    self.candleFields = candleFields
    self.tradeFields = tradeFields
    super(DataServerWebsocket, self).__init__(host,  *args, **kwargs)
  
  def on_message(self, message):
    self.logger.debug(message)
    msg = json.loads(message)
    if msg[0] == self.WS_SYNC_START:
      self.logger.info("Syncing data with backtest server, please wait...")
    elif msg[0] == self.WS_SYNC_END:
      self.logger.info("Syncing complete.")
    elif msg[0] == self.WS_START:
      self.logger.info("Backtest data stream starting...")
    elif msg[0] == self.WS_END:
      self.logger.info("Backtest data stream complete.")
      self.ws.close()
      self.onCompleteHook()
    elif msg[0] == self.WS_CANDLE:
      self._onCandle(msg)
    elif msg[0] == self.WS_TRADE:
      self._onTrade(msg)
    else:
      self.logger.warn('Unknown websocket command: {}'.format(msg[0]))
  
  def _exec_bt_string(self):
    data = '["exec.bt", [{}, {}, "{}", "{}", "{}", "{}", "{}", "{}", "{}"]]'.format(
        self.fromDate, self.toDate, self.symbol, self.tf, json.dumps(self.syncCandles),
        json.dumps(self.syncTrades), self.candleFields, self.tradeFields, json.dumps(self.sync))
    return data
  
  def on_open(self):
    data = self._exec_bt_string()
    self.ws.send(data)
  
  def _onCandle(self, data):
    candle = data[3]
    self.onCandleHook(candle)
  
  def _onTrade(self, data):
    trade = data[2]
    self.onTradeHook(trade)

class LiveBfxWebsocket(GenericWebsocket):
  def __init__(self, host='wss://api.bitfinex.com/ws', *args, **kwargs):
    super(LiveBfxWebsocket, self).__init__(host, *args, **kwargs)
  
  def on_message(self, message):
    self.logger.debug(message)

  def on_open(self):
    self.logger.info("Websocket onOpen.")

