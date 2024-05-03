"""
This script calculates the Combined Relative Strength Index (RSI) for a list of stocks. 
The Combined RSI is a technical indicator used in the analysis of financial markets. 
It is intended to chart the current and historical strength or weakness of a stock or market based on the closing 
prices of a recent trading period. The Combined RSI is calculated by combining the traditional RSI with the volume.
"""

import pricereader as pr
import pandas as pd
import numpy as np
import datetime

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"]) 

def calculate_combined_rsi(df, period=14):
    """
    Calculate the Combined Relative Strength Index (RSI) for a given DataFrame.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing the stock data.
    - period (int): Number of periods to consider for calculating the RSI. Default is 14.

    Returns:
    - combined_rsi (pandas.Series): Series containing the Combined RSI values.
    """
    # Calculate daily price change
    df['Price Change'] = df['Close'].diff()

    # Calculate volume ratio and volatility
    avg_volume = df['Volume'].rolling(window=period).mean()
    df['Volume Ratio'] = df['Volume'] / avg_volume
    volatility = df['Price Change'].rolling(window=period).std()

    # Combine volume and volatility adjustments
    df['Combined Gain'] = np.where(df['Price Change'] > 0, (df['Price Change'] * df['Volume Ratio']) / volatility, 0)
    df['Combined Loss'] = np.where(df['Price Change'] < 0, -(df['Price Change'] * df['Volume Ratio']) / volatility, 0)

    # Compute average combined gain and loss
    avg_combined_gain = df['Combined Gain'].rolling(window=period).mean()
    avg_combined_loss = df['Combined Loss'].rolling(window=period).mean()

    # Calculate Combined RS and RSI
    combined_rs = avg_combined_gain / avg_combined_loss
    combined_rsi = 100 - (100 / (1 + combined_rs))

    return combined_rsi


def main():
    """
    Main function that calculates the Combined RSI for a list of stocks and saves the results to a CSV file.
    """
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'my_rsi'])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the daily stock data
            stock_data = pr.get_price_data(stock, 'd')
            # Drop those with NaN
            stock_data = stock_data.dropna()

            # Calculate combined RSI
            stock_data['Combined_RSI'] = calculate_combined_rsi(stock_data)
            # print(stock_data.tail())
            last_row_idx = stock_data.index[-1]
            row = {'stock': stock, 'my_rsi': str(round(stock_data.loc[last_row_idx, 'Combined_RSI'], 2))}
            # Append the new row to the DataFrame
            result_df.loc[len(result_df)] = row

        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = 'my_rsi_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(output_path + "/" + file_name, index=False)       
    print(f'Saved file {file_name}')


if __name__ == "__main__":
    main()
   