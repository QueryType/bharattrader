'''
A script to determine a trend reversal. This script uses Relative Strength (Stock Price / Benchmark ratio).
The script calculates the moving average of the relative strength values for a specified length (avg_length).
It determines the current trend of this average, based on the following logic:
- If the value of the average is rising means greater that max of any of last 3 (trend_length) weeks, the trend is considered uptrend. This is denoted by letter G.
- If the value of the average is falling means less than minimum of any of last 3 (trend_length)  weeks, the trend is considered downtrend. This is denoted by letter R.
- If the value of the average is neither rising nor falling, the trend is considered sideways. This is denoted by letter S.
Next, the script will create a string of these trends (G,R,S) for the last 26 (analysis_window) weeks, with the most recent week being the last character in the string.
It will save this string in the output column 'Trend' of the output CSV file.
'''

import pandas as pd
import pricereader as pr
import datetime

# Set output folder path
output_path = "output"

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Specify the benchmark symbol
benchmark = "NSEI"

# Interval
data_interval_weekly = 'w'

# Weekly CRS Average length
avg_length = 52 # Weeks
ratio_col = f'ratio{avg_length}W'

# Trend length
trend_length = 3 # Weeks

# Window of analysis
analysis_window = 26 # Weeks

def ratio_mean(data, benchmark_data, avg_length):
    # Calculate the relative strength of the stock by dividing its weekly closing price by the weekly closing price of the Nifty 50 index
    relative_strength = data['Close'] / benchmark_data['Close']
    data[f'relativeRatio'] = relative_strength
    # print(relative_strength.tail(10))

    # Calculate the mean of the relative strength values for length
    data[ratio_col] = relative_strength.rolling(window=avg_length).mean()
    return data


def rising(source, length):
    return source > source.shift(1).rolling(window=length).max()

def falling(source, length):
    return source < source.shift(1).rolling(window=length).min()

def sideways(source, length):
    # Sideways is true when not rising and not falling
    is_rising = rising(source, length)
    is_falling = falling(source, length)
    return ~(is_rising | is_falling)  # Not rising and not falling

def detect_reversal(sequence, initial_count, initial_type, transition_length, final_pattern):
    if sequence[:initial_count].count(initial_type) >= initial_count and sequence[-len(final_pattern):] == final_pattern:
        return True
    return False

def main():
    print("Started...")
    # Create the DataFrame
    result_df = pd.DataFrame(columns=['stock', 'Trend Sequence', 'Reversal Message'])

    # Benchmark data
    benchmark_data = pr.get_price_data(benchmark, data_interval_weekly)
    benchmark_data = benchmark_data.dropna()

    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data, sample as below. Latest data is at the end
            '''
                Date,Open,High,Low,Close,Volume,Adj Close
                2017-11-16,400.0,400.0,361.0,361.0,29447,361.0
                2017-11-20,343.0,343.0,279.45,279.45,5389,279.45
                2017-11-27,265.5,265.5,194.15,206.45,613081,206.45
                2017-12-04,196.0,227.55,181.0,227.55,615553,227.55
                2017-12-11,238.9,290.25,238.9,290.25,87251,290.25
            '''
            data = pr.get_price_data(stock, data_interval_weekly)
            # Drop those with NaN
            data = data.dropna()

            # Calculate the relative ratio and average avg_lengthW
            data = ratio_mean(data, benchmark_data, avg_length)

            # Apply the rising, falling, and sideways functions
            data['MA_rising'] = rising(data[ratio_col], trend_length)
            data['MA_falling'] = falling(data[ratio_col],trend_length)
            data['MA_sideways'] = sideways(data[ratio_col], trend_length)

            # Extract the last analysis_window rows
            analysis_data = data[['MA_rising', 'MA_falling', 'MA_sideways']].tail(analysis_window)
            
            # Create a sequence string from the last 13 rows
            sequence = ''.join(['G' if row['MA_rising'] else 'R' if row['MA_falling'] else 'S' for index, row in analysis_data.iterrows()])

            # Detect reversals, 14 weeks of current trend and 4 weeks of opposite trend, in between we do not care
            bullish_reversal = detect_reversal(sequence, 14, 'R', 4, 'GG')
            bearish_reversal = detect_reversal(sequence, 14, 'G', 4, 'RR')

            # Determine reversal message
            reversal_message = ""
            if bullish_reversal:
                reversal_message = "Bullish reversal detected."
            elif bearish_reversal:
                reversal_message = "Bearish reversal detected."

            # Save the results to the DataFrame
            row = {'stock': stock, 'Trend Sequence': sequence, 'Reversal Message': reversal_message}
            # Append the new row to the DataFrame
            result_df.loc[len(result_df)] = row
        except Exception as e:
            print("Error: " + stock)
            print(e)

    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = 'weeklyRS_Saucer_' + timestamp + '.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(output_path + "/" + file_name, index=False)
    print('Done')

if __name__ == "__main__":
    main()