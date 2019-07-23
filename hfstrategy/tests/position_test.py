"""
This script tests the calculation of the position. I.e if an order fills
or partially fills then the profit/loss, position.amount ect.. should update correctly
"""

import pytest
import asyncio

from ..strategy.position import Position
from ..models import Events
from ..utils.mock_order_manager import generate_fake_data
from .helpers import EventWatcher, create_mock_strategy

test_candle_1 = {
  'mts': 1533919680000,
  'open': 6373,
  'close': 6374.5,
  'high': 6375.9,
  'low': 6369.2,
  'volume': 38.58293517,
  'symbol': 'tBTCUSD',
  'tf': '1hr',
}

test_candle_2 = {
  'mts': 1533919620000,
  'open': 6408.8,
  'close': 6372.9,
  'high': 6408.9,
  'low': 6366,
  'volume': 327.53682997,
  'symbol': 'tBTCUSD',
  'tf': '1hr',
}

test_candle_3 = {
  'mts': 1533919560000,
  'open': 6420,
  'close': 6409.6,
  'high': 6420.1,
  'low': 6406,
  'volume': 42.38708092,
  'symbol': 'tBTCUSD',
  'tf': '1hr',
}

# Different websocket orders

# market
# [0,"oc",[1151374309,null,1545233252044,"tBTCUSD",1545233251229,
# 1545233251250,0,-1,"EXCHANGE MARKET",null,null,null,0,"EXECUTED @ 16571.0(-1.0)",
# null,null,16571,16571,0,0,null,null,null,0,0,null,null,null,"API>BFX",
# null,null,null]]

# part filled
# [0,"on",[1151374313,null,1545233699192,"tBTCUSD",1545233698372,1545233698404,0.91,
# 1,"EXCHANGE LIMIT",null,null,null,0,"PARTIALLY FILLED @ 16673.0(0.09)",null,null,
# 16680,16673,0,0,null,null,null,0,0,null,null,null,"API>BFX",null,null,null]]

# short part filled
# [0,"on",[1151374354,null,1545392433703,"tBTCUSD",1545392432327,1545392432352,-0.98,-1,
# "EXCHANGE LIMIT",null,null,null,0,"PARTIALLY FILLED @ 16700.0(-0.02)",null,null,16700,
# 16700,0,0,null,null,null,0,0,null,null,null,"API>BFX",null,null,null]]

# non filled
# [0,"on",[1151374315,null,1545233913648,"tBTCUSD",1545233912831,1545233912847,1.2,1.2,
# "EXCHANGE LIMIT",null,null,null,0,"ACTIVE",null,null,16680,0,0,0,null,null,null,0
# ,0,null,null,null,"API>BFX",null,null,null]]

# complete
# [0,"oc",[1151374313,null,1545233699192,"tBTCUSD",1545233698372,1545233983863,0,1,
# "EXCHANGE LIMIT",null,null,null,0,"EXECUTED @ 16680.0(0.91): was PARTIALLY FILLED @ 16673.0(0.09)",
# null,null,16680,16679.37,0,0,null,null,null,0,0,null,null,null,"API>BFX",null,null,null]]

# update but no complete
# [0,"ou",[1151374315,null,1545233913648,"tBTCUSD",1545233912831,1545233983863,0.01,1.2,
# "EXCHANGE LIMIT",null,null,null,0,"PARTIALLY FILLED @ 16680.0(1.19)",null,null,16680,16680,
# 0,0,null,null,null,0,0,null,null,null,"API>BFX",null,null,null]]

## before all

@pytest.fixture(scope='function', autouse=True)
async def strategy():
  # create a test strategy
  strategy = create_mock_strategy()
  # inject a fake candle to get latest price
  await strategy._process_new_candle(test_candle_1)
  return strategy

@pytest.mark.asyncio
async def test_new_market_order(strategy):
  # inject candle 2
  await strategy._process_new_candle(test_candle_2)
  expected_fee = test_candle_2['close'] * 0.002

  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  assert position.amount == 1
  assert position.is_open() == True
  assert position.total_fees == expected_fee

@pytest.mark.asyncio
async def test_new_limit_order(strategy):
  # inject candle 2
  await strategy._process_new_candle(test_candle_2)
  expected_fee = test_candle_2['close'] * 0.001

  # register event listener to order_closed
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    mtsCreate=0, amount=1, price=test_candle_2['close'])
  # continue after event has fired
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  assert position.amount == 1
  assert position.is_open() == True
  assert position.total_fees == expected_fee
  assert len(position.orders) == 1

@pytest.mark.asyncio
async def test_multiple_new_long_market_orders(strategy):
  # inject candle 2
  await strategy._process_new_candle(test_candle_2)
  expected_fee = ((test_candle_2['close'] * 0.002) +
                  (test_candle_3['close'] * 0.002))
  
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  # inject candle 3
  await strategy._process_new_candle(test_candle_3)
  o_new_2 = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.update_long_position_market(mtsCreate=1, amount=1)
  await o_new_2.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  assert position.amount == 2
  assert position.is_open() == True
  assert position.total_fees == expected_fee
  assert len(position.orders) == 2

