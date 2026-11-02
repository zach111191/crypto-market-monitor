# Crypto Market Monitor

A small Python project for collecting, checking, storing, and exporting cryptocurrency market data. It uses [CCXT](https://github.com/ccxt/ccxt) to request public hourly OHLCV candles from Kraken.

The current scope is **Kraken, BTC/USD, and the 1-hour timeframe**. Each collection run requests recent candles, excludes candles that have not finished, and selects the latest eight completed candles returned by the exchange. No API key is required.

## Files

```text
crypto-market-monitor/
├── database_setup.py       # Create the SQLite table
├── fetch_sample.py         # Fetch, check, and save a recent batch
├── report.py               # Query stored data and export CSV
├── requirements.txt        # Tested CCXT version
├── README.md
├── .gitignore
└── examples/
    └── sample_report.csv   # Fixed example output
```

The scripts also generate `market_data.db` and `btc_usd_1h.csv` in the project folder. These local outputs are excluded from Git.

## Setup

Python **3.13** is used for this project; the local workflow was tested with **Python 3.13.9**.

From the project folder, run the following commands in a macOS or Linux terminal:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

Run these commands in order, with the virtual environment active:

```bash
python database_setup.py
python fetch_sample.py
python report.py
```

1. `database_setup.py` creates `market_data.db` and the `candles` table if they do not exist. Running it again keeps existing records.
2. `fetch_sample.py` selects eight completed hourly candles and checks for duplicate timestamps, internal missing hours, nonpositive prices, inconsistent high/low prices, and negative volume. It writes the batch only when the count and checks pass. It prints the attempted, newly inserted, and total database record counts.
3. `report.py` reads **all stored Kraken BTC/USD hourly candles**, ordered from oldest to newest. It displays the records and replaces `btc_usd_1h.csv` with the current query results. It does not change database records.

Collection is limited to the latest eight completed candles per run. The report can therefore contain more than eight rows as new batches accumulate. Running collection twice over the same hours can add zero new rows.

## Stored data and CSV

SQLite stores the exchange, symbol, timeframe, candle start timestamp in Unix milliseconds, and five OHLCV values: open, high, low, close, and volume.

The composite primary key is `(exchange, symbol, timeframe, timestamp)`. Insertion uses `ON CONFLICT ... DO NOTHING`: the first saved row for a key is kept, and later copies are skipped. This also means later exchange corrections do not update an existing row.

The CSV columns are:

```text
timestamp_ms,start_time_utc8,end_time_utc8,open,high,low,close,volume
```

The timestamp is the candle's start time. The two readable time columns use ISO 8601 with an explicit `+08:00` offset; the end time is one hour after the start. USD is the price currency and BTC is the volume unit for this market.

`examples/sample_report.csv` is a fixed eight-row excerpt from **2026-11-02**, covering **03:00–11:00 UTC+8**. The complete generated report can contain more records as the database grows. The example demonstrates the output format; it is not current market data.

## Manual checks

There is no automated test suite. The validation branches can be checked manually after a normal fetch returns eight completed candles.

In `fetch_sample.py`, immediately after `records_to_check = selected_candles.copy()`, temporarily uncomment **one case at a time**:

```python
# Duplicate timestamp:
# records_to_check.append(records_to_check[0])

# Missing internal hour:
# del records_to_check[3]

# Invalid high price (uncomment both lines):
# records_to_check[0] = records_to_check[0].copy()
# records_to_check[0][2] = records_to_check[0][1] - 1

# Negative volume (uncomment both lines):
# records_to_check[0] = records_to_check[0].copy()
# records_to_check[0][5] = -1
```

Run `python fetch_sample.py` for each case. Check that the expected issue is printed and the batch is rejected without writing to SQLite. Restore that case to comments before trying the next one. For numeric cases, copying the individual candle keeps the temporary change separate from the selected records.

Finally, restore all test lines to comments and run normally. To check duplicate-safe storage, repeat a successful collection over the same eight hours: the second run should report zero new rows. If the hour has changed, a new candle may legitimately be added.

## Limits

- The gap check detects missing hours only between the earliest and latest timestamps in the checked batch. It does not prove complete historical coverage or detect missing hours at either edge.
- Candle completion uses the computer's local clock. The project does not guarantee that exchange data is fresh or final.
- Each run is a one-shot recent batch. There is no scheduler or backfill for hours missed during downtime.
- The validation assumes each response candle contains six numeric fields in CCXT's OHLCV order. It does not handle every malformed response or non-finite numeric value.
- This is a data collection and validation learning project. It does not place trades, implement a trading strategy, or claim investment performance.
