"""
This scrip will fetch the current high price of a stock and calculate how many weeks it 
has been since the stock was at that price.
"""
import pricereader as pr
import pandas as pd
import time
import datetime

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks5.csv", header=0, usecols=["Ticker"])

# Set output folder path
output_path = "output"

# Function to get the number of bars to reach the high that t
# stock_data: DataFrame containing the stock data
#   Date,Open,High,Low,Close,Volume,Adj Close
#   2002-07-01,283.25,331.0,283.25,317.8,11803,317.8
#   2002-07-08,303.6,327.0,300.0,300.45,10390,300.45
#   2002-07-15,296.2,305.0,290.3,300.0,4744,300.0
#   2002-07-22,286.0,315.0,280.0,304.4,21643,304.4
def get_previous_index_prce_for_last_high(stock_data):
    """
    This function will first fetch the high price of the latest date (latest week)
    Then for each row before this, it will check if this high price was reached or crossed
    If it was, it will return the number of weeks it took to reach this price
    If it was not, it will return -1, indicating that the stock is ATH (All time high)
    stock_data: DataFrame containing the stock data, in acsending order of date
    """
    # Get the high price of the latest date
    latest_high = stock_data['High'].iloc[-1]

    # Iterate through the rows in reverse order
    for index in reversed(stock_data.index[:-1]):
        # Check if the high price was reached or crossed
        if stock_data.loc[index, 'High'] >= latest_high:
            # Return the index of the row where this price was reached
            return index, stock_data.loc[index, 'High']

    # Return last index if the high price was not reached or crossed
    return stock_data.index[-1], latest_high


def main():
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'High of latest week', 'Last such week high', \
                                      'Days passed', 'High of that week', 'diff%'])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the daily stock data
            stock_data = pr.get_price_data(stock, 'w')
            # Drop those with NaN
            stock_data = stock_data.dropna()

            # Get the index and high price of the week when the stock was at its high
            index, high = get_previous_index_prce_for_last_high(stock_data) 

            # Get the high price of the latest date
            latest_high = stock_data['High'].iloc[-1]
            # Current / last date
            latest_date = stock_data.index[-1]
            diff = round((latest_high - high) / high * 100,2)
            days_diff = (latest_date - index).days
            latest_high = round(latest_high,2)
            high = round(high,2)
            # Append the result to the DataFrame
            row = {'stock': stock, 'High of latest week': latest_high, 'Last such week high':index, \
                   'Days passed': f'{days_diff}', 'High of that week': high, 'diff%': f'{diff}%'}
            result_df.loc[len(result_df)] = row
            print(f"Processed: {stock}")
            
        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = 'weeks_to_high_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(output_path + "/" + file_name, index=False)       
    print(f'Saved file {file_name}')

if __name__ == "__main__":
    main()
   