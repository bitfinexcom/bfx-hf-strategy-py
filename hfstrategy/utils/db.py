from peewee import *
import math
import datetime
from bfxapi import Client

db = SqliteDatabase('bfx-hf-strategy.db')
db.connect()

class BaseModel(Model):
    class Meta:
        database = db

class Candle(BaseModel):
    symbol = CharField()
    tf = CharField()
    mts = IntegerField()
    open = FloatField()
    close = FloatField()
    high = FloatField()
    low = FloatField()
    volume = FloatField()

    def to_dict(self):
        return {
            'mts': self.mts,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume
        }

    def to_list(self):
        return [self.mts, self.open, self.close, self.high, self.low, self.volume]

db.create_tables([Candle])

def tf_to_minutes(tf):
    converter = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '3h': 180,
        '6h': 360,
        '12h': 720,
        '1D': 1440,
        '7D': 10080,
        '14D': 20160,
        '1M': 43200
    }
    return converter[tf]

def list_to_chunks(lst, n=999):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def mts_to_datetime(mts):
    #print(f"Converting {mts} to dt")
    return datetime.datetime.fromtimestamp(int(mts / 1000))

def datetime_to_mts(dt):
    return int(dt.timestamp() * 1000)

async def fetch_candles(from_date, end_date, symbol, tf):
    bfx = Client(logLevel='DEBUG')
    candles = []
    minutes = tf_to_minutes(tf)
    print(f'Fetching from {mts_to_datetime(from_date)} to {mts_to_datetime(end_date)} | {symbol} | {tf}')
    step = math.floor(10000 * minutes)
    while from_date < end_date:
        end_of_interval = mts_to_datetime(from_date) + datetime.timedelta(minutes=step)
        now = datetime.datetime.now()

        if end_of_interval > now:
            end_of_interval_ts = datetime_to_mts(now)
        else:
            end_of_interval_ts = datetime_to_mts(end_of_interval)
        response = None
        while not response:
            try:
                response = await bfx.rest.get_public_candles(symbol=symbol, start=from_date, end=end_of_interval_ts,
                                                             tf=tf, limit=10000)
                print(f'Fetched {len(response)} candles')
            except:
                print('Rate limit reached | Sleeping and trying again...')
        candles += response
        from_date = end_of_interval_ts
    store_candles(candles, symbol, tf)
    return candles

def store_candles(candles, symbol, tf):
    data_source = [{
        'symbol': symbol,
        'tf': tf,
        'mts': candle[0],
        'open': candle[1],
        'close': candle[2],
        'high': candle[3],
        'low': candle[4],
        'volume': candle[5]
    } for candle in candles]

    for chunk in list_to_chunks(data_source):
        with db.atomic():
            Candle.insert_many(chunk).execute()

    print(f"Database updated")

def find_fetched_candles_intervals(symbol, tf):
    minutes = tf_to_minutes(tf)
    candles = [candle for candle in
               Candle.select().where(symbol == symbol, tf == tf).order_by(
                   Candle.mts)]
    intervals = []
    interval = []
    previous_candle_dt = None
    for candle in candles:
        candle_dt = mts_to_datetime(candle.mts)
        if not previous_candle_dt:
            interval.append(candle)
        else:
            if (candle_dt - previous_candle_dt).total_seconds() / 60 == minutes:
                interval.append(candle)
            elif (candle_dt - previous_candle_dt).total_seconds() / 60 > minutes:
                intervals.append(interval)
                interval = [candle]
        previous_candle_dt = candle_dt
    intervals.append(interval)

    clean_intervals = []
    for interval in intervals:
        if len(interval) > 0:
            start = mts_to_datetime(interval[0].mts)
            end = mts_to_datetime(interval[-1].mts)
            clean_intervals.append({'start': start, 'end': end})

    return clean_intervals

def get_missing_candles_intervals(from_date, end_date, symbol, tf):
    minutes = tf_to_minutes(tf)
    fetched_intervals = find_fetched_candles_intervals(symbol, tf)
    missing_intervals = []

    for interval in fetched_intervals:
        if (interval['start'] - mts_to_datetime(from_date)).total_seconds() / 60 > minutes:
            missing_intervals.append({'start': from_date, 'end': datetime_to_mts(interval['start'])})
        from_date = datetime_to_mts(interval['end'])

        if end_date < from_date:
            break

    if from_date < end_date and (mts_to_datetime(end_date) - mts_to_datetime(from_date)).total_seconds() / 60 > minutes:
        missing_intervals.append({'start': from_date, 'end': end_date})

    return missing_intervals

async def get_candles(from_date, end_date, symbol, tf):
    print(f"Getting candles from {mts_to_datetime(from_date)} to {mts_to_datetime(end_date)}")
    missing_intervals = get_missing_candles_intervals(from_date, end_date, symbol, tf)
    for interval in missing_intervals:
        print(f"Data missing - Fetching -> Interval start: {mts_to_datetime(interval['start'])} | Interval end: {mts_to_datetime(interval['end'])}")
        await fetch_candles(interval['start'], interval['end'], symbol, tf)
    candles = [candle.to_list() for candle in
               Candle.select().where(from_date <= Candle.mts <= end_date, Candle.symbol == symbol, Candle.tf == tf).order_by(
                   Candle.mts)]
    return candles
