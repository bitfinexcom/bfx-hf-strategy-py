"""
Enum Events to help type all of the different events
that can be emitted by the Strategy class
"""

class Events:
  """ Contains a list of the available event types """
  ERROR = 'error'
  ON_READY = 'ready'
  ON_ENTER = 'on_enter'
  ON_UPDATE = 'on_update'
  ON_UPDATE_LONG = 'on_update_long'
  ON_UPDATE_SHORT = 'on_update_short'
  ON_ORDER_FILL = 'on_order_fill'
  ON_POSITION_UPDATE = 'on_position_update'
  ON_POSITION_CLOSE = 'on_position_close'
  ON_POSITION_STOP_REACHED = 'on_position_stop_reached'
  ON_POSITION_TARGET_REACHED = 'on_position_target_reached'
