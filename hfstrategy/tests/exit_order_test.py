"""
This script tests that the exit order executes a close position if the price is
met or executes a limit order update if the position size changes
"""
import pytest
import asyncio

from ..strategy.position import Position
from .helpers import EventWatcher, create_mock_strategy, generate_fake_candle
from ..models import Events
from ..utils.mock_order_manager import generate_fake_data

## before all

@pytest.fixture(scope='function', autouse=True)
async def strategy():
  # create a test strategy
  strt = create_mock_strategy()
  # inject a fake candle to get latest price
  await strt._process_new_candle(generate_fake_candle(mts=1533919680000))
  return strt

@pytest.mark.asyncio
async def test_exits_order_market_submits_on_target_reached(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_target(6700, exit_type=Position.ExitType.MARKET)
   # process new candle reaching that price
  new_candle = generate_fake_candle(mts=1533919620000, open=6750, close=6750, high=6750, low=6750)
  await strategy._process_new_candle(new_candle)
  # check mockwebsocket thatthe orderManager submitted the exit order
  called_params = strategy.orderManager.get_last_sent_item()
  assert called_params['data']['func'] == 'submit_trade'
  assert called_params['data']['args'][0] == 'tBTCUSD'
  assert called_params['data']['args'][1] == 6750
  assert called_params['data']['args'][2] == -1.0
  assert called_params['data']['args'][4] == 'EXCHANGE MARKET'

@pytest.mark.asyncio
async def test_exits_order_market_submits_on_stop_reached(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=1)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_stop(4000, exit_type=Position.ExitType.MARKET)
   # process new candle reaching that price
  new_candle = generate_fake_candle(mts=1533919620000, open=3500, close=3500, high=3500, low=3500)
  await strategy._process_new_candle(new_candle)
  # check mockwebsocket thatthe orderManager submitted the exit order
  called_params = strategy.orderManager.get_last_sent_item()
  assert called_params['data']['func'] == 'submit_trade'
  assert called_params['data']['args'][0] == 'tBTCUSD'
  assert called_params['data']['args'][1] == 3500
  assert called_params['data']['args'][2] == -1.0
  assert called_params['data']['args'][4] == 'EXCHANGE MARKET'

@pytest.mark.asyncio
async def test_exit_order_update_target_limit_on_position_update(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(mtsCreate=0, amount=3, price=6500)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_target(6700, exit_type=Position.ExitType.LIMIT)
  # generate fake partial fill
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = -2
  fake_order.amount_orig = -3
  fake_order.amount_filled = -1
  # push order through events
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()
  # check that it cancelled the old target order limit first.
  cancel_order = strategy.orderManager.get_sent_items()[-2:][0]
  assert cancel_order['data']['func'] == 'cancel_order_group'
  # check that it created a new target order limit
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert last['data']['args'][0] == 'tBTCUSD'
  assert last['data']['args'][1] == 6700
  assert last['data']['args'][2] == -2
  assert last['data']['args'][4] == 'EXCHANGE LIMIT'

@pytest.mark.asyncio
async def test_exit_order_update_stop_limit_on_position_update(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_limit(mtsCreate=0, amount=3, price=6500)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_stop(5000, exit_type=Position.ExitType.LIMIT)
  # generate fake partial fill
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = -2
  fake_order.amount_orig = -3
  fake_order.amount_filled = -1
  # push order through events
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()
  # check that it cancelled the old target order limit first.
  cancel_order = strategy.orderManager.get_sent_items()[-2:][0]
  assert cancel_order['data']['func'] == 'cancel_order_group'
  # check that it created a new target order limit
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert last['data']['args'][0] == 'tBTCUSD'
  assert last['data']['args'][1] == 5000
  assert last['data']['args'][2] == -2
  assert last['data']['args'][4] == 'EXCHANGE STOP LIMIT'

@pytest.mark.asyncio
async def test_exit_order_close_target_limit_on_position_close(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=3)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_target(7000, exit_type=Position.ExitType.LIMIT)
  # create fake closing order
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = 0
  fake_order.amount_orig = -3
  fake_order.amount_filled = -3
  # push order
  o_close= EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_closed', fake_order)
  await o_close.wait_until_complete()
  # check last request was to cancel order
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'cancel_order_group'

@pytest.mark.asyncio
async def test_exit_order_close_stop_limit_on_position_close(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=3)
  await o_new.wait_until_complete()
  # set position target
  await strategy.set_position_stop(7000, exit_type=Position.ExitType.LIMIT)
  # create fake closing order
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = 0
  fake_order.amount_orig = -3
  fake_order.amount_filled = -3
  # push order
  o_close= EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_closed', fake_order)
  await o_close.wait_until_complete()
  # check last request was to cancel order
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'cancel_order_group'

@pytest.mark.asyncio
async def test_exit_order_creates_oco_order_for_target_and_stop(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=3)
  await o_new.wait_until_complete()
  # set target and stop
  await strategy.set_position_stop(3000, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(7000, exit_type=Position.ExitType.LIMIT)
  # shouldve cancelled the first stop order
  cancel_order = strategy.orderManager.get_sent_items()[-2:][0]
  assert cancel_order['data']['func'] == 'cancel_order_group'
  # check last sent an OCO order
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert last['data']['args'][0] == 'tBTCUSD'
  assert last['data']['args'][1] == 7000
  assert last['data']['args'][2] == -3
  assert last['data']['args'][4] == 'EXCHANGE LIMIT'
  # check oco values
  assert last['data']['kwargs']['oco'] == True
  assert last['data']['kwargs']['oco_stop_price'] == 3000

@pytest.mark.asyncio
async def test_exit_order_updates_oco_order_for_target_and_stop_long(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=3)
  await o_new.wait_until_complete()
  # set target and stop
  await strategy.set_position_stop(3000, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(7000, exit_type=Position.ExitType.LIMIT)
  # trigger a partial fill
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = -2
  fake_order.amount_orig = -3
  fake_order.amount_filled = -1
  # push order through events
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()
  # check oco was updated
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert last['data']['args'][0] == 'tBTCUSD'
  assert last['data']['args'][1] == 7000
  assert last['data']['args'][2] == -2
  assert last['data']['args'][4] == 'EXCHANGE LIMIT'
  # check oco values
  assert last['data']['kwargs']['oco'] == True
  assert last['data']['kwargs']['oco_stop_price'] == 3000

@pytest.mark.asyncio
async def test_exit_order_updates_oco_order_for_target_and_stop_short(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=-3)
  await o_new.wait_until_complete()
  # set target and stop
  await strategy.set_position_stop(7000, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(3000, exit_type=Position.ExitType.LIMIT)
  # trigger a partial fill
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = 2
  fake_order.amount_orig = 3
  fake_order.amount_filled = 1
  # push order through events
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()
  # check oco was updated
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert last['data']['args'][0] == 'tBTCUSD'
  assert last['data']['args'][1] == 3000
  assert last['data']['args'][2] == 2
  assert last['data']['args'][4] == 'EXCHANGE LIMIT'
  # check oco values
  assert last['data']['kwargs']['oco'] == True
  assert last['data']['kwargs']['oco_stop_price'] == 7000

@pytest.mark.asyncio
async def test_exit_order_oco_orders_are_created_with_group_id(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=-3)
  await o_new.wait_until_complete()
  # set target and stop
  await strategy.set_position_stop(7000, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(3000, exit_type=Position.ExitType.LIMIT)
  # assert there is a group id
  last = strategy.orderManager.get_last_sent_item()
  assert last['data']['func'] == 'submit_trade'
  assert 'gid' in last['data']['kwargs'].keys()

@pytest.mark.asyncio
async def test_exit_order_oco_orders_are_cancelled_using_group_id(strategy):
  # create and order with market target exit order
  o_new = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  await strategy.open_long_position_market(mtsCreate=0, amount=-3)
  await o_new.wait_until_complete()
  # set target and stop
  await strategy.set_position_stop(7000, exit_type=Position.ExitType.LIMIT)
  await strategy.set_position_target(3000, exit_type=Position.ExitType.LIMIT)
  expected_gid = strategy.get_position('tBTCUSD').exit_order.order.gid
  # update position to force the oco order to be re-created
  fake_order = generate_fake_data('tBTCUSD', 6600, 0, 0, 'EXCHANGE LIMIT')
  fake_order.amount = 2
  fake_order.amount_orig = 3
  fake_order.amount_filled = 1
  # push order through events
  o_update = EventWatcher.watch(strategy.events, Events.ON_POSITION_UPDATE)
  strategy.mock_ws.ws._emit('order_update', fake_order)
  await o_update.wait_until_complete()
  # 2nd from last
  last = strategy.orderManager.get_sent_items()[-2:][0]
  assert last['data']['func'] == 'cancel_order_group'
  assert expected_gid == last['data']['args'][0]
