import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Set start Date
start_date = '2021-01-24'

# Set end Date
end_date = '2023-01-25'

# Interval
data_interval = '1d'

# lowest close lookback dataset length
lowest_low_lookback = 250

# minimum days since last lowest close
minimum_low_length = 123

# mimnum days since last peak after lowest close
minimum_days_since_high = 55

# determine highest close in the dataset , Priorr to lowest low
def highestClose(stock_data):
    highest_close = stock_data["Close"][0]
    highest_close_date = stock_data.index[0]
    for i in range(1, len(stock_data)):
        if stock_data["Close"][i] >= highest_close:
            highest_close = stock_data["Close"][i]
            highest_close_date = stock_data.index[i]
   
    return [highest_close, highest_close_date]


# determine if lowest close was minimum_low_length ago.
def lowestLow(stock_data):

    lowest_close = stock_data["Close"][0]
    lowest_close_date = stock_data.index[0]
    lowest_close_idx = 0
    for i in range(1, len(stock_data)):
        if stock_data["Close"][i] <= lowest_close:
            lowest_close = stock_data["Close"][i]
            lowest_close_date = stock_data.index[i]
            lowest_close_idx = i
    if len(stock_data) - lowest_close_idx >= minimum_low_length:
       return [True, lowest_close, lowest_close_date]
    else:
       return [False, '', '']

def write_dataframe_to_file(df, name):
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Create the filename
    filename = f'{name}_{timestamp}.csv'
    # Save the DataFrame as a CSV file with specific column names as the header
    df.to_csv(output_path + "/" + filename, index=False, columns=["Stock", "Lowest Close", "Low Date", "High Prior", "High Prior Date", "23_6 Retrace", \
        "38_2 Retrace", "50_0 Retrace", "Curr/High %"])


def main():
    print("Started...")
    # create an empty dataframe to store the results
    results_df = pd.DataFrame(columns=["Stock", "Lowest Close", "Low Date", "High Prior", "High Prior Date", "23_6 Retrace", "38_2 Retrace", \
        "50_0 Retrace", "Curr/High %"])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            result_lowestLow = [False, '', '']
            below_23_6 = False
            below_38_2 = False
            below_50 = False

            # Get the stock data
            # Get the stock data from yfinance, dont adjust OHLC
            stock_data = yf.Ticker(stock+".NS").history(start=start_date, end=end_date,interval=data_interval,auto_adjust=False, prepost=False)
            # Drop those with NaN
            stock_data = stock_data.dropna()

            # Lowest low should be beyond last minimum_low_length months
            result_lowestLow = lowestLow(stock_data.tail(lowest_low_lookback))
            lowest_low_condition = result_lowestLow[0]
            lowest_low_close = result_lowestLow[1]
            lowest_low_date = result_lowestLow[2]

            # if lowest low condition is met, find out max in the data set Priorr to lowest low date
            if (lowest_low_condition):
               # Get dataset upto lowest_low_date
               before_low_data = stock_data.loc[stock_data.index < lowest_low_date]

               # Get highest Priorr to low
               result_highestClosePriorr = highestClose(before_low_data)
               highest_Priorr_close = result_highestClosePriorr[0]
               highest_Priorr_date = result_highestClosePriorr[1]

               # Calcualte difference between close and high
               diff = (highest_Priorr_close - lowest_low_close)
               # 23.6%, 38.2% and 50% retracement value
               level_23_6 = lowest_low_close + (diff * 0.236)
               level_38_2 = lowest_low_close + (diff * 0.382)
               level_50 = lowest_low_close + (diff * 0.50)

               # Get dataset after lowest_low_date
               after_low_data = stock_data.loc[stock_data.index > lowest_low_date]
                # Get highest after low
               result_highestCloseAfter = highestClose(after_low_data)
               highest_after_close = result_highestCloseAfter[0]
               highest_after_date = result_highestCloseAfter[1]

               # Check if the highest close, is within the retracement level
               if highest_after_close <= level_50:
                below_50 = True
                if highest_after_close <= level_38_2:
                    below_38_2 = True
                    if highest_after_close <= level_23_6:
                        below_23_6 = True
                # Calculate distance of current price with respect to the highest value in the retracement
                current_close  = stock_data["Close"].tail(1).values[-1]
                curr_diff = round(((current_close - highest_after_close) / (highest_after_close)) * 100, 2)
            
            if (below_50 or below_23_6 or below_38_2):
                new_row = pd.DataFrame({"Stock": stock, "Lowest Close": lowest_low_close, "Low Date": lowest_low_date, "High Prior": highest_Priorr_close, \
                    "High Prior Date": highest_Priorr_date, "23_6 Retrace": below_23_6, "38_2 Retrace": below_38_2, "50_0 Retrace": below_50, \
                        "Curr/High %": curr_diff}, index=[0])
                results_df = pd.concat([results_df, new_row])

        except Exception as e:
            print("Error: " + stock)
            print(e)

    # print(results_df)
    write_dataframe_to_file(results_df, "Supply_Exhaustion_6M_")
    print("Done")

if __name__ == "__main__":
    main()
