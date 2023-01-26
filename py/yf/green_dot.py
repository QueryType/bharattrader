
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Set start Date
start_date = '2020-01-01'

# Set end Date
end_date = '2023-01-21'

# Specify the benchmark symbol
benchmark = "^NSEI"

# Interval
data_interval_daily = '1d' # '1wk' or '1d'
data_interval_weekly = '1wk'

# Lookback for green dot
lookback = 5

def calculateReversionExpansion(stock_data):
    # Extract the close prices from the DataFrame
    src = stock_data["Close"]

    # Perform the EMA calculations
    l1, l2, l3, l4 = 20, 50, 100, 200 #EMA periods

    # Compute the exponential moving average with a lookback length of 20
    ema1 = src.ewm(span=l1).mean()
    ema2 = src.ewm(span=l2).mean()
    ema3 = src.ewm(span=l3).mean()
    ema4 = src.ewm(span=l4).mean()

    # Merge the series into one DataFrame
    merged_df = pd.concat([ema1, ema2, ema3, ema4], axis=1, keys=['EMA 20', 'EMA 50', 'EMA 100', 'EMA 200'])
    merged_df.fillna(0, inplace=True)
    # Find the lowest and the highest of this emas
    merged_df['lowest'] =  merged_df[(merged_df > 0)].min(axis=1)
    # Cheeky way to replace zero with a miniscule value to get rid of div by zero error
    merged_df['lowest'].replace(0, 1e-10, inplace=True)
    merged_df['highest'] = merged_df.max(axis=1)

    # Now, merge the close, otherwise lowest will consider Close values also
    merged_df = pd.concat([merged_df, src], axis=1)
    # Calculate delta between lowest and highest
    merged_df['delta'] = (merged_df['highest'] - merged_df['lowest']) / merged_df['lowest']
    # Calculate emadelta
    merged_df['emadelta'] = merged_df['delta'].ewm(span=7).mean()
    # Calculate delta between close and lowest ema
    merged_df['pricedelta'] = ( merged_df['Close'] - merged_df['lowest']) / merged_df['lowest']
    # Calculate ema of this pricedelta
    merged_df['emapricedelta'] = merged_df['pricedelta'].ewm(span=7).mean()
    # Determine if a crossover has happened between delta crossing over emadelta
    merged_df['crossover'] = np.where((merged_df['delta'] > merged_df['emadelta']) & (merged_df['delta'].shift(1) < merged_df['emadelta'].shift(1)), 1, 0)
    # Determine if a crossunder has happened between delta crossing over emadelta
    merged_df['crossunder'] = np.where((merged_df['delta'] < merged_df['emadelta']) & (merged_df['delta'].shift(1) > merged_df['emadelta'].shift(1)), 1, 0)

    return merged_df

def checkforGreenDot(rev_exp_data):
    # Check last lookback rows if there has been a crossover and no crossunder in the last
    rev_exp_data_21 = rev_exp_data.tail(lookback)

    crossover = False
    idx = ''
    delta = 0.0
    for index, row in rev_exp_data_21.iterrows():
        if (row['crossover'] == 1 and row['Close'] > row['highest']):
            crossover = True
            idx = index
            delta = row['delta']
        
        if (crossover and row['crossunder'] == 1):
            crossover = False
    return [crossover, idx, delta]

def main():
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'dailyXoverDate', 'dailyDelta', 'weeklyXoverDate', 'weeklyDelta'])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data
            # Get the stock data from yfinance, dont adjust OHLC
            stock_data_daily = yf.Ticker(stock+".NS").history(start=start_date, end=end_date,interval=data_interval_daily,auto_adjust=False, prepost=False)
            # Drop those with NaN
            stock_data_daily = stock_data_daily.dropna()

            # Calculate the entire series of reversion and expansion -- daily
            rev_exp_data = calculateReversionExpansion(stock_data_daily)
            result_daily = checkforGreenDot(rev_exp_data)

            # Weekly data
            stock_data_weekly = yf.Ticker(stock+".NS").history(start=start_date, end=end_date,interval=data_interval_weekly,auto_adjust=False, prepost=False)
            # Drop those with NaN
            stock_data_weekly = stock_data_weekly.dropna()

            # Calculate the entire series of reversion and expansion -- weekly
            rev_exp_data_weekly = calculateReversionExpansion(stock_data_weekly)
            result_weekly = checkforGreenDot(rev_exp_data_weekly)

            condition = result_daily[0] or result_weekly[0]
            if (condition):
                row = {'stock': stock, 'dailyXoverDate': str(result_daily[1]), 'dailyDelta': str(result_daily[2]), 'weeklyXoverDate': str(result_weekly[1]), 'weeklyDelta': str(result_weekly[2])}
                # Append the new row to the DataFrame
                result_df.loc[len(result_df)] = row

        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = 'green_dot_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(output_path + "/" + file_name, index=False)


if __name__ == "__main__":
    main()
   
