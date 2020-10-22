import robin_stocks as r
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce
#S%matplotlib inline

EMAIL = 'email'
PASSWORD = 'password!'

auth = r.login(EMAIL, PASSWORD)


def get_historicals(symbol, span, bounds = 'regular'):
    """
    day: 5min inteval
    week: 10min interval
    month: 1hr interval
    3month: 1hr interval
    year: 1day interval
    5year: 1week interval
    """

    data = pd.DataFrame(r.stocks.get_historicals(symbol, span=span))
    data['open_price'] = data['open_price'].astype(float)
    data['close_price'] = data['close_price'].astype(float)
    data['high_price'] = data['high_price'].astype(float)
    data['low_price'] = data['low_price'].astype(float)
    data.index.span = span

    if bounds == 'regular':
        return data.drop(columns = ['interpolated', 'session'])
    else:
        return data

def find_roc(data, length = 14):
    M = data.diff(length)  
    N = data.shift(length)  
    roc = pd.Series(((M / N) * 100), name = 'ROC_by_' + data.index.span + '_length_' + str(length))   
    return roc

def find_bollinger(data, winma=10, alpha=2):
    """
    returns pd series of low and high bollinger bands
    """
    ser = pd.Series(data)
    ma = ser.rolling(winma).mean()
    std = ser.rolling(winma).std()
    lower = pd.Series(ma - alpha*std)#.fillna(method='bfill')
    upper = pd.Series(ma + alpha*std)#.fillna(method='bfill')
    lower.name = 'lower'
    upper.name = 'upper'
    return lower.to_frame().join(upper)

def find_rocr(data, length = 14):
    N = data.shift(length)
    rocr = pd.Series((data / N), name = 'ROCR_by_' + data.index.span + '_length_' + str(length))
    return rocr
 
def get_buy_alerts(stock, stock_rocr, lower_bband, upper_bband, rocr_range = 0.1):
    crossing = np.argwhere(stock < lower_bband)
    high_rocr = np.argwhere(stock_rocr < 1-rocr_range)
    call = crossing[reduce(np.in1d, (crossing, high_rocr))]

    crossing = np.argwhere(stock > upper_bband)
    high_rocr = np.argwhere(stock_rocr < 1-rocr_range)
    put = crossing[np.in1d(crossing, high_rocr)]
    
    return call, put
    
    

#optionData = r.find_options_for_list_of_stocks_by_expiration_date(['fb','aapl','tsla','nflx'],
#  expirationDate='2018-11-16',optionType='call')
def bb_rocr_options_strategy(symbol, chart_span = '3month', rocr_win = 14, rocr_range = 0.1, bb_win = 20, bb_alpha = 2):
    data = get_historicals(symbol, span=chart_span)
    rocr = find_rocr(data.close_price, rocr_win)
    roc = find_roc(data.close_price, rocr_win)
    bb = find_bollinger(data.close_price, winma=bb_win, alpha=bb_alpha)
    alerts  = get_buy_alerts(data.close_price.values, rocr.values, bb.lower.values, bb.upper.values, rocr_range = rocr_range)
    
    plt.title('{} - {} - Bollinger low & price'.format(symbol, chart_span))
    plt.plot(data.close_price, label = 'close_price', color = 'red')
    plt.plot(bb.lower, color = 'black', label = 'bb.lower')
    plt.plot(bb.upper, color = 'black')
    for a in alerts[0]:
        pass
        plt.plot(data.index[a], data['close_price'][a], 'ro', color = 'blue')
    for a in alerts[1]:
        pass
        plt.plot(data.index[a], data['close_price'][a], 'ro', color = 'purple')
    plt.legend()
    plt.show()
    
    plt.title('{} - {} - ROCR'.format(symbol, chart_span))
    plt.plot(rocr)
    plt.show()
#    plt.title('{} - {} - ROC'.format(symbol, chart_span))
#    plt.plot(roc)
#    plt.show()

#bb_rocr_options_strategy('SPY', rocr_win = 14)



def get_watchlist_symbols():
    return list(map(lambda x: r.get_symbol_by_url(x['instrument']), watchlist))

watchlist = r.get_watchlist_by_name('Default')
symbols = get_watchlist_symbols()

bb_rocr_options_strategy('SPY', rocr_win = 10, rocr_range = 0.1, bb_win = 24, bb_alpha = 2)


for symbol in symbols:
    bb_rocr_options_strategy(symbol, chart_span = '3month', rocr_win = 10, rocr_range = 0.1, bb_win = 24, bb_alpha = 2)
    bb_rocr_options_strategy(symbol, chart_span = 'week', rocr_win = 10, rocr_range = 0.1/6, bb_win = 24, bb_alpha = 2)
    bb_rocr_options_strategy(symbol, chart_span = 'day', rocr_win = 10, rocr_range = 0.1/6, bb_win = 24, bb_alpha = 2)
