import pricereader as pr
import pandas as pd
import time

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Set the bar time frame
data_interval = 'm'

# Initialize a list to store the results
results = []

# Iterate through the list of stocks
for stock in stocks["Ticker"]:
    try:
        # Get the stock data
        data = pr.get_price_data(stock, data_interval)
        # Drop those with NaN
        data = data.dropna()
        # Drop last row, if 2nd last is already of the month
        if data.index[-1].month == data.index[-2].month:
            # Replace the values in the second-to-last row with the values in the last row
            data.loc[data.index[-2]] = data.loc[data.index[-1]]
            # Delete the last row
            data = data.drop(data.index[-1])

        # print(data)
        # data = data.iloc[:-1 , :] // If previous month ATH stocks are desired

        # Initialize the ATH to the first close price and the ATH date to the first date
        ath = data.at[data.index[0], 'High']
        ath_date = data.index[0]
        
        data_iter = data.iloc[:-1]

        # Loop through each row of the dataframe
        for index, row in  data_iter.iterrows():
            # Update the ATH and ATH date if the current close price is higher
            if row['High'] > ath:
                ath = row['High']
                ath_date = index

        # print(stock + " green line: " + str(green_line) + " green line date: " + str(green_line_date))
        last_close = data.at[data.index[-1], 'Close']
        
        if last_close > ath:
            # print(stock +" close: " + str(last_close) + " ath: " + str(ath) + " ath  date: " + str(ath_date))
            results.append(stock)

    except Exception as e:
        print("Error for ticker: " + stock)
        print(e)

# Print the results
print(results)
print("Done")