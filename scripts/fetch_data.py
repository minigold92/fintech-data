#!/usr/bin/env python3
"""
Stock Portfolio Data Fetcher
- EOD 가격 수집 (yfinance)
- ETF 구성종목 수집 (운용사 공식 CSV + yfinance fallback)
- 섹터 정보 조회 (yfinance)

사용법:
    python fetch_data.py

출력:
    ../data/prices.json          - EOD 가격 데이터
    ../data/etf-holdings/*.json  - ETF 구성종목 (상위 50개)
    ../raw/etf-holdings-full/*   - ETF 구성종목 원본
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RAW_DIR = SCRIPT_DIR.parent / "raw"

# MVP 지원 ETF 목록
MVP_ETFS = ["VOO", "QQQ", "SCHD", "VTI", "SPY"]

# 섹터 캐시 (API 호출 최소화)
_sector_cache: dict[str, str] = {}

# ETF 운용사별 Holdings 소스
ETF_HOLDINGS_SOURCES = {
    "SPY": {
        "provider": "SSGA",
        "url": "https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx",
        "type": "ssga_excel",
    },
    "VOO": {
        "provider": "Vanguard",
        "type": "yfinance",  # Vanguard는 직접 다운로드 어려움
    },
    "VTI": {
        "provider": "Vanguard",
        "type": "yfinance",
    },
    "QQQ": {
        "provider": "Invesco",
        "type": "yfinance",  # Invesco도 직접 다운로드 복잡
    },
    "SCHD": {
        "provider": "Schwab",
        "type": "yfinance",
    },
}


def get_sector(symbol: str) -> str:
    """
    yfinance를 사용하여 개별 종목의 섹터 정보 조회
    캐시를 사용하여 중복 API 호출 방지
    """
    if symbol in _sector_cache:
        return _sector_cache[symbol]

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get("sector", "Unknown")
        _sector_cache[symbol] = sector
        return sector
    except Exception:
        _sector_cache[symbol] = "Unknown"
        return "Unknown"


def fetch_eod_prices(symbols: list[str]) -> dict:
    """yfinance를 사용하여 EOD 가격 수집"""
    print(f"Fetching EOD prices for {len(symbols)} symbols...")

    tickers = yf.Tickers(" ".join(symbols))

    prices = {}
    for symbol in symbols:
        try:
            ticker = tickers.tickers.get(symbol)
            if ticker is None:
                print(f"  Warning: {symbol} not found")
                continue

            hist = ticker.history(period="2d")
            if len(hist) < 1:
                print(f"  Warning: No data for {symbol}")
                continue

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0

            prices[symbol] = {
                "price": round(current_price, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
            }
            print(f"  {symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")

        except Exception as e:
            print(f"  Error fetching {symbol}: {e}")

    return {
        "asOfDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "Yahoo Finance",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "prices": prices,
    }


def fetch_holdings_ssga(symbol: str, url: str, top_n: int = 50, enrich_sector: bool = True) -> Optional[dict]:
    """
    SSGA(State Street) ETF Holdings 수집 (SPY 등)
    공식 Excel 파일에서 전체 구성종목 + Weight 수집
    """
    print(f"Fetching {symbol} holdings from SSGA...")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        if response.status_code != 200:
            print(f"  Error: HTTP {response.status_code}")
            return None

        # 임시 파일로 저장 후 읽기
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        # Excel 파싱 (skiprows=4로 헤더 스킵)
        df = pd.read_excel(temp_path, engine='openpyxl', skiprows=4)
        os.unlink(temp_path)

        print(f"  Raw data: {len(df)} rows")

        # 데이터 추출
        holdings = []
        symbols_to_enrich = []

        for _, row in df.iterrows():
            ticker = row.get('Ticker', '')
            if pd.isna(ticker) or ticker == '' or ticker == '-':
                continue

            name = row.get('Name', '')
            weight = row.get('Weight', 0)

            if pd.isna(weight):
                continue

            holding = {
                "symbol": str(ticker).strip(),
                "name": str(name).strip() if not pd.isna(name) else '',
                "weight": round(float(weight), 2),
                "sector": "Unknown",
            }
            holdings.append(holding)
            symbols_to_enrich.append(str(ticker).strip())

        print(f"  Parsed {len(holdings)} holdings")

        # 섹터 정보 추가 (상위 N개만)
        if enrich_sector and holdings:
            print(f"  Enriching sector info for top {min(top_n, len(holdings))} holdings...")
            for i, holding in enumerate(holdings[:top_n]):
                sector = get_sector(holding["symbol"])
                holding["sector"] = sector
                if (i + 1) % 10 == 0:
                    print(f"    {i + 1}/{min(top_n, len(holdings))} done")

        # ETF 이름 가져오기
        try:
            etf_ticker = yf.Ticker(symbol)
            etf_name = etf_ticker.info.get("longName", symbol)
        except:
            etf_name = f"SPDR {symbol} ETF"

        return {
            "symbol": symbol,
            "name": etf_name,
            "asOfDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": "SSGA",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "holdingsCount": len(holdings),
            "holdings": holdings[:top_n],
            "totalHoldings": len(holdings),
        }

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def fetch_holdings_yfinance(symbol: str, top_n: int = 50, enrich_sector: bool = True) -> Optional[dict]:
    """
    yfinance를 사용하여 ETF 구성종목 수집 (fallback)
    상위 10개만 제공됨 (Yahoo Finance 제한)
    """
    print(f"Fetching {symbol} holdings from yfinance...")

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        etf_name = info.get("longName", symbol)

        holdings_df = None
        try:
            if hasattr(ticker, 'funds_data'):
                holdings_df = ticker.funds_data.top_holdings
        except Exception as e:
            print(f"  funds_data error: {e}")

        if holdings_df is None or holdings_df.empty:
            print(f"  Warning: No holdings data for {symbol}")
            return None

        holdings = []
        for stock_symbol, row in holdings_df.head(top_n).iterrows():
            weight_decimal = row.get("Holding Percent", 0)
            weight_percent = round(float(weight_decimal) * 100, 2)

            sector = "Unknown"
            if enrich_sector:
                sector = get_sector(str(stock_symbol))

            holding = {
                "symbol": str(stock_symbol),
                "name": row.get("Name", ""),
                "weight": weight_percent,
                "sector": sector,
            }
            holdings.append(holding)

        print(f"  Found {len(holdings)} holdings")

        return {
            "symbol": symbol,
            "name": etf_name,
            "asOfDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": "Yahoo Finance",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "holdingsCount": len(holdings),
            "holdings": holdings,
        }

    except Exception as e:
        print(f"  Error: {e}")
        return None


def fetch_etf_holdings(symbol: str, top_n: int = 50, enrich_sector: bool = True) -> Optional[dict]:
    """
    ETF 구성종목 수집 (운용사 소스 우선, yfinance fallback)
    """
    config = ETF_HOLDINGS_SOURCES.get(symbol, {"type": "yfinance"})

    if config.get("type") == "ssga_excel":
        result = fetch_holdings_ssga(symbol, config["url"], top_n, enrich_sector)
        if result:
            return result
        print(f"  Falling back to yfinance for {symbol}")

    return fetch_holdings_yfinance(symbol, top_n, enrich_sector)


def save_json(data: dict, filepath: Path):
    """JSON 파일 저장"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filepath}")


