# Token Transaction Velocity Analysis Tool

## Overview
This tool provides a way to analyze the relative changes in transaction velocity for a given Solana token. By fetching transaction data and price history, it helps determine the level of token activity over a given time window.

## Features
- Fetches recent transactions for a specified Solana token
- Retrieves historical price data for correlation analysis
- Plots transactions per minute (TPM) with price overlay
- Computes TPM-derived metrics for deeper insights
- Implements EMA smoothing to highlight trends
- Provides a simple and interactive GUI for user input

## Installation
### Prerequisites:
Ensure you have the following dependencies installed:

- Python 3.7+
- `requests`
- `pandas`
- `matplotlib`
- `tkinter`
- `solders`
- `solana`

Install dependencies using:
```bash
pip install requests pandas matplotlib solana solders
```

## Usage
1. Run the script:
   ```bash
   python script.py
   ```
2. Enter the Solana token address.
3. Specify the time window (in hours) for analysis.
4. Click **Check** to generate the transaction and price analysis plot.

## How It Works
- **Transaction Data:** Fetches transaction timestamps for the given token from the Solana blockchain.
- **Price Data:** Retrieves historical price data from Birdeye API.
- **Analysis:**
  - Computes transactions per minute (TPM).
  - Applies exponential moving averages (EMA) for trend smoothing.
  - Plots TPM against price changes for correlation.
  - Computes a derived metric: `TPM / (Price * 1B)`.

## Interpretation
- A **rise in TPM** suggests increased activity, which may indicate buying pressure or heightened interest in the token.
- The **Derived metric (TPM/Price)** helps gauge relative activity independent of price movements.
- **EMA trends** allow for smoothing of volatile data, making trends easier to spot.

## API Keys
This script requires API keys for:
- Solana RPC
- Birdeye price data

Ensure your keys are correctly set in the script before running.

## Notes
- This tool does not predict token price movements but helps in assessing token activity.
- A high TPM without price changes may indicate wash trading or bot activity.
- Use insights from this tool alongside other market research for informed decisions.

## Screenshot

![img]("https://i.ibb.co/3m7XGgFQ/Screenshot-2025-03-07-185532.png")


## License
MIT License

## Disclaimer
This tool is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

