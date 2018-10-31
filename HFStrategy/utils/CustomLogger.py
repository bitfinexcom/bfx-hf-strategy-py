import logging

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

YELLOW = '\033[93m'
WHITE = '\33[37m'
BLUE = '\033[34m'
LIGHT_BLUE = '\033[94m'
RED = '\033[91m'
GREY = '\33[90m'

KEYWORD_COLORS = {
    'WARNING': YELLOW,
    'INFO': LIGHT_BLUE,
    'DEBUG': WHITE,
    'CRITICAL': YELLOW,
    'ERROR': RED,
    'TRADE': '\33[102m\33[30m'
}

def formatter_message(message, use_color = True):
  if use_color:
      message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
  else:
      message = message.replace("$RESET", "").replace("$BOLD", "")
  return message

class Formatter(logging.Formatter):
  '''
  This Formatter adds some color to the output in order to help comprehension.
  '''
  def __init__(self, msg, use_color = True):
    logging.Formatter.__init__(self, msg)
    self.use_color = use_color

  def format(self, record):
    levelname = record.levelname
    if self.use_color and levelname in KEYWORD_COLORS:
        levelname_color = KEYWORD_COLORS[levelname] + levelname + RESET_SEQ
        record.levelname = levelname_color
    record.name = GREY + record.name + RESET_SEQ
    return logging.Formatter.format(self, record)

class CustomLogger(logging.Logger):
    '''
    This logger adds extra logging functions such as logger.trade
    '''
    FORMAT = "[$BOLD%(name)s$RESET] [%(levelname)s] %(message)s"
    COLOR_FORMAT = formatter_message(FORMAT, True)
    TRADE = 40

    def __init__(self, name, logLevel='DEBUG'):
        logging.Logger.__init__(self, name, logLevel)                
        color_formatter = Formatter(self.COLOR_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)
        self.addHandler(console)
        logging.addLevelName(self.TRADE, "TRADE")
        return
    
    def trade(self, message, *args, **kws):
        if self.isEnabledFor(self.TRADE):
            message = message.replace('CLOSE', YELLOW+'CLOSE'+RESET_SEQ)
            message = message.replace('OPEN', LIGHT_BLUE+'OPEN'+RESET_SEQ)
            # Yes, logger takes its '*args' as 'args'.
            self._log(self.TRADE, message, args, **kws) 


