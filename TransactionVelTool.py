import time
import pandas as pd
import matplotlib.pyplot as plt
import requests
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from solders.pubkey import Pubkey
from solders.signature import Signature
from datetime import datetime, timedelta, timezone
import json
from solana.rpc.api import Client
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImY4ZDI2ZWVmLTg3NzQtNGRlYi1iYzc4LTE1YjcxNGE3NGFmOCIsIm9yZ0lkIjoiMzMyNDk3IiwidXNlcklkIjoiMzQxODY3IiwidHlwZUlkIjoiNWJiZGQzZjAtMzJlYy00YTZhLTgzYjMtNzI5ZjFkZDQwYTViIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE2ODM4Mzk4NzcsImV4cCI6NDgzOTU5OTg3N30.XGlaO5-AdjrVjYk2fVG_YT695G7HdpeJAuSgcq1cTfQ'
headers = {
  "Accept": "application/json",
  "X-API-Key": API_KEY
}
global status_label
def get_token_name(ca):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{ca}/metadata"
    response = requests.request("GET", url, headers=headers)
    return response.json()['name']
# Pubkey.from_string(token_address)

def fetch_last_transactions(token_address,time_window,limit_per_request=1000):
    # Initialize Solana RPC client
    client = Client(
        "https://misty-fluent-dream.solana-mainnet.quiknode.pro/3a7e4bf5bdf4a7ac82f0de3af4b972a39d6e5922")  # better RPC

    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=time_window)
    all_block_times = []
    before_signature = None  # Initialize for pagination
    while True:
        # Fetch transactions
        response = client.get_signatures_for_address(
            Pubkey.from_string(token_address),
            before=Signature.from_string(before_signature) if before_signature else None,
            limit=limit_per_request
        )
        res = json.loads(response.to_json())
        if not res['result']:  # If no more results, break the loop
            break
        # Extract block times and filter for last hour
        filtered_transactions = [
            tx for tx in res['result']
            if datetime.fromtimestamp(tx["blockTime"], timezone.utc) >= one_hour_ago
        ]
        all_block_times.extend(tx["blockTime"] for tx in filtered_transactions)
        # Update the before_signature for the next batch
        before_signature = res['result'][-1]['signature']

        # Stop if the earliest transaction in this batch is older than one hour
        if datetime.fromtimestamp(res['result'][-1]["blockTime"], timezone.utc) < one_hour_ago:
            break

    return all_block_times

def fetch_price_data(token,fromtime):
    current_unix_time = int(time.time())
    # Define the API endpoint and parameters
    url = 'https://public-api.birdeye.so/defi/history_price'
    params = {
        'address': f'{token}',
        'address_type': 'token',
        'type': '1m',
        'time_from': f'{fromtime}',
        'time_to': f'{current_unix_time}'
    }
    headers = {
        'accept': 'application/json',
        'x-chain': 'solana',
        'X-API-KEY': 'a6a4842f77d44a6c8a3d8e5757c64f10'  # Replace with your actual API key
    }

    # Make the API request
    response = requests.get(url, headers=headers, params=params)

    # Parse the response
    if response.status_code == 200:
        res = response.json()['data']['items']

        # Extract prices and times
        prices = [snapshot['value'] for snapshot in res]
        times = [snapshot['unixTime'] for snapshot in res]

        # Convert Unix times to readable format
        readable_times = [time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t)) for t in times]

        # Create a DataFrame for calculations
        df = pd.DataFrame({
            'Time': readable_times,
            'Price': prices
        })
        return df


