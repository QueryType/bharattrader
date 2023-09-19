'''
Detect breakout of CRS from 55 day average
Daily timeframe
'''

import yfinance as yf
import pandas as pd

# Set the bar time frame
data_interval = '1d'

# Set the time frame to max
time_frame = '1y'

# Set CRS average length
average_length = 55

# Specify the benchmark symbol
benchmark = "^NSEI"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

def main():
    print('Started')

    # Use yfinance to retrieve the benchmark data
    benchmark_ticker = yf.Ticker(benchmark)
    benchmark_data = benchmark_ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
    benchmark_data = benchmark_data.dropna()

    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            ticker = yf.Ticker(stock+".NS")
            stock_history = ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
            stock_history = stock_history.dropna()

            # Create a new column in the stock dataframe for relative strength
            rs_column = 'Relative_Strength'
            stock_history[rs_column] = stock_history['Close'] / benchmark_data['Close']

            # Calculate the average_length-day moving average of the 'Relative_Strength' column
            crs_average_column = f'{average_length}_RS_MA'
            stock_history[crs_average_column] = stock_history[rs_column].rolling(window=average_length).mean()

            # Check if there is a cross over of crs
            isCrossOver = stock_history.iloc[-2][rs_column] <= stock_history.iloc[-2][crs_average_column] and \
                            stock_history.iloc[-1][rs_column] > stock_history.iloc[-1][crs_average_column]
            if (isCrossOver):
                print(stock)
            
        except Exception as e:
            print(f"Error: {stock} ==> {e}")

if __name__ == "__main__":
    main()
