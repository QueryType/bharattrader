import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime, timedelta

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Set the time frame to max
time_frame = 'max'

# Set the bar time frame
data_interval = '1mo'

# Set the minimum number of months since the last ath was breached
min_months = 11

# Threshold to previous ATH
threshold = 0.95

# Initialize a list to store the results
results = []

# determine if lowest close was minimum_low_length ago.
def highestClose(stock_data):

    highest_close = stock_data["Close"][0]
    highest_close_date = stock_data.index[0]
    highest_close_idx = 0
    for i in range(1, len(stock_data)):
        if stock_data["Close"][i] > highest_close:
            highest_close = stock_data["Close"][i]
            highest_close_date = stock_data.index[i]
            highest_close_idx = i
    if len(stock_data) - highest_close_idx >= min_months:
       return [True, highest_close, highest_close_date]
    else:
       return [False, '', '']

def write_dataframe_to_file(df, name):
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Create the filename
    filename = f'{name}_{timestamp}.csv'
    # Save the DataFrame as a CSV file with specific column names as the header
    df.to_csv(output_path + "/" + filename, index=False, columns=["Stock", "Highest Close", "Highest Close Date", "Current Close", "Diff"])


def main():
    print("Started...")
    # create an empty dataframe to store the results
    results_df = pd.DataFrame(columns=["Stock", "Highest Close", "Highest Close Date", "Current Close", "Diff"])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data from yfinance, dont adjust OHLC
            ticker = yf.Ticker(stock+".NS")
            data = ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
            # Drop those with NaN
            data = data.dropna()
            # Drop last row, if 2nd last is already of the month
            if data.index[-1].month == data.index[-2].month:
                # Replace the values in the second-to-last row with the values in the last row
                data.loc[data.index[-2]] = data.loc[data.index[-1]]
                # Delete the last row
                data = data.drop(data.index[-1])

            # print(data)

            # Highest close prior to last month
            result_highestClose = highestClose(data.iloc[:-1]) # Skip the current month
            highestClose_condition = result_highestClose[0]
            highestClose_value = result_highestClose[1]
            highestClose_date = result_highestClose[2]

            last_close = data["Close"].tail(1).values[0]
            if (highestClose_condition and last_close >= highestClose_value * threshold):
                diff = round(((last_close - highestClose_value) / highestClose_value) * 100, 2)
                new_row = pd.DataFrame({"Stock": stock, "Highest Close": highestClose_value, "Highest Close Date": highestClose_date, "Current Close": last_close, "Diff": diff}, index=[0])
                results_df = pd.concat([results_df, new_row])

        except Exception as e:
            print("Error for ticker: " + stock)
            print(e)

    # print(results_df)
    write_dataframe_to_file(results_df, "MultiMonth_BO_")
    print("Done")

if __name__ == "__main__":
    main()
