import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

N = 100
XMAX = 5
WINMA = 20
ALPHA = 2

ALPHVANTAGE_API_KEY = ''

#def get_bollinger(data, winma=10, alpha=2):
#    """
#    returns pd series of low and high bollinger bands
#    """
#    ser = pd.Series(data)
#    ma = ser.rolling(winma).mean()
#    std = ser.rolling(winma).std()
#    lower = pd.Series(ma - alpha*std).fillna(method='bfill').values
#    upper = pd.Series(ma + alpha*std).fillna(method='bfill').values
#    return lower, upper
#
#def get_alerts(data, lower, upper):
#    """
#    returns np arrays of low and high bollinger band collisions
#    """
#    low = np.argwhere(data < lower)
#    high = np.argwhere(data > upper)
#    return low, high
#
#def get_moving_avg(data):
#    ser = pd.Series(data)
#    return ser.rolling(WINMA).mean()
#
#if __name__=='__main__':
#
#    X = np.linspace(0.0, XMAX, num=N)
#    data = np.sin(X) + np.random.random(N)
#    lower, upper = get_bollinger(data, winma=WINMA, alpha=ALPHA)
#    low, high = get_alerts(data, lower, upper)
#    for i in low:
#        plt.plot(X[i], data[i], 'ro')
#    for i in high:
#        plt.plot(X[i], data[i], 'ro')
#    
#    ma = get_moving_avg(data)
#    
#    plt.plot(X, lower)
#    plt.plot(X, data)
#    plt.plot(X, upper)
#    plt.plot(X, ma)
#    plt.show()
#    
#
#    
    
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt

ti = TechIndicators(key=ALPHVANTAGE_API_KEY, output_format='pandas')
ts = TimeSeries(key=ALPHVANTAGE_API_KEY, output_format='pandas')
  
def get_buy_alerts(stock, stock_rocr, lower_bband, rocr_range = 0.1):
    crossing = np.argwhere(stock < lower_bband)
    high_roc = np.argwhere(stock_rocr < 1-rocr_range)
    return crossing[np.in1d(crossing, high_roc)]

def get_data(symbol):
    stock_data, meta_data = ts.get_intraday(symbol=symbol,interval='15min', outputsize='full')
    stock_rocr, meta_data = ti.get_rocr(symbol=symbol, interval='15min', time_period=14)
    stock_bbands, meta_data = ti.get_bbands(symbol=symbol, interval='15min', time_period=14)
    return stock_data, stock_rocr, stock_bbands


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
#stock_data, meta_data = ts.get_intraday(symbol='SPY',interval='60min', outputsize='full')

#stock_bbands, meta_data = ti.get_bbands(symbol=symbol, interval='5min', time_period=7)
