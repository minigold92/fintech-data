# 앱 연동 가이드

Stock Portfolio 앱에서 데이터를 연동하는 방법입니다.

## 환경 변수 설정

```bash
# .env.local
NEXT_PUBLIC_DATA_URL=https://minigold92.github.io/fintech-data
```

## 데이터 사용 예시

```typescript
const DATA_BASE_URL = process.env.NEXT_PUBLIC_DATA_URL

// 가격 조회
const prices = await fetch(`${DATA_BASE_URL}/data/prices.json`)

// ETF 구성종목 조회
const holdings = await fetch(`${DATA_BASE_URL}/data/etf-holdings/SPY.json`)

// ETF 목록 조회
const index = await fetch(`${DATA_BASE_URL}/data/etf-holdings/index.json`)
```

## 데이터 요청사항

추가 데이터가 필요한 경우:

1. **새 심볼 추가**: 데이터 담당자에게 요청
2. **새 ETF 추가**: 데이터 소스 확인 필요
3. **스키마 변경**: 사전 협의 필수

## 주의사항

- 데이터는 EOD (장 마감 후) 기준
- 캐싱 권장 (매일 1회 업데이트)
- CORS 제한 없음 (GitHub Pages)
