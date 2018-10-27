from HFStrategy.indicators.indicator import Indicator

class CMF(Indicator):
  def __init__(self, args = []):
    [ period ] = args

    self._p = period
    self._bufferVol = []
    self._bufferMFV = []

    super().__init__({
      'args': args,
      'id': 'cmf',
      'name': 'CMF(%f)' % period,
      'seedPeriod': period,
      'dataType': 'candle',
      'dataKey': '*'
    })

  def reset(self):
    super().reset()
    self._bufferVol = []
    self._bufferMFV = []

  def moneyFlowVolume(candle):
    high = candle['high']
    low = candle['low']
    close = candle['close']
    vol = candle['vol']

    if high == low:
      mf = 0
    else:
      mf = ((close - low) - (high - close)) / (high - low)
    
    return mf * vol

  def update(self, candle):
    vol = candle['vol']
    mfv = CMF.moneyFlowVolume(candle)

    if len(self._bufferVol) == 0:
      self._bufferVol.append(vol)
    else:
      self._bufferVol[-1] = vol
    
    if len(self._bufferMFV) == 0:
      self._bufferMFV.append(vol)
    else:
      self._bufferMFV[-1] = mfv

    if len(self._bufferMFV) < self._p or len(self._bufferVol) < self._p:
      return
    
    super().update(sum(self._bufferMFV) / sum(self._bufferVol))
    return self.v()

  def add(self, candle):
    vol = candle['vol']
    mfv = CMF.moneyFlowVolume(candle)

    self._bufferVol.append(vol)
    self._bufferMFV.append(mfv)

    if len(self._bufferVol) > self._p:
      del self._bufferVol[0]
    
    if len(self._bufferMFV) > self._p:
      del self._bufferMFV[0]

    if len(self._bufferMFV) < self._p or len(self._bufferVol) < self._p:
      return
    
    super().add(sum(self._bufferMFV) / sum(self._bufferVol))
    return self.v()
