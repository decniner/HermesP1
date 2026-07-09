# yfinance & Crypto Data Patterns

Session-derived patterns for fetching stock and crypto data via yfinance in Python web apps.

## Symbol Normalization

User symbols come in various formats. Normalize for yfinance:

| Input | Normalized | Type |
|-------|-----------|------|
| `8604:T` | `8604.T` | Tokyo Stock Exchange |
| `BTC/JPY` | `BTC-JPY` | Crypto pair (Yahoo format) |
| `ETH-JPY` | `ETH-JPY` | Already correct |
| `^N225` | `^N225` | Index (no change) |
| `BTC-USDT` | `BTC-USDT` | Already correct |

```python
def normalize_symbol(raw: str) -> str:
    s = raw.strip().upper()
    for sep in (":", "/"):
        if sep in s:
            parts = [p.strip() for p in s.split(sep, maxsplit=1)]
            if parts[0].isdigit():
                return f"{parts[0]}.{parts[1]}"
            return f"{parts[0]}-{parts[1]}"
    return s
```

## Fetching 4H Candles

```python
data = yf.download(
    tickers=ticker,
    period="1mo",     # ~30 days
    interval="4h",    # 4-hour candles
    progress=False,
    auto_adjust=True,
)
```

## Flattening MultiIndex Columns

yfinance may return MultiIndex columns. Always flatten before use:

```python
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data.columns = [str(c).lower() for c in data.columns]
```

## Default Assets for Market Analysis Apps

Useful starter symbols for a Japan-based user interested in both local stocks and crypto:

| Symbol | Description |
|--------|-------------|
| `8604.T` | Nomura Holdings (major Japanese brokerage) |
| `^N225` | Nikkei 225 index |
| `9984.T` | SoftBank Group |
| `BTC-JPY` | Bitcoin / Japanese Yen |
| `ETH-JPY` | Ethereum / Japanese Yen |
| `XRP-JPY` | Ripple / Japanese Yen |
