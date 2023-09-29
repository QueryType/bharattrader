'''
We detect a consolidation after a rally and quantify the box formation
Rally is defined as 3 consecutive higher closes, and the high of that candle defines the top left of the box
The low is extended with each new lower low
'''
import yfinance as yf
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# Set the bar time frame
data_interval = '1d'
# Set the time frame to 90d
time_frame = '90d'

# Set output folder path
output_path = "boxscan/output"
# Initialize an empty DataFrame to store the output CSV data
output_df = pd.DataFrame(columns=['Stock Code', 'Box Duration', 'Drawdown', 'Fall Rate'])

# Read the list of stocks from the CSV file
stocks = pd.read_csv("stocks500.csv", header=0, usecols=["Ticker"])

# Box depth threshold %
box_depth_threshold = -20
# Rally days
min_rally_days = 3
# Box days
min_days_in_box = 3

# Function to plot and save chart and data
def scan_for_box(df, stock_code):

    # Calculate 50-day average volume
    df['50_day_avg_vol'] = df['Volume'].rolling(window=50).mean()

    # Set up plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    ax1.set_ylabel('Price')
    ax1.set_title(f'{stock_code} with Negative Drawdown')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Volume')

    # Initialize variables for debugging and the box
    rally_days = 0
    rally_volume_high = False
    box_start = None
    box_end = None
    box_high = None
    box_low = None

    # Iterate through the data to identify rallies, place debug dots, and draw the box
    for i in range(len(df)):
        color = 'g' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'r'
        vol_color = color
        vol_color = 'g' if i > 0 and df.iloc[i]['Close'] >= df.iloc[i-1]['Close'] else 'r'
            
        ax1.plot([i, i], [df.iloc[i]['Low'], df.iloc[i]['High']], color=color)
        ax1.add_patch(patches.Rectangle((i - 0.3, df.iloc[i]['Open']), 0.6, df.iloc[i]['Close'] - df.iloc[i]['Open'], facecolor=color))
        ax2.bar(i, df.iloc[i]['Volume'], color=vol_color, width=0.6)

        # Detect a rally
        if i > 0 and df.iloc[i]['Close'] > df.iloc[i - 1]['Close']:
            rally_days += 1
            if df.iloc[i]['Volume'] > df.iloc[i]['50_day_avg_vol']:
                rally_volume_high = True
        else:
            rally_days = 0
            rally_volume_high = False

        if rally_days >= min_rally_days and rally_volume_high:
            ax1.plot(i, df.iloc[i]['High'], 'o', color='orange')
            box_high = df.iloc[i]['High']
            box_low = df.iloc[i]['Low']
            box_start = i

        if box_start is not None:
            new_low = df.iloc[i]['Low']
            if new_low < box_low:
                box_low = new_low
            box_end = i
            ax1.add_patch(patches.Rectangle((box_start, box_low), box_end - box_start, box_high - box_low, fill=True, color='yellow', alpha=0.3))

            if df.iloc[i]['Close'] > box_high:
                box_start = None
                box_end = None
                box_high = None
                box_low = None

    # Book keeping
    if box_start is not None:
        box_days = (box_end - box_start) + 1
        box_drop_percent = -((box_high - box_low) / box_high) * 100
        box_fall_rate = round(-box_drop_percent / box_days, 2)
        text_str = f"Box Duration: {box_days} days\nDrawdown: {box_drop_percent:.2f}%\nFR: {box_fall_rate:.2f}"
        ax1.text(0.75, 0.1, text_str, transform=ax1.transAxes, fontsize=12, verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        if box_end == len(df) - 1 and box_drop_percent > box_depth_threshold and box_days > min_days_in_box:
            plt.savefig(f"{output_path}/{stock_code}.png")
            output_df.loc[len(output_df)] = [stock_code, box_days, box_drop_percent, box_fall_rate]
    plt.close()


def main():
    print('Started')
    # Iterate through the list of stocks
    for stock in stocks["Ticker"]:
        try:
            ticker = yf.Ticker(stock+".NS")
            stock_history = ticker.history(period=time_frame,interval=data_interval,auto_adjust=False)
            stock_history = stock_history.dropna()
            scan_for_box(stock_history, stock)
        except Exception as e:
            print(f"Error: {stock} ==> {e}")
    
    # Append current timestamp to the file name
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
    file_name = f'{output_path}/box_scan_{timestamp}.csv'
    # Export the DataFrame to CSV
    output_df.to_csv(file_name, index=False)
    print(f'Done, output saved in {file_name}')

if __name__ == "__main__":
    main()
