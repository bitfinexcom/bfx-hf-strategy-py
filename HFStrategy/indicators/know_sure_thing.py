from HFStrategy.indicators.indicator import Indicator
from HFStrategy.indicators.roc import ROC
from HFStrategy.indicators.sma import SMA

class KST(Indicator):
  def __init__(self, args = []):
    [ rocA, rocB, rocC, rocD, smaA, smaB, smaC, smaD, smaSignal ] = args

    self._rocA = ROC([rocA])
    self._rocB = ROC([rocB])
    self._rocC = ROC([rocC])
    self._rocD = ROC([rocD])

    self._smaA = SMA([smaA])
    self._smaB = SMA([smaB])
    self._smaC = SMA([smaC])
    self._smaD = SMA([smaD])

    self._smaSignal = SMA([smaSignal])

    super().__init__({
      'args': args,
      'id': 'kst',
      'name': 'KST(%f, %f, %f, %f, %f, %f, %f, %f, %f)' % (
        rocA, rocB, rocC, rocD, smaA, smaB, smaC, smaD, smaSignal
      ),
      'seedPeriod': max([
        rocA + smaA,
        rocB + smaB,
        rocC + smaC,
        rocD + smaD,
        smaSignal
      ])
    })
  
  def reset(self):
    super().reset()

    self._rocA.reset()
    self._rocB.reset()
    self._rocC.reset()
    self._rocD.reset()

    self._smaA.reset()
    self._smaB.reset()
    self._smaC.reset()
    self._smaD.reset()

    self._smaSignal.reset()


  def update(self, v):
    self._rocA.update(v)
    self._rocB.update(v)
    self._rocC.update(v)
    self._rocD.update(v)

    if self._rocA.ready():
      self._smaA.update(self._rocA.v())

    if self._rocB.ready():
      self._smaB.update(self._rocB.v())

    if self._rocC.ready():
      self._smaC.update(self._rocC.v())

    if self._rocD.ready():
      self._smaD.update(self._rocD.v())
    
    if not self._smaA.ready() or not self._smaB.ready() or not self._smaC.ready() or not self._smaD.ready():
      return

    kst = self._smaA.v() + (self._smaB.v() * 2) + (self._smaC.v() * 3) + (self._smaD.v() * 4)
    self._smaSignal.update(kst)

    super().update({
      'v': kst,
      'signal': self._smaSignal.v()
    })

    return self.v()

  def add(self, v):
    self._rocA.add(v)
    self._rocB.add(v)
    self._rocC.add(v)
    self._rocD.add(v)

    if self._rocA.ready():
      self._smaA.add(self._rocA.v())

    if self._rocB.ready():
      self._smaB.add(self._rocB.v())

    if self._rocC.ready():
      self._smaC.add(self._rocC.v())

    if self._rocD.ready():
      self._smaD.add(self._rocD.v())
    
    if not self._smaA.ready() or not self._smaB.ready() or not self._smaC.ready() or not self._smaD.ready():
      return

    kst = self._smaA.v() + (self._smaB.v() * 2) + (self._smaC.v() * 3) + (self._smaD.v() * 4)
    self._smaSignal.add(kst)

    super().add({
      'v': kst,
      'signal': self._smaSignal.v()
    })

    return self.v()
