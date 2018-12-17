
```python
from hfstrategy import Strategy
from bfxhfindicators import EMA

class EMAStrategy(Strategy):
  indicators = {
    'emaL': EMA([100]),
    'emaS': EMA([20])
  }

  async def onEnter(self, update):
    iv = self.indicatorValues()
    emaS = self.indicators['emaS']
    if emaS.crossed(iv['emaL']):
      await self.openLongPositionMarket(
          mtsCreate=update['mts'], price=update['price'], amount=0.1)
  
  async def onUpdateLong(self, update):
    iv = self.indicatorValues()
    if iv['emaS'] < l:
      await self.closePositionMarket(
          price=update['price'], mtsCreate=update['mts'])

```

### Execute

```python
import os
from hfstrategy import executeLive
executeLive(strategy, os.getenv("BFX_KEY"), os.getenv("BFX_SECRET"))
```

# Honey Framework for Python
This repo serves as a framework for creating trading bots/strategies on the Bitfinex platform. It consists of a set of order methods and an architecture compatible with bfx-hf-data-server and bfx-hf-backtest for backtests on historical candle/trade data, which can be transitioned seamlessly to trading on the live markets.

Strategies written using this framework must define a set of update methods, called on each tick (with either a trade or a candle), along with a set of indicators which are automatically updated on each tick. The indicators are made available to the strategy methods, and can be queried to direct trading behavior.


Install bfx-hf-indicators-py:
```sh
git clone https://github.com/bitfinexcom/bfx-hf-indicators-py
cd bfx-hf-indicators-py
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

Run example ema_cross backtest:
```sh
# in bfx-strategy-hf-py
cd examples
python3 ema_cross.py  
```

# Features
- Execute on Live or with backtest data
- Realtime data feeds
- Simple interface
- Quick websocket connections
- Open/Close/Update positions

# Quickstart

## Defining a strategy
To define a trading strategy, first we have to create a new object that implements the `hfstrategy` class. Then we need to decide on a set of indicators to use and bind them to the classes `indicators` variable. Strategies created with it can be used with bfx-hf-backtest or with the exec method to run on the live market. An example strategy follows below:
```python
from hfstrategy import Strategy
from bfxhfindicators import EMA

class EMAStrategy(Strategy):
  indicators = {
    'emaL': EMA([100]),
    'emaS': EMA([20])
  }

  async def onEnter(self, update):
    # Do something
  
  async def onUpdateLong(self, update):
    # Do something
```
The above strategy defines two EMA indicators, emaL and emaS, with periods of 100 and 20 respectively, and 3 update methods; In total, 5 update methods are available:

- `onEnter` - called when no position is open
- `onUpdateLong` - called when a long position is open
- `onUpdateShort` - called when a short position is open
- `onUpdate` - called when any position is open
- `onPriceUpdate` - called on every tick

## Update Handlers

All update handlers must be asynchronous, and receive an update json object which has the following fields:

- `type` - 'candle' or 'trade', indicating which fields are available
- `mts` - Timestamp, in ms
- `price` - Candle or trade price (depends on candlePrice strategy setting)
for candles, open, high, low, close, and vol are provided

Strategy state is stored in the strategy object (`self`) and can be queried for historical candle data, indicators & indicator values, open positions, and previous strategy trades. For an example, see the EMA cross example `onEnter` handler below.

```python
async def onEnter(self, update):
  iv = self.indicatorValues()
  emaS = self.indicators['emaS']

  s = iv['emaS']
  l = iv['emaL']
  if emaS.crossed(l):
    if s > l:
      await self.openLongPositionMarket(
        mtsCreate=update['mts'], price=update['price'], amount=0.1)
    else:
      await self.openShortPositionMarket(
        mtsCreate=update['mts'], price=update['price'], amount=0.1)

```

## Managing positions

The hfstrategy class exposes a bunch of asynchronous methods to help open/close/update any positions:

- `open_long_position_market(*args, **kwargs)`
- `open_long_position_limit(*args, **kwargs)`
- `open_long_position(*args, **kwargs)`
- `open_short_position_market(*args, **kwargs)`
- `open_short_position_limit(*args, **kwargs)`
- `open_short_position(*args, **kwargs)`
- `open_position(*args, **kwargs)`
- `update_long_position_market(*args, **kwargs)`
- `update_long_position_limit(*args, **kwargs)`
- `update_long_position(*args, **kwargs)`
- `update_short_position_market(*args, **kwargs)`
- `update_short_position_limit(*args, **kwargs)`
- `update_short_position(*args, **kwargs)`
- `update_position(*args, **kwargs)`
- `close_position_market(*args, **kwargs)`
- `close_position_limit(*args, **kwargs)`
- `close_position(*args, **kwargs)`

The price and mtsCreate timestamp must both be provided to all update handlers, even those operating with MARKET orders, in order to record the price and timestamp during backtests. If these are not provided, backtests run via bfx-hf-backtest will fail.


## Examples

For more info on how to use this framework please navigate to `/examples`.
