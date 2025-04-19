"""
Momentum Investing Scanner (MIP‑12) (Modified from Prashanth Sir’s book)

This module implements a momentum‑based stock scanner following the “MIP‑12” strategy 
from Prashanth Sir’s recent book. It filters and ranks Nifty 500 stocks by multiple 
technical criteria and outputs a CSV report. The original algorithm has been modified 
to include a ranking metric based on the Sharpe ratio, rather than Volar as that is proprietary.

--- Overview ---
1. Market Trend Filter:
    Checks if the benchmark index (e.g., Nifty 500) is above its 20‑day EMA.
2. Entry Filters (applied only when market is bullish):
    • 52‑Week High Retracement: stock must be within 50% of its 52‑week high.
    • 200‑Day EMA: stock’s latest close must exceed its 200‑day EMA.
3. Ranking Metric:
    Computes a simple Sharpe ratio (mean daily return ÷ standard deviation of daily returns).
4. Final Selection:
    • If market is bullish: all stocks passing entry filters are ranked by Sharpe ratio.
    • If market is bearish: no new entries are considered, but ranking is still performed.
5. Output:
    • `mip12_scan_report.csv` with columns: 
         Ticker, Rank#, Price, 52W_High, 200D_EMA, Sharpe_Ratio
    • `mip12_scan_errors.csv` capturing any per‑symbol exceptions.

--- Functions ---
market_trend_filter(benchmark_df, ema_period=20) → bool  
get_52w_high(stock_df, period=252) → float  
get_200d_ema(stock_df, period=200) → float  
compute_sharpe_ratio(stock_df) → float  

--- Main Flow ---
1. Load benchmark data.
2. Determine `is_bullish` flag based on the market trend filter.
3. Loop over each symbol:
    a. Load its price series.
    b. If bullish, enforce entry filters (52W High Retracement and 200D EMA).
    c. Compute Sharpe ratio for ranking.
    d. Append record (Ticker, Price, 52W_High, 200D_EMA, Sharpe_Ratio).
    e. Catch and log any exceptions per symbol.
4. Build a DataFrame, sort by Sharpe ratio, and insert Rank#.
5. Export the report and any errors to CSV.

--- Logging & Error Handling ---
- Uses Python’s `logging` module to record INFO and ERROR messages.
- Errors for individual symbols are collected and saved to `mip12_scan_errors.csv`.

Usage:
     python mip12_scanner.py

"""
import pricereader as pr
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Interval
data_interval = 'd'

# Benchmark symbol
benchmark = "CRSLDX"  # Nifty 500 Index

# Read the list of stocks from the CSV file
stocks = pd.read_csv("nifty500.csv", header=0, usecols=["Ticker"])

# --- Helper functions ---

def market_trend_filter(benchmark_df: pd.DataFrame,
                        ema_period: int = 20,
                        price_col: str = 'Close') -> bool:
    """Return True if latest benchmark Close > its EMA."""
    ema = benchmark_df[price_col].ewm(span=ema_period, adjust=False).mean()
    return benchmark_df[price_col].iloc[-1] > ema.iloc[-1]

def get_52w_high(stock_df: pd.DataFrame,
                 period: int = 252,
                 price_col: str = 'Close') -> float:
    """Return the 52‑week high price, or NaN if insufficient data."""
    closes = stock_df[price_col].dropna()
    if len(closes) < period:
        return float('nan')
    return closes.iloc[-period:].max()

def get_200d_ema(stock_df: pd.DataFrame,
                period: int = 200,
                price_col: str = 'Close') -> float:
    """Return the most recent 200‑day EMA, or NaN if insufficient data."""
    closes = stock_df[price_col].dropna()
    if len(closes) < period:
        return float('nan')
    ema = closes.ewm(span=period, adjust=False).mean()
    return ema.iloc[-1]

