from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt

ALPHVANTAGE_API_KEY = ''

ti = TechIndicators(key=ALPHVANTAGE_API_KEY, output_format='pandas')
ts = TimeSeries(key=ALPHVANTAGE_API_KEY, output_format='pandas')
  
def get_buy_alerts(stock, stock_rocr, lower_bband, rocr_range = 0.1):
    crossing = np.argwhere(stock < lower_bband)
    high_roc = np.argwhere(stock_rocr < 1-rocr_range)
    return crossing[np.in1d(crossing, high_roc)]

def get_data(symbol):
    stock_data, meta_data = ts.get_intraday(symbol=symbol,interval='5min', outputsize='full')
    stock_rocr, meta_data = ti.get_rocr(symbol=symbol, interval='5min', time_period=7)
    stock_bbands, meta_data = ti.get_bbands(symbol=symbol, interval='5min', time_period=7)
    return stock_data, stock_rocr, stock_bbands

def get_heiken_ashi(df):
    df['HA_Close']=(df['Open']+ df['High']+ df['Low']+df['Close'])/4

    idx = df.index.name
    df.reset_index(inplace=True)

    for i in range(0, len(df)):
        if i == 0:
            df.set_value(i, 'HA_Open', ((df.get_value(i, 'Open') + df.get_value(i, 'Close')) / 2))
        else:
            df.set_value(i, 'HA_Open', ((df.get_value(i - 1, 'HA_Open') + df.get_value(i - 1, 'HA_Close')) / 2))

    if idx:
        df.set_index(idx, inplace=True)

    df['HA_High']=df[['HA_Open','HA_Close','High']].max(axis=1)
    df['HA_Low']=df[['HA_Open','HA_Close','Low']].min(axis=1)
    return df# -*- coding: utf-8 -*-

def plot_strategy(stock_data, stock_rocr, stock_bbands):
    
    stock_close = stock_data.iloc[:, 3]
    
    data = stock_bbands[:]
    data.insert(0, 'Close', stock_close)
    data.insert(1, 'ROCR', stock_rocr)
    
    alerts = get_buy_alerts(data['Close'].values, data['ROCR'].values, data['Real Lower Band'].values, rocr_range = 0.05)
    
    for a in alerts:
        plt.plot(data.index[a], data['Close'][a], 'ro')
    
    plt.plot(data['Close'], label = 'Close')
    plt.plot(data['Real Lower Band'], label = 'Low BB')
    plt.title('BBbands indicator for stock (15 min)')
    plt.legend()
    plt.show()

    #plt.plot(stock_rocr)

stock_data, stock_rocr, stock_bbands = get_data('GE')

plot_strategy(stock_data, stock_rocr, stock_bbands)
