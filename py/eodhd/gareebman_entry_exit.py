'''
We are working here on identifying my favorite point of a company's business 
when there is a turn around. This analysis will try to capture from a price 
movement perspective.

We solely rely on technical indicators for shortlisting in this scan. Ideally
we should look for long bases, and then, we see if price is bottoming and
then picking up.

To keep it simple, we will track only RSI and Volstop.
For favourable entries into watchlist we will look for, (in weekly timeframe)
rsi > threshold (45) and volstop in uptrend. We will check with the previous
weeks to see if we had a "False", and now we have a "True". This means entry.
We dont expect to see too many flip-flops.
We are also defining an exit (from the watchlist), if volstop is in downtrend.
Again the same logic of comparing with previous week will apply.

We are also keeping a count of the current "entry" or "exit". So, let us say
a "trend" is "entry" and "duration" is 8, it means entry condition satisfied 
8 bars ago and continues to remain "entry" (without "exit" condition triggered)

So, do not confuse with the normal "entry" - "exit" terminology and method of 
trading. "entry" doesnt mean sell your house and take position. It means start
to track it.
'''

import pandas as pd
import numpy as np
import ta
from ta.volatility import AverageTrueRange
import datetime
import pricereader as pr

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Interval
data_interval_weekly = 'w'

# RSI interval
rsi_length = 14
# RSI weekly threshold
rsi_weekly_threshold = 45

def rsi(data):
    # Calculate the RSI
    data['rsi'] = ta.momentum.RSIIndicator(data['Close'], window=rsi_length).rsi()
    return data

def calculate_true_range(df):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    true_ranges = pd.concat([high_low, high_close, low_close], axis=1)
    return true_ranges.max(axis=1)

def calculate_atr(df, atrlen):
    df['TR'] = calculate_true_range(df)
    return df['TR'].rolling(window=atrlen, min_periods=1).mean()

def vol_stop(df, atrlen=10, atrfactor=2.0):
    df['ATR'] = calculate_atr(df, atrlen) * atrfactor
    max_val = df['Close'].iloc[0]
    min_val = df['Close'].iloc[0]
    uptrend = True
    stop = 0.0

    stops = []
    uptrends = []

    for index, row in df.iterrows():
        max_val = max(max_val, row['Close'])
        min_val = min(min_val, row['Close'])
        atrM = row['ATR']

        if uptrend:
            stop = max(stop, max_val - atrM)
        else:
            stop = min(stop, min_val + atrM)

        if row['Close'] - stop >= 0.0:
            uptrend = True
        else:
            uptrend = False

        if uptrend != uptrends[-1] if uptrends else True:
            max_val = row['Close']
            min_val = row['Close']
            stop = max_val - atrM if uptrend else min_val + atrM

        stops.append(stop)
        uptrends.append(uptrend)

    df['VolStop'] = stops
    df['Uptrend'] = uptrends
    return df

def main():
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'Close', 'VolStop10_2.0', 'RSI(14)', 'Entry', 'Exit', 'Trend', 'Duration'])
     # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data
            data = pr.get_price_data(stock, data_interval_weekly)
            # Drop those with NaN
            data = data.dropna()

            # Get RSI data
            data = rsi(data)

            # Get VolStop
            data = vol_stop(data)

            # Creating the 'entry' column
            data['entry'] = (data['rsi'] > rsi_weekly_threshold) & data['Uptrend']
            
            # Creating the 'exit' column
            data['exit'] = ~data['Uptrend']

            # Check entry toggle
            entry =  data['entry'].iloc[-1] and not data['entry'].iloc[-2]

            # Check exit toggle
            exit =  data['exit'].iloc[-1] and not data['exit'].iloc[-2]

            # Combine the 'entry' and 'exit' columns into a single column representing the current trend
            data['trend'] = np.where(data['entry'], 'entry', 'exit')

            # Identify where the trend changes
            trend_changes = data['trend'].ne(data['trend'].shift()).cumsum()

            # Group by these changes and count within each group
            data['trend_duration'] = data.groupby(trend_changes).cumcount() + 1

            row = {}

            if (entry or exit):
                row = {'stock': stock,'Close': str(round(data['Close'].iloc[-1], 2)),'VolStop10_2.0':str(round(data['VolStop'].iloc[-1])), \
                       'RSI(14)':str(round(data['rsi'].iloc[-1])), 'Trend': data['trend'].iloc[-1], \
                        'Duration': data['trend_duration'].iloc[-1], 'Entry':entry,'Exit':exit}
            else:
                row = {'stock': stock,'Close': str(round(data['Close'].iloc[-1], 2)),'VolStop10_2.0':str(round(data['VolStop'].iloc[-1])), \
                       'RSI(14)':str(round(data['rsi'].iloc[-1])), 'Trend': data['trend'].iloc[-1], \
                        'Duration': data['trend_duration'].iloc[-1], 'Entry':'-','Exit':'-'}
            
            # Append the new row to the DataFrame
            result_df.loc[len(result_df)] = row

        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = f'{output_path}/gareebman_report_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(file_name, index=False)
    print('Done')    

if __name__ == "__main__":
    main()