def plot_transactions_per_minute(token_address, time_window):
    rolling_window = 5
    start_time = time.time()
    block_times = fetch_last_transactions(token_address, int(time_window))
    end_time = time.time()
    execution_time = end_time - start_time
    status_label.config(text=f"Read: {len(block_times)} TX's ({execution_time:.5f}s)")

    # Convert block times to pandas datetime series
    timestamps = pd.to_datetime(block_times, unit='s')
    df = pd.DataFrame({'timestamp': timestamps})

    # Group by minute and count transactions
    df['minute'] = df['timestamp'].dt.floor('min')
    transactions_per_minute = df.groupby('minute').size()

    # Apply rolling window to smooth the data
    rolling_avg = transactions_per_minute.rolling(rolling_window).mean()

    try:
        token_name = get_token_name(token_address)
    except Exception as e:
        print(e)
        token_name = token_address
    from_time = int(end_time - int(time_window)*60*60)
    # Fetch price data
    price_df = fetch_price_data(token_address,from_time)

    # Merge price data with transactions data based on time
    price_df['Time'] = pd.to_datetime(price_df['Time'])  # Ensure consistent datetime format
    # Align TPM and price data by finding the nearest preceding price timestamp for each TPM timestamp
    tpm_df = pd.DataFrame({'minute': transactions_per_minute.index, 'TPM': transactions_per_minute.values})
    tpm_df = tpm_df.sort_values('minute')
    combined_df = pd.merge_asof(tpm_df, price_df, left_on='minute', right_on='Time', direction='backward')
    # Calculate derived values (TPM / (Price * 100000000))
    combined_df['Derived'] = combined_df['TPM'] / (combined_df['Price'] * 1000_000_000)
    # Calculate EMA20 for the Derived metric
    combined_df['EMA20'] = combined_df['Derived'].ewm(span=5, adjust=False).mean()

    combined_df['TPM_EMA20'] = combined_df['TPM'].ewm(span=10, adjust=False).mean()
    # Get dynamic y-axis range based on data
    max_value = rolling_avg.max()
    y_min = 0
    y_max = max(2000, max_value * 1.2)  # Ensure buffer above the peak

    # Plot the results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

    # First chart: Transactions per minute with price overlay
    #ax1.plot(tpm_df['minute'], rolling_avg, label=f'{rolling_window}-minute Rolling Average', color='black')
    ax1.plot(combined_df['minute'], combined_df['TPM_EMA20'], label='TPM EMA20', color='purple')
    ax1.set_title(f'TPM and Price Data for Token: {token_name}', fontsize=16)
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Transactions per Minute', fontsize=12)
    ax1.grid(True)
    ax1.legend(loc='upper left')

    # Add secondary y-axis for price
    ax1_twin = ax1.twinx()
    ax1_twin.plot(price_df['Time'], price_df['Price'], color='blue', label='Price')
    ax1_twin.set_ylabel('Price', fontsize=12)
    ax1_twin.legend(loc='upper right')

    # Second chart: Derived values
    ax2.plot(combined_df['minute'], combined_df['EMA20'], color='orange', linestyle='--', label='TPM / (Price * 1000M)')
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Derived Metric', fontsize=12)
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    plt.show()
    plt.show()



def start_gui():
    def on_plot():
        token_address = token_entry.get()
        try:
            time_window = int(time_window_entry.get())
            if not token_address:
                raise ValueError("Token address cannot be empty.")
            plot_transactions_per_minute(token_address, time_window)
        except Exception as e:
            print(e)
            messagebox.showerror("Input Error", 'error')

    # Create main window
    root = tk.Tk()
    root.title("Token Metrics Tool")
    root.geometry("400x250")

    # Add input fields and labels
    ttk.Label(root, text="Token Address:").pack(pady=5)
    token_entry = ttk.Entry(root, width=50)
    token_entry.pack(pady=5)

    ttk.Label(root, text="Time Window (hours):").pack(pady=5)
    time_window_entry = ttk.Entry(root, width=10)
    time_window_entry.pack(pady=5)

    # Add a Plot button
    plot_button = ttk.Button(root, text="Check", command=on_plot)
    plot_button.pack(pady=20)
    global status_label
    # Add a status label to show the number of signatures read
    status_label = ttk.Label(root, text="Ready", foreground="blue")
    status_label.pack(pady=10)

    # Run the GUI loop
    root.mainloop()

# Call the GUI function
start_gui()

