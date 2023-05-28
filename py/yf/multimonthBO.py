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
MIN_MONTHS = 11

# Threshold to previous ATH
threshold = 1.0

# Initialize a list to store the results
results = []

# Crore
One_Cr = 10000000

# determine if highest close was minimum_low_length ago.
def highestClose(stock_data, min_months):

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
    df.to_csv(output_path + "/" + filename, index=False, columns=["Stock", "mcap", "Highest Close", "Highest Close Date", "Current Close", "Diff", "sector", "industry"])


def main():
    print("Started...")
    # create an empty dataframe to store the results
    results_df = pd.DataFrame(columns=["Stock", "mcap", "Highest Close", "Highest Close Date", "Current Close", "Diff", "sector" , "industry"])
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
            if (len(data) <= 2):
                print(f'Skipping {stock} since not enough data present ')
                continue

            min_months = MIN_MONTHS
            if (len(data) < (MIN_MONTHS + 1)):
                print(f'{stock} has only {len(data)} months, trimming condition')
                min_months = len(data)
                
            # Highest close prior to last month
            result_highestClose = highestClose(data.iloc[:-1], min_months) # Skip the current month
            highestClose_condition = result_highestClose[0]
            highestClose_value = result_highestClose[1]
            highestClose_date = result_highestClose[2]

            # Essential data
            sector = ''
            industry = ''
            marketCap = ''
            try:
                if ticker.info:
                    marketCap = round(ticker.info['marketCap'] / One_Cr, 0)
                    industry = ticker.info['industry']
                    sector = ticker.info['sector']
            except Exception as err:
                pass

            last_close = data["Close"].tail(1).values[0]
            if (highestClose_condition and last_close >= highestClose_value * threshold):
                diff = round(((last_close - highestClose_value) / highestClose_value) * 100, 2)
                new_row = pd.DataFrame({"Stock": stock, "mcap": marketCap, "Highest Close": round(highestClose_value, 2), "Highest Close Date": highestClose_date, \
                                        "Current Close": round(last_close, 2), "Diff": diff, "sector": sector, "industry": industry}, index=[0])
                results_df = pd.concat([results_df, new_row])

        except Exception as e:
            print(f'Error for ticker: {stock} ==> {e}')

    # print(results_df)
    write_dataframe_to_file(results_df, "MultiMonth_BO_")
    print("Done")

if __name__ == "__main__":
    main()
