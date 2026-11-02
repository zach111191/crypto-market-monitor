import csv

import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

database_path = Path(__file__).resolve().with_name("market_data.db")
connection = sqlite3.connect(database_path)

query_sql = """
SELECT timestamp, open, high, low, close, volume
FROM candles
WHERE exchange = ? AND symbol = ? AND timeframe = ?
ORDER BY timestamp ASC
"""

result = connection.execute(query_sql, ("kraken", "BTC/USD", "1h"))
rows = result.fetchall()

connection.close()

local_timezone = timezone(timedelta(hours=8))

print("从数据库读取到的记录数：", len(rows))

for row in rows:
    start_time = datetime.fromtimestamp(row[0] / 1000, tz=local_timezone)
    end_time = start_time + timedelta(hours=1)

    print("开始时间：", start_time)
    print("结束时间：", end_time)
    print("OHLCV：", row[1:])
    print()


csv_path = Path(__file__).resolve().with_name("btc_usd_1h.csv")

with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "timestamp_ms",
        "start_time_utc8",
        "end_time_utc8",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ])

    for row in rows:
        start_time = datetime.fromtimestamp(row[0] / 1000, tz=local_timezone)
        end_time = start_time + timedelta(hours=1)

        writer.writerow([
            row[0],
            start_time.isoformat(),
            end_time.isoformat(),
            row[1],
            row[2],
            row[3],
            row[4],
            row[5]
        ])

print("CSV文件位置：", csv_path)
print("导出行情条数：", len(rows))