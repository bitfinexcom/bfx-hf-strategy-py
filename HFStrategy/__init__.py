name = 'HFStrategy'

from HFStrategy.strategy import Strategy
from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.ema import EMA
from HFStrategy.indicators.rsi import RSI
from HFStrategy.indicators.roc import ROC
from HFStrategy.indicators.accumulation_distribution import AccumulationDistribution
from HFStrategy.indicators.acceleration import Acceleration
from HFStrategy.backtest import execOffline