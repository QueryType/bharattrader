'''
Volume is where the whole story begins. So it is important to determine volume expansions.
On charts, one can look for volume expansions, when they breach daily/weekly averages by huge margins. (LimeVolume day)
This indicate institutional demand.
Expansion of volume and presense of demand at different life cycle stages of a stock can mean different things.
For example, a limevolume day observed in Stage 1 for the first time, may be the first signal of demand, but not good 
to initiate a long trade just yet, because instituion will absorb the supply gradually.
If the base is instead formed well, and we start to see limevolume with higher lows on price chart, it might indicate
begining of stage 2.
If a scrip is already in an established up trend, (Stage 2), then limevolume days on a sideways (resting) trend, indicates
renewed demand either by the same institution or a new player interested in the company. Maybe suitable for top-up.
'''

import yfinance as yf
import pandas as pd
import numpy as np
import math
import csv
import datetime

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks.csv", header=0, usecols=["Ticker"])
# Exchange ".BO" for BSE, ".NS" for Nifty
exchg = ".NS"

# Set start Date
start_date = '2022-07-25' # Should be a date that is start of the week date, so that daily and weekly data can match

# Set end Date
end_date = '2023-07-29'
# Folder location
output = 'output'

# Interval
data_interval_wkeely = '1wk'
data_interval_daily = '1d'

# Weekly volume average length
weekly_volume_length = 10
# Daily volume average length
daily_volume_length = 100

# Number of days to check for limevolume
lookback_length = 55 #3-months daily

# Read up sector/industry information from text data
stock_industry_map = pd.read_csv("stock_sector_industry_map.csv", header=0, usecols=["NSE Code","Industry","Market Cap", "Sector"])

# Crore
One_Cr = 10000000

def fetch_industry_mcap(nse_code):

    industry = ''
    mcap = ''
    sector = ''

    try:
        # We try to get from local file first
        sector = stock_industry_map[stock_industry_map['NSE Code'] == nse_code]['Sector'].iloc[0]
        industry = stock_industry_map[stock_industry_map['NSE Code'] == nse_code]['Industry'].iloc[0]
        mcap =  stock_industry_map[stock_industry_map['NSE Code'] == nse_code]['Market Cap'].iloc[0]
    except Exception as err:
        pass

    if industry == '' or mcap == '':
        try:
                # Try yf
                ticker = yf.Ticker(nse_code+".NS")
                if ticker.info:
                    if industry == '':
                        industry = ticker.info['industry']
                    if mcap == '':
                        mcap = round(ticker.info['marketCap'] / One_Cr, 0)
                    if sector == '':
                        sector = ticker.info['sector']
        except Exception as err:
            pass

    return [sector, industry, mcap]

