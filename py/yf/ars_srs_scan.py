import yfinance as yf
import pandas as pd
import time
import datetime

def cleanUp_data(data):
    # Drop those with NaN
    data = data.dropna()
    return data

# set the file name of stocks
stock_filename = "stocks.csv"

# Set the time frame to max
time_frame = '2y'

# Set the bar time frame
data_interval = '1d'

# Specify the benchmark symbol
benchmark = "^NSEI"


# Specify the reference date
reference_date = "2022-06-03"

# Specify the number of rows to look back for the Static RS calculation
srs_length = 123

# Read the list of stocks from the CSV file
stocks = pd.read_csv(stock_filename, header=0, usecols=["Ticker"])

# Use yfinance to retrieve the benchmark data
benchmark_ticker = yf.Ticker(benchmark)
benchmark_data = benchmark_ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
benchmark_data = cleanUp_data(benchmark_data)

# Create an empty list to store the stock data
stock_data_list = []

# Iterate through the list of stocks
for stock in stocks["Ticker"]:
    try:
        ticker = yf.Ticker(stock+".NS")

        # Use yfinance to retrieve the stock data
        stock_data = ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
        stock_data = cleanUp_data(stock_data)

        # Calculate the Adaptive relative strength (ARS) using the formula you provided
        stock_data["Adaptive RS"] = (stock_data["Close"] / stock_data.loc[stock_data.index == reference_date, "Close"].values[0]) / (benchmark_data["Close"] / benchmark_data.loc[benchmark_data.index == reference_date, "Close"].values[0]) - 1

        # Calculate the Static relative strength (SRS) using the formula you provided and the specified number of rows to look back
        stock_close_123 = stock_data.at[stock_data.index[-123], 'Close']
        benchmark_close_123 = benchmark_data.at[benchmark_data.index[-123], 'Close']
        stock_data["Static RS"] = (stock_data["Close"] /stock_close_123) / (benchmark_data["Close"] / benchmark_close_123) - 1

        # Get the last row of the stock data
        last_row = stock_data.tail(1)

        # Extract the ARS and SRS values from the last row
        ars = round(last_row["Adaptive RS"].values[0], 2)
        srs = round(last_row["Static RS"].values[0], 2)

        # Create a dictionary with the stock name, ARS, and SRS values
        stock_data_dict = {"Stock": stock, "Adaptive RS": ars, "Static RS": srs}

        # Add the dictionary to the list
        stock_data_list.append(stock_data_dict)
    except Exception as e:
        print("Error " + stock)
        print(e)

# print(stock_data_list)

# Get the current timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Construct the file name using the timestamp
filename = "rs_stock_data_" + timestamp + ".csv"

# Convert the list of dictionaries to a dataframe
stock_data_df = pd.DataFrame(stock_data_list)

# Write the dataframe to the CSV file
stock_data_df.to_csv(filename, index=False)
