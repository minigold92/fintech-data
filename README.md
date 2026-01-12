# Fintech Data Pipeline

Stock Portfolio 앱을 위한 금융 데이터 수집 파이프라인입니다.

## 데이터 URL

```
https://minigold92.github.io/fintech-data/
```

| 데이터 | URL |
|--------|-----|
| 가격 | `/data/prices.json` |
| ETF 구성종목 | `/data/etf-holdings/{SYMBOL}.json` |
| ETF 목록 | `/data/etf-holdings/index.json` |

## 지원 데이터

**EOD 가격**: VOO, QQQ, SCHD, VTI, SPY, AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA

**ETF 구성종목**: SPY, VOO, QQQ, SCHD, VTI

## 자동 업데이트

GitHub Actions로 매일 UTC 22:00 (KST 07:00) 자동 실행

## 문서

- [앱 연동 가이드](docs/APP-INTEGRATION.md) - 앱 담당자용
- [데이터 스키마](docs/DATA-SCHEMA.md) - 데이터 구조 상세
- [운영 가이드](docs/OPERATIONS.md) - 데이터 담당자용
