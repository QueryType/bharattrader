'''
We tryto analyze trend reversal in stocks with major corrections
In order to reduce noise we select monthly candles and further use HA
5 consecutive red candles, followed by 2 green candles should be a clean trend reversal
These reversals must be validated with price action on lower timeframes.
Also, one just confirm demand, by checking limevolumes.
Relative strength across benchmark and sector must be checked.
'''
import yfinance as yf
import pandas as pd
import datetime

# Folder location
output = 'output'

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])

# Set the time frame to max
time_frame = 'max'

# Set the bar time frame
data_interval = '1mo'

# Crore
One_Cr = 10000000

def create_HA_Candles(df):

    # Create a new DataFrame to store the Heikin-Ashi values
    heikin_ashi_data = pd.DataFrame(index=df.index)

    if (len(df) < 2): # We need at least 2
        return heikin_ashi_data

    # Append the 'High' and 'Low' columns from the original data
    heikin_ashi_data[['High', 'Low']] = df[['High', 'Low']]
    # Calculate the Heikin-Ashi open, close, high, and low values
    heikin_ashi_data['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    # Handle the first row separately
    first_row_open = (df['Open'][0] + df['Close'][0]) / 2
    heikin_ashi_data['HA_Open'] = first_row_open
    # Calculate HA_Open correctly for subsequent rows
    for i in range(1, len(heikin_ashi_data)):
        heikin_ashi_data['HA_Open'][i] = (heikin_ashi_data['HA_Open'][i-1] + heikin_ashi_data['HA_Close'][i-1]) / 2

    heikin_ashi_data['HA_High'] = heikin_ashi_data[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    heikin_ashi_data['HA_Low'] = heikin_ashi_data[['HA_Open', 'HA_Close', 'Low']].min(axis=1)

    # Drop the 'High' and 'Low' columns
    heikin_ashi_data.drop(['High', 'Low'], axis=1, inplace=True)

    #print(heikin_ashi_data.tail(5))
    return heikin_ashi_data


def check_trend_change(df):
        # Check for the first 5 candles as red and the last 2 candles as green
        last_7_candles = df.tail(7)  # Select the last 7 candles

        red_candles_count = 0
        green_candles_count = 0
        valid_pattern = False

        for i in range(5):
            candle = last_7_candles.iloc[i]
            if candle['HA_Close'] < candle['HA_Open']:
                red_candles_count += 1
            else:
                break

        for i in range(5, 7):
            candle = last_7_candles.iloc[i]
            if candle['HA_Close'] > candle['HA_Open']:
                green_candles_count += 1
            else:
                break

        if red_candles_count == 5 and green_candles_count == 2:
            valid_pattern = True

        return valid_pattern


def main():
    print("Started... ")
    # Create the DataFrame
    df = pd.DataFrame(columns=['stock', 'mcap', 'vol1', 'vol2d', 'vol3d', 'sector' , 'industry'])

    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            # Get the stock data from yfinance, dont adjust OHLC
            stk_ticker = yf.Ticker(stock+".NS")
            data = stk_ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
            # Drop those with NaN
            data = data.dropna()
            if (len(data) < 2): # cannot do much analysis with 2 month candle
                continue
            # Drop last row, if 2nd last is already of the month
            if data.index[-1].month == data.index[-2].month:
                # Replace the values in the second-to-last row with the values in the last row
                data.loc[data.index[-2]] = data.loc[data.index[-1]]
                # Delete the last row
                data = data.drop(data.index[-1])
            
            heikin_ashi_data = create_HA_Candles(data)
            if (len(heikin_ashi_data) < 7) :
                print(f'Skipped for {stock} too less data')
            
            # Merge it to data
            heikin_ashi_data = heikin_ashi_data.join(data)

            # Check if there is a trend change
            if check_trend_change(heikin_ashi_data):
                sector = ''
                industry = ''
                marketCap = ''
                try:
                    if stk_ticker.info:
                        sector = stk_ticker.info['sector']
                        industry = stk_ticker.info['industry']
                        marketCap = round(stk_ticker.info['marketCap'] / One_Cr, 0)
                except Exception as err:
                    pass

                # Get volume data
                vols = data.tail(3)['Volume']
                vol1 = vols[0]
                vol2d = vols[1] - vol1
                vol3d = vols[2] - vols[1]

                # Append to row
                row = {'stock': stock, 'mcap' : marketCap, 'vol1' : vol1, 'vol2d' : vol2d,'vol3d' : vol3d, 'sector' : sector, 'industry' : industry}
                # Append the new row to the DataFrame
                df.loc[len(df)] = row
            
        except Exception as e:
            print(f'Error for ticker {stock} ==> {e}')
    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = f'{output}/ha_trendreversal_{timestamp}.csv'
    # Export the DataFrame to CSV
    df.to_csv(file_name, index=False)
    print('Done')


if __name__ == "__main__":
    main()
