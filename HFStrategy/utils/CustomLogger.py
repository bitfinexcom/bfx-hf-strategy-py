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
    'ERROR': RED
}

def formatter_message(message, use_color = True):
  if use_color:
      message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
  else:
      message = message.replace("$RESET", "").replace("$BOLD", "")
  return message

class Formatter(logging.Formatter):
  '''
  This logger adds some color to the output in order to help comprehension.
  It also highlights certain outputs that include key phrases i.e anything
  that has the word SHORT in it will be red. Anything with the word LONG in it
  will be green.
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
    FORMAT = "[$BOLD%(name)s$RESET] [%(levelname)s] %(message)s"
    COLOR_FORMAT = formatter_message(FORMAT, True)

    def __init__(self, name, logLevel='DEBUG'):
        logging.Logger.__init__(self, name, logLevel)                
        color_formatter = Formatter(self.COLOR_FORMAT)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)
        self.addHandler(console)
        return


