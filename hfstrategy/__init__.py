"""
This module exposes the core honey frameworkd packages.
"""
from hfstrategy.Strategy.Strategy import Strategy
from hfstrategy.Strategy.PositionManager import PositionError
from hfstrategy.Strategy.Position import Position
from .utils.Executor import (backtestOffline, backtestWithDataServer,
                             backtestLive, executeLive)

NAME = 'hfstrategy'
