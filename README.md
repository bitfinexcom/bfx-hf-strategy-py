# bfx-hf-strategy-py

Install prettytable for nicely formatted backtest results:
```sh
pip3 install prettytable
```

Install bfx-hf-indicators-py:
```sh
git clone https://github.com/bitfinexcom/bfx-hf-indicators-py
cd bfx-hf-indicators-py
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

Run example ema_cross backtest:
```sh
# in bfx-strategy-hf-py
cd examples
python3 ema_cross.py  
```
