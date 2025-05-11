#!/usr/bin/env python3
"""
Stock Result Analysis Script for Screener Source Data

This script processes stock data from ss_result_file.csv, which contains stock information
from Screener. For each stock, it downloads historical price data from Yahoo Finance
and calculates various performance metrics relative to benchmark.

The script:
1. Reads stock information from a CSV file with 'companyId' format as 'NSE:SYMBOL' or 'BSE:SYMBOL'
2. Downloads historical price data for each stock using yfinance
3. Calculates performance metrics (stock change %, benchmark change %, Alpha, ARS)
4. Saves the enriched data to a new CSV file

Usage:
    python ss_result_parser.py
"""

# Standard library imports
import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# Constants
ARS_DATE = "2024-05-10"  # ARS (Adaptive Relative Strength) reference date
START_DATE = '2024-01-01'  # Beginning of analysis period
END_DATE = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')  # today + 1 day

RESULT_FILE = "ss_result_file.csv"
OUTPUT_FILE = "final_ss_result_parser.csv"


def main():
    """
    Main function to process stock data and calculate performance metrics.
    """
    print('Started... with yfinance version:', yf.__version__)
    
    # Use yfinance to retrieve the benchmark data
    benchmark_ticker = yf.Ticker("^NSEI")  # NIFTY 50 Index
    benchmark_data = benchmark_ticker.history(start=START_DATE, end=END_DATE, interval='1d', auto_adjust=False, prepost=False)
    benchmark_data = benchmark_data.dropna()

    # Read the result file
    result = pd.read_csv(RESULT_FILE)
    result = result.dropna(subset=['companyId'])  # Only drop rows with no companyId
    
    # Process each stock
    for index, row in result.iterrows():
        try:
            # Extract exchange and symbol from companyId
            company_id_parts = row['companyId'].split(':')
            exchange = company_id_parts[0]
            symbol = company_id_parts[1]
            
            print(f"Processing {row['Name']}...")
            
            # Set ticker format based on exchange
            if exchange == "NSE":
                stk_ticker = symbol + '.NS'
            elif exchange == "BSE":
                stk_ticker = symbol + '.BO'
            else:
                print(f"Unknown exchange for {row['companyId']}")
                continue
                
            stk_ticker = yf.Ticker(stk_ticker)
            stock_data = stk_ticker.history(start=START_DATE, end=END_DATE, interval='1d', auto_adjust=False, prepost=False)
            
            if stock_data.empty:
                print(f"No data available for {row['companyId']}")
                continue
                
            # Fetch Result Date, and then fetch the price on that date from stock_data.
            if pd.isna(row['Last Result Date']):
                print(f"No result date for {row['companyId']}")
                continue
                
            result_date = datetime.datetime.strptime(row['Last Result Date'], '%Y-%m-%d').strftime('%Y-%m-%d')
            result_price = 0.00
            
            # Get the last date in the stock data
            last_date = stock_data.index[-1].strftime('%Y-%m-%d')
            if last_date < result_date:
                print(f"Error: {row['companyId']} => Result Date {result_date} is greater than last date in stock data {last_date}")
                continue
            
            # If price not found on result date, try following dates
            while result_date <= last_date:
                try:
                    result_price = stock_data.loc[stock_data.index == result_date, "Close"].values[0]
                    break
                except:
                    result_date = (datetime.datetime.strptime(result_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    continue
            
            # Calculate and add stock performance metrics
            add_stock_metrics(result, index, stock_data, result_date, result_price)
            
            # Calculate and add benchmark performance metrics
            add_benchmark_metrics(result, index, benchmark_data, result_date)
            
            # Calculate alpha and ARS
            calculate_comparative_metrics(result, index, stock_data, benchmark_data)

        except Exception as e:
            print(f'Error processing {row.get("companyId", "unknown")}: {e}')
            continue
            
    # Save the result file
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"Processing complete. Results saved to {OUTPUT_FILE}")


def add_stock_metrics(result_df, index, stock_data, result_date, result_price):
    """
    Calculate and add stock-specific metrics to the result dataframe.
    
    Args:
        result_df: The dataframe containing stock information
        index: The row index in the dataframe
        stock_data: Historical stock data from yfinance
        result_date: The date when the result was announced
        result_price: The stock price on the result date
    """
    result_df.at[index, 'Result Date Price'] = round(result_price, 2)
    result_df.at[index, 'Last Close Date'] = stock_data.index[-1].strftime('%Y-%m-%d')
    result_df.at[index, 'Last Close Price'] = round(stock_data['Close'].iloc[-1], 2)
    result_df.at[index, '% Stock change'] = round((stock_data['Close'].iloc[-1] - result_price) / result_price * 100, 2)


def add_benchmark_metrics(result_df, index, benchmark_data, result_date):
    """
    Calculate and add benchmark metrics to the result dataframe.
    
    Args:
        result_df: The dataframe containing stock information
        index: The row index in the dataframe
        benchmark_data: Historical benchmark data from yfinance
        result_date: The date when the result was announced
    """
    benchmark_result_price = benchmark_data.loc[benchmark_data.index == result_date, "Close"].values[0]
    result_df.at[index, 'Result Date Benchmark Price'] = round(benchmark_result_price, 2)
    result_df.at[index, 'Last Benchmark Date'] = benchmark_data.index[-1].strftime('%Y-%m-%d')
    result_df.at[index, 'Last Benchmark Price'] = round(benchmark_data['Close'].iloc[-1], 2)
    result_df.at[index, '% Benchmark change'] = round((benchmark_data['Close'].iloc[-1] - benchmark_result_price) / benchmark_result_price * 100, 2)


def calculate_comparative_metrics(result_df, index, stock_data, benchmark_data):
    """
    Calculate comparative performance metrics like Alpha and ARS.
    
    Args:
        result_df: The dataframe containing stock information
        index: The row index in the dataframe
        stock_data: Historical stock data from yfinance
        benchmark_data: Historical benchmark data from yfinance
    """
    # Calculate alpha (stock performance relative to benchmark)
    result_df.at[index, 'Alpha'] = result_df.at[index, '% Stock change'] - result_df.at[index, '% Benchmark change']

    # Calculate ARS (Adaptive Relative Strength)
    try:
        result_df.at[index, 'ARS'] = round(
            (stock_data['Close'].iloc[-1] / stock_data.loc[stock_data.index == ARS_DATE, "Close"].values[0]) / 
            (benchmark_data['Close'].iloc[-1] / benchmark_data.loc[benchmark_data.index == ARS_DATE, "Close"].values[0]) - 1, 2)
    except:
        result_df.at[index, 'ARS'] = 0.00  # Error in calculating ARS, set it to 0.00


if __name__ == "__main__":
    main()