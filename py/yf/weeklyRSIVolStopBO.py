'''
BOs of nifty500 stocks, that gave a weekly breakout from RSI(14) > 60
Also, check if they are above the volstop(10,2.5)
Also, check if they are abover the 20-EMA
Prefer, stocks with relative ratio on an increasing trend on 5-6M average
All calculations on weekly timeframes

Generally, such stocks that take repitative support on a bullish RSI level,
with backing of sectoral tailwind or strong fundamentals give good long term moves
Exits can be planned on volstop break, or 20-EMA break or both with partial booking on
break of one
'''

import yfinance as yf
import pandas as pd
import ta
import datetime

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks500.csv", header=0, usecols=["Ticker"])

# Set start Date
start_date = '2020-02-01'

# Set end Date
end_date = '2023-02-26'

# Specify the benchmark symbol
benchmark = "^NSEI"

# Interval
data_interval_weekly = '1wk'

import yfinance as yf
import pandas as pd
import numpy as np

def rsi_crossover(data, rsi_level):
    current_rsi = data.iloc[-1]['RSI']
    previous_rsi = data.iloc[-2]['RSI']
    return previous_rsi <= 60.0 and current_rsi > 60.0

def volatility_stop(data, period, multiplier):
    high = data['High']
    low = data['Low']
    close = data['Close']

    atr = pd.Series((high - low).abs().rolling(period).mean(), name='ATR')
    direction = np.where(close.diff() > 0, 1, -1)
    vol_stop = close - direction * atr * multiplier

    data['volStop'] = vol_stop
    return data

def ratio_mean(data, benchmark_data, length):
    # Calculate the relative strength of the stock by dividing its weekly closing price by the weekly closing price of the Nifty 50 index
    relative_strength = data['Close'] / benchmark_data['Close']
    data[f'relativeRatio'] = relative_strength
    # print(relative_strength.tail(10))

    # Calculate the mean of the relative strength values for length
    data[f'ratio{length}W'] = relative_strength.rolling(window=length).mean()
    return data
    
    
def main():
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'Close', 'volStop10_2.5', 'ema20', 'RS-ratio', 'ratio-21W', 'RSI(14)'])

    # Benchmark data
    # Use yfinance to retrieve the benchmark data
    benchmark_ticker = yf.Ticker(benchmark)
    benchmark_data = benchmark_ticker.history(start=start_date, end=end_date, interval=data_interval_weekly,auto_adjust=False, prepost=False)
    benchmark_data = benchmark_data.dropna()

    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data from yfinance, dont adjust OHLC
            data = yf.Ticker(stock+".NS").history(start=start_date, end=end_date,interval=data_interval_weekly,auto_adjust=False, prepost=False)
            # Drop those with NaN
            data = data.dropna()

            # Calculate the RSI using a 14-day period
            data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
            # Check if a crossover from value lower than 60 has happend, we need to however look at RSI trend on a charting platform
            if (rsi_crossover(data, 60)):
                # Calculate volStop
                data = volatility_stop(data, 10, 2.5)
                # Calculate ema20W
                data['ema20'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
                # Calculate the relative ratio and average 21W
                data = ratio_mean(data, benchmark_data, 21)
                curr_data = data.iloc[-1]
                row = {'stock': stock, 'Close': curr_data['Close'], 'volStop10_2.5': str(round(curr_data['volStop'], 2)), 'ema20': str(round(curr_data['ema20'], 2)), \
                        'RS-ratio': str(round(curr_data['relativeRatio'], 2)), 'ratio-21W': str(round(curr_data['ratio21W'], 2)), 'RSI(14)': str(round(curr_data['RSI'], 2))}
                # Append the new row to the DataFrame
                result_df.loc[len(result_df)] = row

        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = 'weeklyRSIVolStopBO_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(file_name, index=False)
    print('Done')

if __name__ == "__main__":
    main()