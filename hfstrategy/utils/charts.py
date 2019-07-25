import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import datetime

def show_orders_chart(pricesDict, strategy):
  prices = [(pricesDict[l], l) for l in pricesDict.keys()]
  positions = [pos for pos in strategy.closedPositions]
  # sort the candles by timestamp
  prices.sort(key=lambda x: x[1])
  # Plot price data
  t = [ datetime.datetime.fromtimestamp(p[1]/1000) for p in prices ]
  s = [ p[0] for p in prices ]
  line, = plt.plot(t, s, zorder=2)
  line.set_color('lightblue')

  # Plot order data
  for pos in positions:
    orders = list(pos.orders.values())
    for index, order in enumerate(orders):
      if order.amount_filled > 0:
        marker = "^"
        color = "green"
      else:
        marker = "v"
        color = "red"
      # if order closes position
      if index == len(orders) -1:
        marker = "."
        color = "blue"
      plt.scatter(datetime.datetime.fromtimestamp(order.mts_create/1000), order.price_avg, s=50,
                  c=color, marker=marker, zorder=5)

  # Plot indicators
  for indicator in strategy.get_indicators().values():
    i_v = [indicator.prev(i-1) for i in range(len(prices), 0, -1)]
    plt.plot(t, i_v)

  plt.show()