def main():
    print("Started... " + start_date + " - " + end_date)

    # Create the DataFrame
    df = pd.DataFrame(columns=['stock', 'mcap', 'blueVolCount', 'limeVolToday', 'limeVolCount', 'latestLimeVolDate',  'earliestLimeVolDate', 'tealVolCount', 'latestTealVolDate', \
                               'earliestTealVolDate', 'priceChng', 'sector' , 'industry'])
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            print(f'Analyzing {stock}...')
            # Get the stock data
            stk_ticker = yf.Ticker(stock+exchg)
            # Get the stock data from yfinance, dont adjust OHLC
            stock_data_daily = stk_ticker.history(start=start_date, end=end_date,interval=data_interval_daily,auto_adjust=False, prepost=False)
            # Drop those with NaN
            stock_data_daily = stock_data_daily.dropna()

            stock_data_weekly = stk_ticker.history(start=start_date, end=end_date,interval=data_interval_wkeely,auto_adjust=False, prepost=False)
            # Drop those with NaN
            stock_data_weekly = stock_data_weekly.dropna()

            #10wk avg volume
            weekly_vol_avg_col = f'Weekly_Volume_Avg{weekly_volume_length}'
            stock_data_weekly[weekly_vol_avg_col] = stock_data_weekly['Volume'].rolling(window=weekly_volume_length, min_periods=1).mean().fillna(0)

            #100d avg volule
            daily_vol_avg_col = f'Daily_Volume_Avg{daily_volume_length}'
            stock_data_daily[daily_vol_avg_col] = stock_data_daily['Volume'].rolling(window=daily_volume_length, min_periods=1).mean().fillna(0)

            # Create a new column in the daily data to store the corresponding weekly volume
            stock_data_daily[weekly_vol_avg_col] = 0

            # Loop through each row in the daily data
            mismatch_ctr = 0
            never_matched = True
            for i, row in stock_data_daily.iterrows():
                # Extract the date from the current row
                date = row.name.date()
                
                # Look up the corresponding row in the weekly data
                weekly_row = stock_data_weekly.loc[stock_data_weekly.index.date == date]
                
                # If there is no corresponding weekly data for the current date, propagate the last known weekly volume forward
                if len(weekly_row) == 0:
                    if never_matched and mismatch_ctr < 7:
                        mismatch_ctr = mismatch_ctr + 1
                        continue # Try to match up data for next week
                    stock_data_daily.at[i, weekly_vol_avg_col] = stock_data_daily[weekly_vol_avg_col].shift(1)[i]         
                # If there is corresponding weekly data for the current date, fetch the volume and set it in the daily data
                else:
                    never_matched = False
                    weekly_avg_volume = weekly_row[weekly_vol_avg_col].iloc[0]
                    stock_data_daily.at[i, weekly_vol_avg_col] = weekly_avg_volume
          
            isTodayLimeVolume = False
            cntLimeCount = 0
            cntTealCount = 0
            pctChange = 0
            earliestLimeVolDate = ''
            latestLimeVolDate = ''
            earliestTealVolDate = ''
            latestTealVolDate = ''
            # reverse
            stock_data_daily = stock_data_daily.iloc[::-1]

            if len(stock_data_daily) > lookback_length:
                for i in range(0, lookback_length):
                    if stock_data_daily['Close'][i] > stock_data_daily['Close'][i+1]: # Up Day
                        weekly_avg_to_compare = stock_data_daily[weekly_vol_avg_col][i]
                        for j in range(i+1, i+7): # Find the previous week volume average, by checking previous unmatched value
                            _weekly_avg = stock_data_daily[weekly_vol_avg_col][j]
                            if _weekly_avg != weekly_avg_to_compare:
                                weekly_avg_to_compare = _weekly_avg
                                break
                        if stock_data_daily['Volume'][i] > weekly_avg_to_compare: # Now compare if this day's volume is greater than weekly average volume
                            cntLimeCount = cntLimeCount + 1
                            earliestLimeVolDate = stock_data_daily.index[i].strftime("%d-%b-%Y")
                            if cntLimeCount == 1:
                                latestLimeVolDate = stock_data_daily.index[i].strftime("%d-%b-%Y")
                                pctChange = round(((stock_data_daily['Close'][i] / stock_data_daily['Close'][i+1]) - 1 ) * 100, 2)
                            if i == 0:
                                isTodayLimeVolume = True
                        # Teal Volume
                        if stock_data_daily['Volume'][i] > stock_data_daily[daily_vol_avg_col][i]: # Now compare if this day's volume is greater than daily average volume
                            cntTealCount = cntTealCount + 1
                            earliestTealVolDate = stock_data_daily.index[i].strftime("%d-%b-%Y")
                            if cntTealCount == 1:
                                latestTealVolDate = stock_data_daily.index[i].strftime("%d-%b-%Y")
            
            # Fetch industy and mcap
            [sector, industry, marketCap] = fetch_industry_mcap(stock)

            blueVolCnt = cntLimeCount + cntTealCount
            row = {'stock': stock, 'blueVolCount': str(blueVolCnt), 'limeVolToday' : str(isTodayLimeVolume), 'limeVolCount': str(cntLimeCount), \
                   'latestLimeVolDate' : str(latestLimeVolDate), 'earliestLimeVolDate' : str(earliestLimeVolDate), \
                    'tealVolCount': str(cntTealCount), 'latestTealVolDate' : str(latestTealVolDate), 'earliestTealVolDate' : str(earliestTealVolDate), \
                    'mcap' : marketCap, 'priceChng': str(pctChange),  'sector' : sector, 'industry' : industry}
            # Append the new row to the DataFrame
            df.loc[len(df)] = row

        except Exception as e:
            print(f'Error: {stock} => {e}')
    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = f'{output}/limevolume_{timestamp}.csv'
    # Export the DataFrame to CSV
    df.to_csv(file_name, index=False)
    print('Done')

if __name__ == "__main__":
    main()