def passes_ratio_200d_ema(stock_df: pd.DataFrame,
                          benchmark_df: pd.DataFrame,
                          period: int = 200,
                          price_col: str = 'Close') -> bool:
    """
    Return True if the latest ratio of stock/benchmark Close is above
    its 200‑day EMA on the ratio series.
    """
    # align on common dates
    ratio = (stock_df[price_col] / benchmark_df[price_col]).dropna()
    if len(ratio) < period:
        return False
    ema = ratio.ewm(span=period, adjust=False).mean()
    return ratio.iloc[-1] > ema.iloc[-1]

def compute_sharpe_ratio(stock_df: pd.DataFrame,
                         price_col: str = 'Close',
                         period: int = 252) -> float:
    """
    Compute the Sharpe ratio as mean(daily returns) / std(daily returns) for the last `period` days.
    Returns 0.0 if there is insufficient data or if the annualized volatility is zero.
    """
    df_1y = stock_df.tail(period).copy()

    # Calculate 12M ROC
    current_price = df_1y['Close'].iloc[-1]
    price_1y_ago = df_1y['Close'].iloc[0]
    roc_12m = (current_price / price_1y_ago) - 1

    # Daily returns & volatility
    df_1y['daily_return'] = df_1y['Close'].pct_change()
    daily_vol = df_1y['daily_return'].std()
    annualized_vol = daily_vol * np.sqrt(period)

    return 0.0 if annualized_vol == 0 else roc_12m / annualized_vol


# --- Main scanning function ---

def main():
     
    logging.info("Scan started.")
    
    # 1. Load & trim benchmark data
    benchmark_data = pr.get_price_data(benchmark, data_interval)
    
    # 2. Check market trend
    is_bullish = market_trend_filter(benchmark_data)
    if is_bullish:
        logging.info("Market is bullish → full entry filters apply.")
    else:
        logging.info("Market is NOT bullish → only ranking/exits, no new entries.")
        print("Market is NOT bullish → only ranking/exits, no new entries.")
    
    # 3. Prepare lists
    candidates = stocks["Ticker"].tolist()
    records = []
    errors = []
    
    # 4. Per‐stock processing
    for symbol in candidates:
        try:
            print(f"Processing {symbol}...")
            df = pr.get_price_data(symbol, data_interval)
            if df.empty:
                continue  # no data in date range
            
            # Entry filters if bullish
            high_52w = get_52w_high(df)
            ema_200  = get_200d_ema(df)
            
            
            price = df['Close'].iloc[-1]
            if pd.isna(high_52w) or price < 0.5 * high_52w:
                logging.info("Skipping %s: 52W high retracement not met.", symbol)
                continue
            if pd.isna(ema_200) or price <= ema_200:
                logging.info("Skipping %s: 200D EMA not met.", symbol)
                continue

            if not passes_ratio_200d_ema(df, benchmark_data):
                logging.info("Skipping %s: ratio chart condition not met.", symbol)
                continue
            
            # Compute ranking metric
            sharpe = compute_sharpe_ratio(df)
            
            # Record all required fields
            records.append({
                "Ticker":       symbol,
                "Price":        df['Close'].iloc[-1],
                "52W_High":     high_52w,
                "200D_EMA":     ema_200,
                "Sharpe_Ratio": sharpe
            })
        
        except Exception as e:
            logging.error(f"Error processing {symbol}: {e}")
            errors.append({"Ticker": symbol, "Error": str(e)})
    
    # 5. Build final report DataFrame
    report_df = pd.DataFrame(records)
    report_df = report_df.dropna(subset=["Sharpe_Ratio"])
    report_df = report_df.sort_values("Sharpe_Ratio", ascending=False)
    report_df.insert(1, "Rank#", range(1, len(report_df) + 1))
    
    # 6. Export results
    report_df.to_csv("mip12_scan_report.csv", index=False)
    logging.info("Report saved to mip12_scan_report.csv.")
    
    # 7. Optionally export errors
    if errors:
        err_df = pd.DataFrame(errors)
        err_df.to_csv("mip12_scan_errors.csv", index=False)
        logging.info("Errors saved to mip12_scan_errors.csv.")
    
    return report_df

# If this script is run directly, invoke main():
if __name__ == "__main__":
    main()