@pytest.mark.asyncio
async def test_open_and_close_position(strategy):
  # inject candle 2
  await strategy._process_new_candle(test_candle_2)
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # inject candle 3
  await strategy._process_new_candle(test_candle_3)
  # check profit loss
  expected_fee = test_candle_2['close'] * 0.002
  expected_net_pl = test_candle_3['close'] - test_candle_2['close'] - expected_fee
  assert position.net_profit_loss == expected_net_pl

  o_new_2 = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.close_position_market(mtsCreate=1)
  await o_new_2.wait_until_complete()

  expected_fee = (test_candle_2['close']  * 0.002) + (test_candle_3['close'] * 0.002)
  # position.update_with_price(test_candle_3['close'])
  assert position.total_fees == expected_fee
  assert position.profit_loss == 0
  assert position.net_profit_loss == -expected_fee
  assert position.amount == 0
  assert position.is_open() == False

@pytest.mark.asyncio
async def test_target_market_exit(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  await strategy.set_position_target(6400)
  pos = strategy.get_position('tBTCUSD')
  # load candle that reaches target price
  await strategy._process_new_candle(test_candle_3)
  # check position has been closed
  await asyncio.sleep(0.01)
  assert pos.amount == 0
  assert pos.is_open() == False
  assert pos.amount == 0

@pytest.mark.asyncio
async def test_stop_market_exit(strategy):
  await strategy._process_new_candle(test_candle_3)
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  await strategy.set_position_stop(6380)
  pos = strategy.get_position('tBTCUSD')
  # load candle that reaches stop price
  await strategy._process_new_candle(test_candle_1)
  # check position has been closed
  await asyncio.sleep(0.01)
  assert pos.amount == 0
  assert pos.is_open() == False
  assert pos.amount == 0

@pytest.mark.asyncio
async def test_switch_between_exit_type(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()
  pos = strategy.get_position('tBTCUSD')
  # target and stop should be market
  assert pos.exit_order.target == None
  assert pos.exit_order.stop == None
  assert pos.exit_order.target_type == Position.ExitType.MARKET
  assert pos.exit_order.stop_type == Position.ExitType.MARKET

  await strategy.set_position_stop(1, exit_type=Position.ExitType.LIMIT)
  # stop should be limit
  assert pos.exit_order.stop == 1
  assert pos.exit_order.stop_type == Position.ExitType.LIMIT
  assert pos.exit_order.target == None
  assert pos.exit_order.target_type == Position.ExitType.MARKET

  await strategy.set_position_target(8000, exit_type=Position.ExitType.LIMIT)
  # target should be limit
  assert pos.exit_order.target == 8000
  assert pos.exit_order.target_type == Position.ExitType.LIMIT
  assert pos.exit_order.stop == 1
  assert pos.exit_order.stop_type == Position.ExitType.LIMIT

@pytest.mark.asyncio
async def test_dynamic_position_update_order_update(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=1000, mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # send fake order update via event emitter
  fake_order = generate_fake_data('tBTCUSD', 1500, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = 2.5
  fake_order.amount_orig = 3
  fake_order.amount_filled = fake_order.amount_orig - fake_order.amount

  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()

  # check if position has updated with the correct amount
  assert position.amount == 1.5

@pytest.mark.asyncio
async def test_dynamic_position_update_partial_fill(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=1000, mtsCreate=0, amount=10)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # send fake order update via event emitter
  # short 10 but only 2.5 filled
  fake_order = generate_fake_data('tBTCUSD', 1000, 0, 0, 'EXCHANGE LIMIT')
  fake_order.id = 1
  fake_order.amount = -7.5
  fake_order.amount_orig = -10
  fake_order.amount_filled = fake_order.amount_orig - fake_order.amount

  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()

  assert position.amount == 7.5
  assert position.is_open() == True
  # send fake order update via event emitter
  # confirm the rest of the short has been filled
  fake_order2 = generate_fake_data('tBTCUSD', 1000, 0, 1, 'EXCHANGE LIMIT')
  fake_order.id = 1
  fake_order.amount = 0
  fake_order.amount_orig = -10
  fake_order.amount_filled = fake_order.amount_orig - fake_order.amount

  o_closed = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_closed', fake_order2)
  await o_closed.wait_until_complete()

  assert position.amount == 0
  assert position.is_open() == False


@pytest.mark.asyncio
async def test_dynamic_position_update_order_closed(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=1000, mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # send fake order update via event emitter
  fake_order = generate_fake_data('tBTCUSD', 1500, 2, 22020, 'EXCHANGE LIMIT')
  fake_order.amount_filled = fake_order.amount_orig - fake_order.amount

  o_closed = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_closed', fake_order)
  await o_closed.wait_until_complete()

  # check if position has updated with the correct amount
  assert position.amount == 3
  expected_volume = 1000 + (1500 * 2)
  assert position.volume == expected_volume
  expected_fees = expected_volume * 0.001
  expected_pl = 1500 - 1000 - expected_fees
  # the position updates profit loss based on the price
  # of the most recent order (and market updates)
  assert position.total_fees == expected_fees
  assert round(position.net_profit_loss, 2) == round(expected_pl, 2)

@pytest.mark.asyncio
async def test_dynamic_position_update_order_new(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=1000, mtsCreate=0, amount=1)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # send fake order update via event emitter
  fake_order = generate_fake_data('tBTCUSD', 1500, 1.2, 20202, 'EXCHANGE LIMIT')
  fake_order.amount = 1.2
  fake_order.amount_orig = 1.2
  fake_order.amount_filled = fake_order.amount_orig - fake_order.amount

  o_new_2 = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_new', fake_order)
  await o_new_2.wait_until_complete()
  # check if position has updated with the correct amount
  assert position.amount == 1

@pytest.mark.asyncio
async def test_dynamic_profit_loss_calculation(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=test_candle_1['close'], mtsCreate=0, amount=3)
  await o_new.wait_until_complete()

  # check profit losss
  expect_pl = (test_candle_2['close'] - test_candle_1['close']) * 3
  await strategy._process_new_candle(test_candle_2)
  position = strategy.get_position('tBTCUSD')
  assert position.profit_loss == expect_pl
  # check profit loss
  new_expect_pl = (test_candle_3['close'] - test_candle_1['close']) * 3
  await strategy._process_new_candle(test_candle_3)
  assert position.profit_loss == new_expect_pl

@pytest.mark.asyncio
async def test_dynamic_profit_loss_calculation_new_order(strategy):
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=test_candle_1['close'], mtsCreate=0, amount=3)
  await o_new.wait_until_complete()

  position = strategy.get_position('tBTCUSD')
  # create short order
  await strategy._process_new_candle(test_candle_2)

  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.update_long_position_limit(
    price=test_candle_2['close'], mtsCreate=0, amount=-1.5)
  await o_update.wait_until_complete()

  # position update takes 1.5 profit
  profit_taken = (test_candle_2['close'] - test_candle_1['close']) * 1.5
  await strategy._process_new_candle(test_candle_3)
  expect_pl = ((test_candle_3['close'] - test_candle_1['close']) * 1.5
                + profit_taken)
  assert round(position.profit_loss, 2) == round(expect_pl, 2)
  # check with fees
  volume = ((test_candle_1['close'] * 3) + (test_candle_2['close'] * 1.5))
  expected_fees = volume * 0.001
  assert round(position.net_profit_loss, 2) == round(expect_pl - expected_fees, 2)

@pytest.mark.asyncio
async def test_dynamic_stop_target_update(strategy):
  # open initial order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(
    price=test_candle_1['close'], mtsCreate=0, amount=3)
  await o_new.wait_until_complete()

  await strategy.set_position_stop(100, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(10000, exit_type=Position.ExitType.LIMIT)
  position = strategy.get_position('tBTCUSD')
  assert position.exit_order.stop == 100
  assert position.exit_order.target == 10000
  assert position.exit_order.amount == -3

  ## create a another order
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.update_long_position_limit(
    price=test_candle_1['close'], mtsCreate=0, amount=3)
  await o_update.wait_until_complete()

  assert position.exit_order.stop == 100
  assert position.exit_order.target == 10000
  assert position.exit_order.amount == -6
  ## simulate partial order fill
  fake_order = generate_fake_data('tBTCUSD', 1000, 0, 0, 'EXCHANGE LIMIT')
  fake_order.id = 1
  fake_order.amount = -5
  fake_order.amount_orig = -10
  fake_order.amount_filled = -5

  o_update_2 = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update_2.wait_until_complete()
  assert position.exit_order.stop == 100
  assert position.exit_order.target == 10000
  assert position.exit_order.amount == -1

  ## similate partial order fully filled
  fake_order2 = generate_fake_data('tBTCUSD', 1000, 0, 20, 'EXCHANGE LIMIT')
  fake_order2.id = 1
  fake_order2.amount = 0
  fake_order2.amount_orig = -10
  fake_order2.amount_filled = -10

  o_closed = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_closed', fake_order2)
  await o_closed.wait_until_complete()

  assert position.exit_order.stop == 100
  assert position.exit_order.target == 10000
  assert position.exit_order.amount == 4
  ## close position
  await strategy.close_position_market(mtsCreate=1)
  assert position.exit_order.stop == None
  assert position.exit_order.target == None
  assert position.exit_order.amount == 0
