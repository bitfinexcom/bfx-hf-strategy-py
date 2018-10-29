import unittest
import sys

sys.path.append('../')
from HFStrategy import AccumulativeSwingIndex

candles = [
  {
    'open': 6373,
    'high': 6375.9,
    'low': 6369.2,
    'close': 6374.5,
  },
  {
    'open': 6408.8,
    'high': 6408.9,
    'low': 6366,
    'close': 6372.9,
  }
]

class ASITest(unittest.TestCase):
  def test_is_calculated_properly(self):
    asi = AccumulativeSwingIndex([6400])
    asi.add(candles[0])
    asi.add(candles[1])
    self.assertEqual(round(asi.v(), 13), -0.1190821779318)


if __name__ == '__main__':
    unittest.main()
