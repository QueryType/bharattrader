import yfinance as yf
import pandas as pd
import time

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])
# Exchange, ".BO, .NS"
exchange = ".NS"

# Set the time frame to max
time_frame = 'max'

# Set the bar time frame
data_interval = '1mo'

# Set the green line to the all-time high of the stock
green_line = 0.0

# Set the minimum number of months since the ath/green line was breached
min_months = 2

# Initialize a list to store the results
results = []

# Iterate through the list of stocks
for stock in stocks["Ticker"]:
    try:
        # Get the stock data from yfinance, dont adjust OHLC
        ticker = yf.Ticker(f'{stock}{exchange}')
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

        # Initialize the ATH to the first close price and the ATH date to the first date
        ath = data.at[data.index[0], 'High']
        ath_date = data.index[0]
        green_line = ath
        green_line_date = ath_date

        # Loop through each row of the dataframe
        for index, row in  data.iterrows():
            # Update the ATH and ATH date if the current close price is higher
            if row['High'] > ath:
                ath = row['High']
                ath_date = index
            # Update Greenline if condition of minimum months is met
            if  data.index.get_loc(index) - data.index.get_loc(ath_date)  >= min_months:
                    green_line = ath
                    green_line_date = ath_date

        # print(stock + " green line: " + str(green_line) + " green line date: " + str(green_line_date))
        last_close = data.at[data.index[-1], 'Close']
        second_last_close = data.at[data.index[-2], 'Close']
        if second_last_close < green_line and last_close > green_line:
            # print(stock +" close: " + str(last_close) + " second last close: " + str(second_last_close) + " green line: " + str(green_line) + " green line date: " + str(green_line_date))
            results.append(stock)

    except Exception as e:
        print("Error for ticker: " + stock)
        print(e)

# Print the results
print(results)
ex = 'NSE' if exchange == '.NS' else 'BSE'
for stk in results:
    print(f'{ex}:{stk},')
print("Done")
