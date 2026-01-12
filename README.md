# Fintech Data Pipeline

Stock Portfolio 앱을 위한 금융 데이터 수집 파이프라인입니다.

## 목적

모바일 포트폴리오 앱에서 사용할 **EOD(End-of-Day) 가격**과 **ETF 구성종목** 데이터를 수집하여 정적 JSON 파일로 제공합니다.

### 왜 별도 Repo인가?

1. **Git 히스토리 분리**: 매일 업데이트되는 데이터와 앱 코드를 분리
2. **CDN 효과**: GitHub Pages로 정적 파일 서빙 (무료 + 빠름)
3. **독립 배포**: 앱 업데이트 없이 데이터만 갱신 가능
4. **담당자 분리**: 데이터 수집과 앱 개발을 별도로 관리

---

## 데이터 소비자 (앱)

### 앱 Repository
- **Repo**: `stock_portfolio` (Next.js 앱)
- **담당자**: (앱 개발자)

### 앱에서 데이터 사용 방식
```typescript
// src/infrastructure/api/remote-data-adapter.ts
const DATA_BASE_URL = process.env.NEXT_PUBLIC_DATA_URL || '/data-pipeline/data'

// 가격 조회
const prices = await fetch(`${DATA_BASE_URL}/prices.json`)

// ETF 구성종목 조회
const holdings = await fetch(`${DATA_BASE_URL}/etf-holdings/SPY.json`)
```

### 앱 설정 필요사항
```bash
# .env.local
NEXT_PUBLIC_DATA_URL=https://<username>.github.io/fintech-data/data
```

---

## 폴더 구조

```
fintech-data/                     # 이 Repo
├── .github/workflows/
│   └── update_data.yml           # 매일 자동 실행 (UTC 22:00 = KST 07:00)
├── scripts/
│   ├── fetch_data.py             # 메인 수집 스크립트
│   └── requirements.txt          # Python 의존성
├── data/                         # 앱용 데이터 (GitHub Pages 루트)
│   ├── prices.json               # EOD 가격
│   └── etf-holdings/
│       ├── index.json            # ETF 목록 인덱스
│       ├── SPY.json              # 개별 ETF 구성종목
│       ├── VOO.json
│       └── ...
└── raw/                          # 원본 데이터 (백업용)
    └── etf-holdings-full/
        └── SPY.json              # 전체 503개 홀딩 (섹터 없음)
```

---

## 현재 지원 데이터

### EOD 가격 (`data/prices.json`)

| 필드 | 설명 |
|------|------|
| `asOfDate` | 데이터 기준일 (YYYY-MM-DD) |
| `source` | 데이터 출처 ("Yahoo Finance") |
| `updatedAt` | 수집 시각 (ISO 8601) |
| `prices` | 심볼별 가격 정보 |

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

**수집 대상 심볼:**
- ETF: `VOO`, `QQQ`, `SCHD`, `VTI`, `SPY`
- 개별주: `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `TSLA`

### ETF 구성종목 (`data/etf-holdings/*.json`)

| 필드 | 설명 |
|------|------|
| `symbol` | ETF 티커 |
| `name` | ETF 이름 |
| `asOfDate` | 데이터 기준일 |
| `source` | 데이터 출처 (SSGA, Yahoo Finance) |
| `holdingsCount` | 저장된 홀딩 수 (최대 50) |
| `totalHoldings` | 전체 홀딩 수 (SSGA만 제공) |
| `holdings` | 구성종목 배열 |

```json
{
  "symbol": "SPY",
  "name": "SPDR S&P 500 ETF",
  "asOfDate": "2026-01-11",
  "source": "SSGA",
  "holdingsCount": 50,
  "totalHoldings": 503,
  "holdings": [
    { "symbol": "NVDA", "name": "NVIDIA CORP", "weight": 7.61, "sector": "Technology" },
    { "symbol": "AAPL", "name": "APPLE INC", "weight": 6.48, "sector": "Technology" }
  ]
}
```

---

## 데이터 소스 및 제한사항

### 현재 구현

| ETF | 소스 | 홀딩 수 | 비고 |
|-----|------|---------|------|
| **SPY** | SSGA 공식 Excel | 503개 (상위 50개 저장) | 섹터 정보 포함 |
| VOO | yfinance | 10개 | Yahoo 제한 |
| QQQ | yfinance | 10개 | Yahoo 제한 |
| SCHD | yfinance | 10개 | Yahoo 제한 |
| VTI | yfinance | 10개 | Yahoo 제한 |

### 개선 필요 (추후 작업)

1. **VOO/VTI**: Vanguard 공식 데이터 크롤링 구현
   - 현재: yfinance (10개)
   - 목표: Vanguard CSV (500개+)

2. **QQQ**: Invesco 공식 데이터 크롤링 구현
   - 현재: yfinance (10개)
   - 목표: Invesco API 또는 CSV

3. **SCHD**: Schwab 공식 데이터 크롤링 구현
   - 현재: yfinance (10개)
   - 목표: Schwab CSV

### 섹터 정보

- **방식**: yfinance 개별 종목 조회 (`ticker.info.sector`)
- **적용**: 상위 50개 종목에만 적용 (API 호출 제한)
- **캐시**: 스크립트 실행 중 메모리 캐시 사용

---

## 스크립트 실행

### 로컬 실행

```bash
cd scripts
pip install -r requirements.txt
python fetch_data.py
```

### GitHub Actions

```yaml
# .github/workflows/update_data.yml
# 매일 UTC 22:00 (KST 07:00) 자동 실행
# 수동 실행: Actions 탭 → "Update Data" → "Run workflow"
```

---

## 협업 인터페이스

### 앱 → 데이터 요청사항

앱에서 추가 데이터가 필요한 경우:

1. **새 심볼 추가**: `scripts/fetch_data.py`의 `MVP_ETFS` 또는 가격 심볼 목록 수정
2. **새 ETF 추가**: `ETF_HOLDINGS_SOURCES`에 소스 설정 추가
3. **필드 추가**: JSON 스키마 변경 시 앱 담당자와 협의 필요

### 데이터 → 앱 변경 알림

스키마 변경 시 앱 담당자에게 알려야 할 사항:

1. **필드 추가**: 앱 호환성 유지 (optional 필드로 추가)
2. **필드 제거/변경**: 사전 협의 필수
3. **source 변경**: 앱 UI에 표시되므로 알림 필요

### 연락처

- **앱 담당자**: (앱 개발자 연락처)
- **데이터 담당자**: (데이터 파이프라인 담당자)

---

## 트러블슈팅

### 일반적인 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| Holdings 0개 | yfinance API 변경 | `funds_data.top_holdings` 확인 |
| SSGA 다운로드 실패 | URL 변경 | SSGA 웹사이트에서 새 URL 확인 |
| 섹터 "Unknown" | yfinance 미제공 | BRK.B 등 일부 종목은 정상 |
| GitHub Actions 실패 | Rate limit | 재실행 또는 지연 추가 |

### 로그 확인

```bash
# 로컬 실행 시 상세 로그
python fetch_data.py 2>&1 | tee fetch.log
```

---

## 변경 이력

### 2026-01-12
- SSGA 공식 Excel 크롤링 구현 (SPY 503개 홀딩)
- 섹터 정보 enrichment (yfinance 개별 조회)
- 데이터 파이프라인 초기 구축

---

## 라이선스

Private - Internal Use Only