def main():
    print("=" * 50)
    print("Stock Portfolio Data Fetcher")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 50)

    # 1. EOD 가격 수집
    print("\n[1/2] Fetching EOD Prices...")
    price_symbols = MVP_ETFS + ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]
    prices_data = fetch_eod_prices(price_symbols)
    save_json(prices_data, DATA_DIR / "prices.json")

    # 2. ETF 구성종목 수집
    print("\n[2/2] Fetching ETF Holdings...")

    all_holdings = {}
    for symbol in MVP_ETFS:
        # 앱용 데이터 (상위 50개, 섹터 포함)
        holdings = fetch_etf_holdings(symbol, top_n=50, enrich_sector=True)

        if holdings:
            save_json(holdings, DATA_DIR / "etf-holdings" / f"{symbol}.json")
            all_holdings[symbol] = holdings

            # 원본 데이터 (전체, 섹터 없음 - 빠른 수집)
            if holdings.get("totalHoldings", 0) > 50:
                full_holdings = fetch_etf_holdings(symbol, top_n=500, enrich_sector=False)
                if full_holdings:
                    save_json(full_holdings, RAW_DIR / "etf-holdings-full" / f"{symbol}.json")

    # 통합 인덱스 파일
    index_data = {
        "asOfDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "etfs": {
            symbol: {
                "name": data["name"],
                "holdingsCount": data["holdingsCount"],
                "source": data["source"],
            }
            for symbol, data in all_holdings.items()
        }
    }
    save_json(index_data, DATA_DIR / "etf-holdings" / "index.json")

    print("\n" + "=" * 50)
    print("Data fetch completed!")
    print(f"Prices: {len(prices_data['prices'])} symbols")
    print(f"ETF Holdings: {len(all_holdings)} ETFs")
    print(f"Sector cache: {len(_sector_cache)} symbols")
    print("=" * 50)


if __name__ == "__main__":
    main()
