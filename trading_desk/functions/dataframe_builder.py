import pandas as pd

def build_closing_price_series(klines:List):
    df = pd.DataFrame(klines, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "num_trades",
                "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
            ])

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close"] = df["close"].astype(float)
    return df.set_index("open_time")["close"]

def build_dataframe(close_prices:Dict):
    return pd.DataFrame(close_prices)
