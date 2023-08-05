'''
A comparitive analysis of the stock market based on sectors (or any grouping) from a significant date/event of past as reflected on the benchmark.
The idea then is to calculate the gains not only of the individual stocks but the entire group, with respect to that event.
Interesting analysis can be done, if the entire group is considered, where we can see that the leader stocks move much in advance of their peers and
start outperformance with respect to benchmark and the sectors. We can also see how the sector as a group is performing with respect to the benchmark.
'''
import pandas as pd
import os
from datetime import datetime, timedelta
import csv
import yfinance as yf


# Read up sector/industry information from text data
stock_industry_map = pd.read_csv("stock_sector_industry_map.csv", header=0, usecols=["NSE Code","Industry","Market Cap", "Sector"])

# Reference Date for comaprison, preferred <= 200
reference_date = '2022-12-01'

# Run date, must be greater than reference date
run_date = '2023-08-05'

# Minimum number of trading days to consider for index
min_trading_days = 200

# Maximum number of stocks to include in a sector group
max_stocks_per_sector = 10

# Limit on marketcap
min_cap = 500 # Crores

# Calculate gain percentages for different time periods
periods = [5, 21, 55, 123]

# Specify the benchmark symbol
benchmark = "^NSEI"

# Folder location
output = 'output'

def has_min_days_data(nse_code):
    # Calculate the start date as one year before the run_date
    start_date = (datetime.strptime(run_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')

    # Get the daily data for the specified period
    ticker = yf.Ticker(nse_code+'.NS')    
    stock_data = ticker.history(start=start_date, end=run_date, interval='1d',auto_adjust=False, prepost=False)
    
    # Check if the stock has at least min_trading_days days of trading data
    if len(stock_data) >= min_trading_days:
        return True
    else:
        return False

def prepare_custom_indexes(df):
    # Group the stocks by their sectors into a dictionary
    custom_indices = {}

    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        sector = row['Sector']
        stock_info = {
            'NSE Code': row['NSE Code'],
            'Industry': row['Industry'],
            'Market Cap': row['Market Cap']
        }
        nse_code = row['NSE Code']
        
        # Check if the stock has at least 200 days of trading data
        if has_min_days_data(nse_code):
            # Check if the sector already exists in the dictionary
            if sector in custom_indices:
                custom_indices[sector].append(stock_info)
            else:
                custom_indices[sector] = [stock_info]

    # Sort the stocks within each sector by decreasing market cap
    for sector in custom_indices:
        stocks_in_sector = custom_indices[sector]
        stocks_sorted_by_market_cap = sorted(stocks_in_sector, key=lambda x: x['Market Cap'], reverse=True)
        custom_indices[sector] = stocks_sorted_by_market_cap[:max_stocks_per_sector]

    # print(custom_indices)
    return custom_indices

def generate_watchlist_with_headers(custom_indices):
    watchlist_string_withheaders = ""
    watchlist_string = ""

    sector_index_mapper = {}

    for sector, stocks in custom_indices.items():
        # Calculate the number of stocks in the sector
        num_stocks = len(stocks)
        str = ''
        str_header = f'###{sector},'
        for stock in stocks:
            nse_code = 'NSE:' + stock['NSE Code']
            str += nse_code.replace('-','_').replace('&','_') + "+"
        
        str = str.rsplit('+', 1)[0].strip()
        str = f'( {str} )/{num_stocks}' + ','
        watchlist_string += str
        sector_index_mapper[sector.upper()] = str
        watchlist_string_withheaders = watchlist_string_withheaders + str_header.upper() + str

    # Write the watchlist to the txt file
    with open('custom_indices_without_headers.txt', 'w') as file:
        file.write(watchlist_string)

    # Write the watchlist to the txt file
    with open('custom_indices_with_headers.txt', 'w') as file:
        file.write(watchlist_string_withheaders)
    
    return sector_index_mapper

def calculate_gain_percentages(data_df, reference_date, run_date):
    # Filter the data from the reference date to the run date
    filtered_data = data_df.loc[reference_date:run_date]

    # Calculate the gain percentage for the original period
    start_price = filtered_data.iloc[0]['Close']
    end_price = filtered_data.iloc[-1]['Close']
    gain_percentage = ((end_price - start_price) / start_price) * 100

    gain_percentages = [gain_percentage]

    for period in periods:
        if len(filtered_data) < period:
            gain_percentages.append(None)  # Append None if there's insufficient data for the period
        else:
            start_price_period = filtered_data.iloc[-period]['Close']
            gain_percentage_period = ((end_price - start_price_period) / start_price_period) * 100
            gain_percentages.append(round(gain_percentage_period, 2))

    return gain_percentages

def calculate_sector_gains(custom_indices, reference_date, run_date):
    sector_gains = {}

    for sector, stocks in custom_indices.items():
        total_close_start = 0.0
        total_close_end = 0.0

        for stock in stocks:
            nse_code = stock['NSE Code']
            ticker = yf.Ticker(nse_code+'.NS')
            stock_data = ticker.history(start=reference_date, end=run_date, interval='1d',auto_adjust=False, prepost=False)
            if not stock_data.empty:
                # Get the closing price on the reference_date and run_date
                close_start = stock_data.iloc[0]['Close']
                close_end = stock_data.iloc[-1]['Close']
                total_close_start += close_start
                total_close_end += close_end

        # Calculate the gain percentage for the sector from reference_date to run_date
        sector_gain = round(((total_close_end - total_close_start) / total_close_start) * 100, 2)
        sector_gains[sector] = sector_gain

    return sector_gains

def main():
    print("Started...")
    # Prepare working dataset We only take NSE Codes and Market Cap > min_cap Crores
    df = stock_industry_map[(stock_industry_map['NSE Code'].notna()) & (stock_industry_map['Market Cap'] >= min_cap)]
    print(f'{len(df)} NSE stocks with mcap > {min_cap} Cr')
    # print(df.tail(10))
    # Prepare custom index
    ### df = df.tail(30) ### FOR TESTS ONLY####################
    print("Preparing custom indices...")
    custom_indices = prepare_custom_indexes(df)
    sector_index_mapper = generate_watchlist_with_headers(custom_indices)

    print("Calculating benchmark gain...")
    # Calculate gains of benchmark from reference date to run date
    benchmark_ticker = yf.Ticker(benchmark)
    benchmark_data = benchmark_ticker.history(start=reference_date, end=run_date, interval='1d',auto_adjust=False, prepost=False)
    benchmark_gain = calculate_gain_percentages(benchmark_data, reference_date, run_date)[0]

    print("Calculating sector gains...")
    sector_gains = calculate_sector_gains(custom_indices, reference_date, run_date)

    # Convert the date strings to datetime objects
    date1 = datetime.strptime(run_date, '%Y-%m-%d')
    date2 = datetime.strptime(reference_date, '%Y-%m-%d')

    # Calculate the difference in days between the two dates
    days_difference = (date1 - date2).days

    # Now we run for all stocks and create a big list and report
    result_df = pd.DataFrame(columns=['symbol', 'start','end','days', 'mcap', 'sector', 'industry', 'gain_stock_sector',  'gain_stock_benchmrk', 'gain_sector_benchmrk', \
                                      'gain_stock_refdate', 'gain_sector_refdate', 'gain_benchmrk_refdate', 'gain_stock_5d', 'gain_stock_21d', 'gain_stock_55d', 'gain_stock_123d',\
                                        'sector_index'])
    
    print("Calculating stock performances...")
    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        nse_code = row['NSE Code']
        ticker = yf.Ticker(nse_code+'.NS')
        try:
            stock_data = ticker.history(start=reference_date, end=run_date, interval='1d',auto_adjust=False, prepost=False)
            if (len(stock_data) <= 2):
                print(f'Skipping... {nse_code}')
                continue
            stock_gains = calculate_gain_percentages(stock_data,reference_date, run_date)
            stock_gain_from_refdate = stock_gains[0]
            sector = row['Sector']
            industry = row['Industry']
            mcap = row['Market Cap']
            gain_stock_sector = stock_gain_from_refdate - sector_gains[sector]
            gain_stock_benchmrk = stock_gain_from_refdate - benchmark_gain
            gain_sector_benchmrk = sector_gains[sector] - benchmark_gain
            gain_sector_refdate = sector_gains[sector]
            sector_index = sector_index_mapper[sector.upper()]
            
            row = {'symbol': nse_code, 'start': reference_date, 'end' : run_date, 'days' : days_difference, 'mcap': str(mcap), 'sector' : sector.upper(), 'industry' : industry.upper(), \
                'gain_stock_sector' : str(gain_stock_sector), 'gain_stock_benchmrk' : str(gain_stock_benchmrk), 'gain_sector_benchmrk' : str(gain_sector_benchmrk), \
                    'gain_stock_refdate' : str(stock_gain_from_refdate),  'gain_sector_refdate' : str(gain_sector_refdate), 'gain_benchmrk_refdate' : str(benchmark_gain), \
                        'gain_stock_5d' : str(stock_gains[1]), 'gain_stock_55d' : str(stock_gains[2]), 'gain_stock_21d' : str(stock_gains[3]), 'gain_stock_123d' : str(stock_gains[4]),\
                            'sector_index' : sector_index}
            
            # Append the new row to the DataFrame
            result_df.loc[len(result_df)] = row        
        except Exception as e:
            print(f'Error: {nse_code} => {e}')

    # Append current timestamp to the file name
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = f'{output}/stock_sector_benchmark_{reference_date}_{run_date}_{timestamp}.csv'
    # Export the DataFrame to CSV
    result_df.to_csv(file_name, index=False)
    # print(sector_index_mapper)
    print("Done")

if __name__ == "__main__":
    main()
