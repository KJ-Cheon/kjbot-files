# 🤖 KJBot - 최종 버전

**TradingView Webhook 기반 Binance 선물 자동매매 봇**

---

## 🎯 주요 기능

- ✅ **Binance 선물 전용** (안전하고 빠른 거래)
- ✅ **복리 효과** (잔고 퍼센트 방식)
- ✅ **격리 마진** (리스크 제한)
- ✅ **복수 종목** (각기 다른 설정)
- ✅ **완전 자동화** (수동 작업 0)

---

## 📦 GitHub 업로드 파일

### **필수 파일 (2개):**

```
1. kjbot-manager-final.tar.gz
   위치: KJ-Bot/kjbot-manager-final.tar.gz

2. kjbot-cloud-init.yaml
   위치: KJ-Bot/deployment/kjbot-cloud-init.yaml
```

**Repository:** https://github.com/KJ-Cheon/kjbot-files

---

## 🚀 빠른 시작

### **1. GitHub 업로드**
```
kjbot-manager-final.tar.gz
kjbot-cloud-init.yaml
```

### **2. TradingView 설정**
```
Pine Script:
- tradingview/KJ-LongShort-KJBot.pine 복사
- 저장 및 차트에 추가

KJBot 설정:
✅ 웹훅 활성: ON
레버리지: 1 (안전)
포지션설정 선택: percent (복리)
포지션 비율(%): 10
```

### **3. Vultr 서버 생성**
```
deployment/kjbot-cloud-init.yaml 복사
→ Vultr User Data 붙여넣기
→ Deploy Now
→ 20분 대기
```

### **4. Cockpit 설정**
```
http://<서버IP>
(포트 9090 없이 접속!)

KJBOT 메뉴:
- API 키 설정
- 거래 설정 확인
- 마진 모드: 격리 마진
```

---

## 📁 프로젝트 구조

```
KJ-Bot/
├── README.md                      # 프로젝트 소개
├── FINAL_RELEASE.md               # 최종 가이드
├── kjbot-manager-final.tar.gz     # GUI 빌드 ⭐
├── cockpit-kjbot-v2/              # React 소스
├── backend/                       # Python 소스
├── deployment/
│   └── kjbot-cloud-init.yaml      # Cloud-Init ⭐
├── tradingview/
│   └── KJ-LongShort-KJBot.pine    # Pine Script ⭐
└── KJ-Bot-Ref/                    # 참고 문서
```

---

## 🎯 핵심 기능

### **1. 복리 효과**
```
잔고 1,000 USDT → 10% = 100 USDT
잔고 1,100 USDT → 10% = 110 USDT (자동 증가!)
```

### **2. 격리 마진**
```
각 포지션 독립
→ 한 포지션 청산되어도 다른 포지션 안전
```

### **3. 복수 종목**
```
BTCUSDT: 10%, 레버리지 10x
ETHUSDT: 5%, 레버리지 5x
→ 각 종목마다 독립적 설정!
```

---

## 📖 상세 가이드

모든 가이드는 `KJ-Bot-Ref/` 폴더에 있습니다:

- `FINAL_RELEASE.md` - 최종 배포 가이드
- `COMPOUND_EFFECT_GUIDE.md` - 복리 효과 가이드
- `DEPLOYMENT_V2.md` - 배포 상세 가이드

---

## ⚠️ 주의사항

### **안전 설정:**
```
✅ 레버리지: 1-5x (초보자)
✅ 포지션 비율: 5-10%
✅ 격리 마진 사용
✅ 소액으로 시작
```

### **API 권한:**
```
✅ Enable Futures (필수)
❌ Withdrawal (비활성화)
```

---

## 🔒 보안

- ✅ IP 화이트리스트 (TradingView IP만 허용)
- ✅ API 키 암호화 저장
- ✅ 격리 마진 (리스크 제한)

---

## 🛠️ 기술 스택

**Frontend:** React + TypeScript + Vite  
**Backend:** Python + Flask + CCXT  
**Infrastructure:** Ubuntu 22.04 + Nginx + Cockpit

---

## 📝 TradingView 설정

### **Webhook URL:**
```
http://<서버IP>/webhook
```

### **알림 메시지:**
```
비워두기! (Pine Script가 자동 생성)
```

---

## 🎊 최종 버전

**버전:** v2.3 (최종)  
**날짜:** 2026-01-04  
**GitHub:** https://github.com/KJ-Cheon/kjbot-files

---

**완벽한 KJBot으로 성공적인 거래 되세요!** 🚀
