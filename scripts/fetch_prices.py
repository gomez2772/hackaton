"""Daily prices of the KID proxy ETFs (task C-5): 3 years from Yahoo Finance -> app/data/prices/<ticker>.csv.

Run:  python scripts/fetch_prices.py            (all proxy tickers in app/data/kids.json)
      python scripts/fetch_prices.py IWDA.AS    (only some tickers)
CSV columns: date, close (dividend/split adjusted). The files are versioned so the demo works offline.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from app.data.loaders import DATA, load_kids  # noqa: E402

log = logging.getLogger("fetch_prices")
MIN_ROWS = 700  # ~3 years of trading days, with some slack for holidays


def fetch(ticker: str, period: str = "3y") -> pd.DataFrame:
    """Adjusted daily close of `ticker` as a DataFrame with columns date, close."""
    import yfinance as yf

    hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if hist.empty:
        raise RuntimeError(f"Yahoo no devuelve precios para {ticker}")
    df = pd.DataFrame({"date": hist.index.tz_localize(None).date, "close": hist["Close"].round(4).to_numpy()})
    return df.dropna().drop_duplicates("date")


def main() -> None:
    """Download every proxy ticker (or those given) and write the CSVs."""
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="*", help="por defecto, todos los proxy_ticker de kids.json")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tickers = args.tickers or sorted({k.proxy_ticker for k in load_kids().values()})
    out = DATA / "prices"
    out.mkdir(exist_ok=True)
    failed = []
    for t in tickers:
        try:
            df = fetch(t)
        except Exception as e:  # network or Yahoo errors: report and continue with the rest
            log.error("%s: %s", t, e)
            failed.append(t)
            continue
        df.to_csv(out / f"{t}.csv", index=False)
        level = logging.WARNING if len(df) < MIN_ROWS else logging.INFO
        log.log(level, "%s: %d días (%s a %s)", t, len(df), df["date"].iloc[0], df["date"].iloc[-1])
    if failed:
        sys.exit(f"Fallaron: {', '.join(failed)}")


if __name__ == "__main__":
    main()
