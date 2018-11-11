import websocket
import json
import time

from .CustomLogger import CustomLogger
from btfxwss import BtfxWss

class GenericWebsocket(object):
  def __init__(self, host, onCandleHook=None, onTradeHook=None, onCompleteHook=None):
    if not onCandleHook:
      raise KeyError("Expected `onCandleHook` in parameters.")
    if not onTradeHook:
      raise KeyError("Expected `onTradeHook` in parameters.")
    if not onCompleteHook:
      raise KeyError("Expected `onCompleteHook` in parameters.")
    self.onCandleHook = onCandleHook
    self.onTradeHook = onTradeHook
    self.onCompleteHook = onCompleteHook

    self.logger = CustomLogger('HFWebSocket', logLevel='INFO')
  
  def on_error(self, error):
    self.logger.error(error)
  
  def on_close(self):
    self.logger.info("Websocket closed.")
  
  def on_open(self):
    pass

  def on_message(self, message):
    pass

class DataServerWebsocket(GenericWebsocket):
  '''
  Basic websocket client that simply reads data from the DataServer. This instance
  of the websocket should only ever be used in backtest mode since it isnt capable
  of handling orders.
  '''
  WS_END = 'bt.end'
  WS_CANDLE = 'bt.candle'
  WS_TRADE = 'bt.trade'
  WS_START = 'bt.start'
  WS_SYNC_START = 'bt.sync.start'
  WS_SYNC_END = 'bt.sync.end'

  def __init__(self, fromDate, toDate, symbol, syncTrades=True,  syncCandles=True, tf='1m',
      candleFields='*', tradeFields='*', syncMissing=True, host='ws://localhost:8899', *args, **kwargs):
    websocket.enableTrace(True)
    self.ws = ws = websocket.WebSocketApp(
      host,
      on_message=self.on_message,
      on_error=self.on_error,
      on_close=self.on_close
    )
    ws.on_open = self.on_open
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
    self.ws.run_forever()
  
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
  '''
  More complex websocket that heavily relies on the btfxwss module. This websocket requires
  authentication and is capable of handling orders.
  https://github.com/Crypto-toolbox/btfxwss
  '''
  def __init__(self, symbol, host='wss://api.bitfinex.com/ws', *args, **kwargs):
    super(LiveBfxWebsocket, self).__init__(host, *args, **kwargs)
    wss = BtfxWss()
    wss.start()

    while not wss.conn.connected.is_set():
      time.sleep(1)
    
    # Subscribe to some channels
    wss.subscribe_to_ticker('BTCUSD')
    wss.subscribe_to_candles('BTCUSD')
    wss.subscribe_to_order_book('BTCUSD')

    # Accessing data stored in BtfxWss:
    while True:
      tickers = wss.tickers('BTCUSD')
      trades = wss.trades('BTCUSD')
      candles = wss.candles('BTCUSD', '1m')
      while not tickers.empty():
        print ('Ticker')
        print(tickers.get())
      while not trades.empty():
        print ('Trade')
        print(trades.get())
      while not candles.empty():
        print ('Candles')
        print(candles.get())
  
  def on_message(self, message):
    self.logger.debug(message)

  def on_open(self):
    self.logger.info("Websocket onOpen.")

