# 운영 가이드

데이터 파이프라인 운영 및 관리 방법입니다.

## 폴더 구조

```
fintech-data/
├── .github/workflows/
│   └── update_data.yml       # 자동 실행 워크플로우
├── scripts/
│   ├── fetch_data.py         # 메인 수집 스크립트
│   └── requirements.txt      # Python 의존성
├── data/                     # 앱용 데이터 (GitHub Pages)
│   ├── prices.json
│   └── etf-holdings/
├── raw/                      # 원본 데이터 (백업)
│   └── etf-holdings-full/
└── docs/                     # 문서
```

## 로컬 실행

```bash
cd scripts
pip install -r requirements.txt
python fetch_data.py
```

## GitHub Actions

- **자동 실행**: 매일 UTC 22:00 (KST 07:00)
- **수동 실행**: Actions 탭 → "Update Data" → "Run workflow"

## 데이터 소스

| ETF | 소스 | 홀딩 수 | 비고 |
|-----|------|---------|------|
| SPY | SSGA 공식 Excel | 503개 (상위 50개 저장) | 섹터 정보 포함 |
| VOO | yfinance | 10개 | Yahoo 제한 |
| QQQ | yfinance | 10개 | Yahoo 제한 |
| SCHD | yfinance | 10개 | Yahoo 제한 |
| VTI | yfinance | 10개 | Yahoo 제한 |

## 개선 필요 작업

1. **VOO/VTI**: Vanguard 공식 CSV 크롤링 구현
2. **QQQ**: Invesco 공식 API 또는 CSV 구현
3. **SCHD**: Schwab 공식 CSV 구현

## 심볼 추가 방법

`scripts/fetch_data.py` 수정:

```python
# 가격 심볼 추가
PRICE_SYMBOLS = ["VOO", "QQQ", ..., "NEW_SYMBOL"]

# ETF 추가
MVP_ETFS = ["VOO", "QQQ", ..., "NEW_ETF"]
```

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| Holdings 0개 | yfinance API 변경 | `funds_data.top_holdings` 확인 |
| SSGA 다운로드 실패 | URL 변경 | SSGA 웹사이트에서 새 URL 확인 |
| 섹터 "Unknown" | yfinance 미제공 | BRK.B 등 일부 종목은 정상 |
| Actions 실패 | Rate limit | 재실행 또는 지연 추가 |

## 앱과 협업

### 스키마 변경 시

1. **필드 추가**: optional 필드로 추가 (앱 호환성 유지)
2. **필드 제거/변경**: 앱 담당자와 사전 협의 필수
3. **source 변경**: 앱 UI에 표시되므로 알림 필요

## 변경 이력

### 2026-01-12
- 데이터 파이프라인 별도 repo 분리
- GitHub Pages 활성화
- SSGA 공식 Excel 크롤링 구현 (SPY)
