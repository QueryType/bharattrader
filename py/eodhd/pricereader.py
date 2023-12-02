import pandas as pd
base_path = 'price_data'

def get_price_data(stockname, period):
    """
    Fetches stock price data from CSV files for the given stock name and period.
    Sets the 'Date' column as a DatetimeIndex.
    
    :param stockname: Name of the stock (str)
    :param period: List of periods for which to fetch data ['d', 'w', 'm']
    :return: Dictionary of DataFrames with keys as the period
    """

    df = pd.DataFrame()
    
    # Mapping of period to file suffix
    period_suffix = {'d': '_D.csv', 'w': '_W.csv', 'm': '_M.csv'}
    

    # Construct file path based on stock name and period
    file_path = f"{base_path}/{stockname}{period_suffix[period]}"
    try:
        # Read the data from the file and set the 'Date' column as the index
        df = pd.read_csv(file_path, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
    except FileNotFoundError:
        print(f"No data available for {stockname} for period: {period}")
    
    return df

'''
This requires to pass df, after selection of the timeframe
'''
def get_price_daterange(df, start_date, end_date):
    # Ensure the dates are in the correct format
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter the dataframe
    filtered_df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    return filtered_df
