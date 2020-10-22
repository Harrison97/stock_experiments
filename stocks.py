import requests
import string
from bs4 import BeautifulSoup
import threading
import robin_stocks as r
import os
import json
import pandas as pd
import finviz
import numpy as np

AUTHORIZATION = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJleHAiOjE1ODgzNTYzNDUsInRva2VuIjoiMGVLYkZpUjNwZTdjUzlieGt5TURwbnI3dlVqZVVlIiwidXNlcl9pZCI6ImRkZmMyZDg5LTIzZTctNDM0Zi04ZjVjLTYyZjFmY2YyMDMyOCIsImRldmljZV9oYXNoIjoiMDlhODc5MzY4YTRlYjg3YTc5MGI0ZjU3YWMyMGYzODUiLCJzY29wZSI6ImludGVybmFsIiwidXNlcl9vcmlnaW4iOiJVUyIsIm9wdGlvbnMiOnRydWUsImxldmVsMl9hY2Nlc3MiOnRydWV9.kxNbJQQeDo-kbIns-u27vgHMgY4-FgIdMbITRZGSx3sBXlSvJYOHHIi2VaoI3wNRiPXaky--xRy6nJe2iT5hYuad09doPP3N0pBspmSJDFd0DOdN-bjSk7KBJ6bPPYMrjyiWULMlWYZvxXOH2weCz9L4P1ddPi5pXR-ynaoytxLYEX6MyW3WGP20vgvyV320rz2Al9U4PFyTW8tIDAwHkgPHeqFthQD9ZkR3q0S9MVqegOjijiqbjmPhlFn7ORSagoARY5OHO5sDNmAvEyz6ralHO2DTgq6LUlLu4kRZ3vxaFEX8TQWH9F1T8fDHBW5OTLtkVjz2mCrxtGnoCxha1w'
r.helper.SESSION.headers['Authorization'] = AUTHORIZATION
r.helper.LOGGED_IN = True

EMAIL = 'email'
PASSWORD = 'password'

URLS = [
  'https://www.advfn.com/nasdaq/nasdaq.asp?companies=',
  'https://www.advfn.com/nyse/newyorkstockexchange.asp?companies=',
  'https://www.advfn.com/amex/americanstockexchange.asp?companies='
]



def get_all_tickers_from_advfn():
  tickers = set()

  def scrape_url(url):
    r = requests.get(url)

    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.find_all('table')[4].find_all('tr', attrs={'class':'ts0'})
    rows += soup.find_all('table')[4].find_all('tr', attrs={'class':'ts1'})

    for row in rows:
      ticker = row.find_all('td')[1].text
      if ticker:
        tickers.add(ticker)

  threads = []
  for letter in list(string.ascii_uppercase):
    for url in URLS:
      threads.append(threading.Thread(target = scrape_url, args = (str(url + letter),)))
  for t in threads:
    print('start')
    t.start()
    print('start end')
  for t in threads:
    print('join')
    t.join()
    print('join end')
  return sorted(list(tickers))

def get_all_tickers_from_finviz():
  print('scanner start')
  screener = finviz.Screener()
  print('scanner end')
  tickers = []
  for stock in screener:
    tickers.append(stock['Ticker'])
  return tickers

def fetch_all_tickers():
  adv = get_all_tickers_from_advfn()
  fin = get_all_tickers_from_finviz()
  fin += adv
  ticks = set(fin)
  ticks = list(ticks)
  map(lambda x: x, ticks)
  ticks.sort()
  return ticks

def fetch_gap_up_10():
  screener = finviz.Screener(filters=['ta_gap_u10'])
  tickers = list(map(lambda x: x['Ticker'], screener))
  tickers = json.dumps(tickers)
  tickers = json.loads(tickers)
  return tickers


# Clear ~./tokens if not working
#auth = r.login(EMAIL, PASSWORD)
robin_tickers = []

def is_robin_stock(ticker):
  try:
    if r.get_latest_price(ticker) is not None:
      robin_tickers.append(ticker)
      print('ADDDED ' + ticker)
      return
    print('IDK ' + ticker)
  except:
    print('None for ' + ticker)

def get_robin_tickers(all_tickers):
  threads = []

  for ticker in all_tickers:
    threads.append(threading.Thread(target = is_robin_stock, args = (ticker,)))
    threads[-1].start()
    if len(threads) >= 10:
      for t in threads:
        t.join()
      threads = []

  return robin_tickers

def update_robin_stocks_json():
  """ Gets stocks from URLS and checks if robin stocks """
  all_tickers = get_all_tickers()
  r_ticks = get_robin_tickers(all_tickers)
  myfile = open('robin_tickers.json', 'w')
  myfile.seek(0)
  myfile.truncate()
  myfile.write(json.dumps(r_ticks))
  myfile.close()

def get_from_json(filename):
  myfile = open(filename, 'r')
  return json.load(myfile)

def get_fundamentals(tickers):
  fundamentals = []
  sets_of_100 = len(tickers) // 100

  for i in range(sets_of_100):
    print('Call #' + str(i + 1))
    fundamentals += r.get_fundamentals(tickers[i*100 : (i+1)*100])

  fundamentals += r.get_fundamentals(tickers[sets_of_100*100 : ])
  return fundamentals

def filter_by_fundamentals(df):
  df.drop(df[df['float'] > 10000000].index, inplace = True)
  df.drop(df[df['market_cap'] > 100000000].index, inplace = True)
  df.drop(df[df['volume'] < 1000000].index, inplace = True)
  if 'close' in df:
    df.drop(df[((df['high'] - df['low']) * 0.75) + df['low'] > df['close']].index, inplace = True)
  if 'gap_up' in df:
    df.drop(df[df['gap_up'] < 0.1].index, inplace = True)
  print(df)

def fill_na_floats(df):
  def get_na_float(row):
    my_float = finviz.get_stock(row['symbol'])['Shs Float'] if np.isnan(row['float']) else row['float']
    def str_to_float(f):
      powers = { 'K': 3, 'M': 6, 'B': 9 }
      try:
        return float(f)
      except:
        try:
          return float(f[:-1]) * (10**powers[f[-1]])
        except:
          return np.nan
    return str_to_float(my_float)
  df['float'] = df.apply(get_na_float, axis=1)

def add_current_close_price(df):
  df['close'] = df['symbol'].apply(lambda x: float(r.get_latest_price(x)[0]))

def add_gap_up(df):
  df['gap_up'] = df.apply(lambda row: row['open'] / float(r.get_historicals(row['symbol'], span='year')[-1]['close_price']) - 1, axis = 1)







robin_tickers = get_from_json('robin_tickers.json')
#all_fundamentals = get_from_json('robin_fundamentals.json')
#all_ticks = get_from_json('all_tickers.json')

def low_float_strategy(tickers):
  fundamentals = get_fundamentals(tickers)
  #fundamentals = get_from_json('robin_fundamentals.json')
  df = pd.DataFrame(fundamentals, dtype=float)[['symbol', 'open', 'high', 'low', 'volume', \
    'market_cap', 'float', 'high_52_weeks']]
  print('Filtering funds..')
  filter_by_fundamentals(df)

  add_gap_up(df)
  print('Filtering gap_up..')
  filter_by_fundamentals(df)
  print(len(df))

  add_current_close_price(df)
  print('Filtering current close..')
  filter_by_fundamentals(df)

  fill_na_floats(df)
  print('Filtering floats..')
  filter_by_fundamentals(df)
  return df

