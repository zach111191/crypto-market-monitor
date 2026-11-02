import sqlite3
from pathlib import Path

database_path = Path(__file__).resolve().with_name("market_data.db")

connection = sqlite3.connect(database_path)

connection.execute("""
CREATE TABLE IF NOT EXISTS candles (
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    PRIMARY KEY (exchange, symbol, timeframe, timestamp))
""")

connection.commit()

result = connection.execute("SELECT COUNT(*) FROM candles")
row_count = result.fetchone()[0]

print("数据库文件位置：", database_path)
print("表内记录数：", row_count)

connection.close()