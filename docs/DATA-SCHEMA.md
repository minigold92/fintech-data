# 데이터 스키마

## 가격 데이터 (`data/prices.json`)

```json
{
  "asOfDate": "2026-01-11",
  "source": "Yahoo Finance",
  "updatedAt": "2026-01-11T23:44:20+00:00",
  "prices": {
    "SPY": { "price": 694.07, "change": 4.55, "changePercent": 0.66 },
    "AAPL": { "price": 259.37, "change": 0.34, "changePercent": 0.13 }
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `asOfDate` | string | 데이터 기준일 (YYYY-MM-DD) |
| `source` | string | 데이터 출처 |
| `updatedAt` | string | 수집 시각 (ISO 8601) |
| `prices` | object | 심볼별 가격 정보 |
| `prices[symbol].price` | number | 종가 |
| `prices[symbol].change` | number | 전일 대비 변동 |
| `prices[symbol].changePercent` | number | 전일 대비 변동률 (%) |

## ETF 구성종목 (`data/etf-holdings/{SYMBOL}.json`)

```json
{
  "symbol": "SPY",
  "name": "SPDR S&P 500 ETF",
  "asOfDate": "2026-01-11",
  "source": "SSGA",
  "holdingsCount": 50,
  "totalHoldings": 503,
  "holdings": [
    { "symbol": "NVDA", "name": "NVIDIA CORP", "weight": 7.61, "sector": "Technology" }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `symbol` | string | ETF 티커 |
| `name` | string | ETF 이름 |
| `asOfDate` | string | 데이터 기준일 |
| `source` | string | 데이터 출처 |
| `holdingsCount` | number | 저장된 홀딩 수 |
| `totalHoldings` | number | 전체 홀딩 수 (가능한 경우) |
| `holdings` | array | 구성종목 배열 |
| `holdings[].symbol` | string | 종목 티커 |
| `holdings[].name` | string | 종목명 |
| `holdings[].weight` | number | 비중 (%) |
| `holdings[].sector` | string | 섹터 (없으면 "Unknown") |

## ETF 인덱스 (`data/etf-holdings/index.json`)

```json
{
  "updatedAt": "2026-01-11T23:44:20+00:00",
  "etfs": ["SPY", "VOO", "QQQ", "SCHD", "VTI"]
}
```

## TypeScript 타입

```typescript
interface PricesData {
  asOfDate: string
  source: string
  updatedAt: string
  prices: Record<string, {
    price: number
    change: number
    changePercent: number
  }>
}

interface ETFHolding {
  symbol: string
  name: string
  weight: number
  sector: string
}

interface ETFHoldingsData {
  symbol: string
  name: string
  asOfDate: string
  source: string
  holdingsCount: number
  totalHoldings?: number
  holdings: ETFHolding[]
}
```
