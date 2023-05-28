
'''
This code, also searches for new monthly highs, but not just ATH
This it does by boxing a lookback limit and a minimum duration where the new high should be
with respect to the historical high.
'''
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

# Set the maximum number of months to lookback
LOOKBACK_LIIMIT = 15 * 12 # Years in months

# Set minimum numbber of months that this BO should be after
MIN_BO_LENGTH = 50 #5 * 12 # Years in months

# Initialize a list to store the results
results = []

# Crore
One_Cr = 10000000

# Columnns in the report
report_columns = ["Stock", "mcap", "High Close", "High Close Date", "Current Close", "#MonthsBO", "Diff", "sector" , "industry"]

def write_dataframe_to_file(df, name):
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Create the filename
    filename = f'{name}_{timestamp}.csv'
    # Save the DataFrame as a CSV file with specific column names as the header
    df.to_csv(f'{output_path}/{filename}',index=False)



def main():
    print("Started...")
    # create an empty dataframe to store the results
    results_df = pd.DataFrame(columns=report_columns)
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
            
            if (len(data) < MIN_BO_LENGTH + 1):
                print(f'Skipping. Not enough data for {stock}, only {len(data)} available, minimum required {MIN_BO_LENGTH+1}')
                continue

            # Reverse the data frame to start from current candle
            stk_df = data.iloc[::-1]
            max_loopback = LOOKBACK_LIIMIT
            if (len(stk_df) < LOOKBACK_LIIMIT): # Limit lookback if not available data for so long
                max_loopback = len(stk_df)
            
            stk_df_max_lookback = stk_df.head(max_loopback)
            current_close = stk_df_max_lookback['Close'][0]
            for i in range(1, len(stk_df_max_lookback)):
                this_close = stk_df_max_lookback['Close'][i]
                if this_close > current_close:
                    if i >= MIN_BO_LENGTH: 
                        highest_close_date = stk_df_max_lookback.index[i].strftime('%Y-%m-%d')
                        diff = round((this_close - current_close)/current_close * 100, 2)
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
                        new_row = pd.DataFrame({"Stock": stock, "mcap": marketCap, "High Close": round(this_close, 2), "High Close Date": highest_close_date, \
                                        "Current Close": round(current_close, 2), "#MonthsBO": i, "Diff": diff, "sector": sector, "industry": industry}, index=[0])
                        results_df = pd.concat([results_df, new_row])
                        break
                    else:
                        break # A newer high exist before MIN_BO_LENGTH
        except Exception as e:
            print(f'Error for ticker: {stock} ==> {e}')

    # print(results_df)
    write_dataframe_to_file(results_df, "newHighMonthly_BO_")
    print("Done")

if __name__ == "__main__":
    main()
