import sqlite3
from pathlib import Path

import ccxt
from datetime import datetime,timezone,timedelta

local_timezone = timezone(timedelta(hours=8))
target_count = 8

#记录本轮检查的参考时间
reference_time = datetime.now(local_timezone)

exchange = ccxt.kraken()
candles = exchange.fetch_ohlcv("BTC/USD",
                               timeframe="1h",
                               limit=target_count + 1)

# 准备一个空列表，收集已经结束的小时记录
completed_candles = []

for candle in candles:
    start_time = datetime.fromtimestamp(candle[0]/1000, tz=local_timezone)
    end_time = start_time + timedelta(hours=1)

    if end_time <= reference_time:
        completed_candles.append(candle)
    else:
        print("暂时排除:", start_time, "至:", end_time)

# 从符合条件的记录中，取最后 8 条
selected_candles = completed_candles[- target_count:]

print("本轮参考时间", reference_time)
print("原始记录数：", len(candles))
print("最终保留记录数：", len(selected_candles))

if len(selected_candles) < target_count:
    print("提示：已经结束的记录不足 8 条，需要进一步检查。")

for candle in selected_candles:
    start_time = datetime.fromtimestamp(candle[0] / 1000, tz=local_timezone)
    end_time = start_time + timedelta(hours=1)
    print("开始时间：", start_time)
    print("结束时间：", end_time)
    print("OHLCV：", candle[1:])
    print()

# 复制一份记录，用于检查和后续测试
records_to_check = selected_candles.copy()
#records_to_check.append(records_to_check[0])
#del records_to_check[3]
#records_to_check[0] = records_to_check[0].copy()
#records_to_check[0][2] = records_to_check[0][1] - 1
#records_to_check[0][5] = -1

seen_timestamps = set()
duplicate_timestamps = []

for candle in records_to_check:
    timestamp = candle[0]

    if timestamp in seen_timestamps:
        duplicate_timestamps.append(timestamp)
    else:
        seen_timestamps.add(timestamp)

print("检查记录数：", len(records_to_check))
print("重复记录数：", len(duplicate_timestamps))

for timestamp in duplicate_timestamps:
    duplicate_time = datetime.fromtimestamp(timestamp / 1000, tz=local_timezone)
    print("重复时段的开始时间：", duplicate_time)

# 一小时对应的毫秒数
hour_ms = 60 * 60 * 1000
missing_timestamps = []

if len(seen_timestamps) > 0:
    first_timestamp = min(seen_timestamps)
    last_timestamp = max(seen_timestamps)

    for expected_timestamp in range(
        first_timestamp,
        last_timestamp + hour_ms,
        hour_ms):
        if expected_timestamp not in seen_timestamps:
            missing_timestamps.append(expected_timestamp)
print("内部缺失小时数", len(missing_timestamps))

for timestamp in missing_timestamps:
    missing_start = datetime.fromtimestamp(timestamp / 1000, tz=local_timezone)
    missing_end = missing_start + timedelta(hours=1)
    print("缺失时段:", missing_start,"至", missing_end)

invalid_record_count = 0
for candle in records_to_check:
    open_price= candle[1]
    high_price = candle[2]
    low_price = candle[3]
    close_price = candle[4]
    volume = candle[5]

    issues=[]
    if min(open_price, high_price, low_price, close_price) <= 0:
        issues.append("价格必须大于0")

    if high_price < max(open_price, low_price, close_price):
        issues.append("最高价低于其他价格")

    if low_price > min(open_price, high_price, close_price):
        issues.append("最低价高于其他价格")

    if volume < 0:
        issues.append("成交量不能为负数")

    if len(issues) > 0:
        invalid_record_count += 1
        record_time = datetime.fromtimestamp(candle[0] / 1000, tz=local_timezone)
        print("数值异常时段的开始时间：", record_time)
        print("发现的问题：", issues)
        print("这一条的OHLCV：", candle[1:])

print("数值异常记录数：", invalid_record_count)





checks_passed = (
    len(selected_candles) == target_count
    and len(duplicate_timestamps) == 0
    and len(missing_timestamps) == 0
    and invalid_record_count == 0 )

if checks_passed:
    database_path = Path(__file__).resolve().with_name("market_data.db")
    connection = sqlite3.connect(database_path)

    before_count = connection.execute(
        "SELECT COUNT(*) FROM candles" ).fetchone()[0]

    insert_sql = """
    INSERT INTO candles (
        exchange, symbol, timeframe, timestamp,
        open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (exchange, symbol, timeframe, timestamp) DO NOTHING
    """

    for candle in selected_candles:
        values = (
            "kraken", "BTC/USD", "1h",
            candle[0], candle[1], candle[2],
            candle[3], candle[4], candle[5])
        connection.execute(insert_sql, values)

    connection.commit()

    after_count = connection.execute(
        "SELECT COUNT(*) FROM candles" ).fetchone()[0]

    connection.close()

    print("本轮待保存条数：", len(selected_candles))
    print("本轮新增条数：", after_count - before_count)
    print("数据库累计条数：", after_count)
else:
    print("本轮数量不足或检查未通过，没有写入数据库。")
