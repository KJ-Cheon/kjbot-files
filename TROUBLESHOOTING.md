# KJBot 거래 실행 문제 해결 가이드

## 🚨 증상: TradingView 알림은 오지만 실제 거래가 실행되지 않음

### 📋 체크리스트 (순서대로 확인)

#### 1️⃣ **서버 로그 확인** (가장 중요!)
```bash
# SSH로 서버 접속 후
sudo tail -f /var/log/kjbot/webhook.log
```

**로그에서 확인할 내용:**
- `📨 Webhook 수신:` - 웹훅이 도착했는지 확인
- `⚠️ 허용되지 않은 IP:` - IP 차단 여부
- `❌ 거래가 비활성화되어 있습니다` - 거래 비활성화 상태
- `❌ binance 거래소가 연결되지 않았습니다` - API 키 미등록
- `✅ 거래 성공:` - 정상 실행

---

#### 2️⃣ **거래 활성화 확인**

**Cockpit 대시보드에서 확인:**
1. 서버 IP로 접속 (http://서버IP)
2. 좌측 하단 "KJBOT" 메뉴 클릭
3. "거래 설정" 섹션에서 **"거래 활성화"** 스위치가 **ON**인지 확인

**또는 SSH로 직접 확인:**
```bash
cat /etc/kjbot/config.json | grep enable_trading
```

**결과:**
- `"enable_trading": true` ✅ 정상
- `"enable_trading": false` ❌ 거래 비활성화됨

**수정 방법:**
```bash
# config.json 편집
sudo nano /etc/kjbot/config.json

# enable_trading을 true로 변경
"enable_trading": true

# 저장 후 서비스 재시작
sudo systemctl restart kjbot
```

---

#### 3️⃣ **Binance API 키 등록 확인**

**Cockpit 대시보드에서 확인:**
1. "API 키 설정" 섹션
2. Binance 상태 배지가 **"연결됨"** 또는 **초록색**인지 확인

**SSH로 확인:**
```bash
cat /etc/kjbot/config.json | grep -A 3 "api_keys"
```

**API 키가 없다면:**
1. Cockpit 대시보드에서 API 키 입력
2. 또는 SSH로 직접 등록:
```bash
curl -X POST http://localhost:5000/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "binance",
    "api_key": "YOUR_API_KEY",
    "secret_key": "YOUR_SECRET_KEY"
  }'
```

---

#### 4️⃣ **IP 화이트리스트 설정 확인** (보안모드)

**현재 설정 확인:**
```bash
cat /etc/kjbot/config.json | grep require_ip_whitelist
```

**결과:**
- `"require_ip_whitelist": false` ✅ 일반모드 (모든 IP 허용)
- `"require_ip_whitelist": true` ⚠️ 보안모드 (화이트리스트만 허용)

**보안모드일 경우 해결 방법:**

**방법 1: 일반모드로 변경 (권장)**
```bash
sudo nano /etc/kjbot/config.json

# 다음과 같이 수정
"security": {
    "require_ip_whitelist": false,
    "allowed_ips": []
}

# 저장 후 재시작
sudo systemctl restart kjbot
```

**방법 2: TradingView IP 추가**
```bash
sudo nano /etc/kjbot/config.json

# TradingView IP 범위 추가
"security": {
    "require_ip_whitelist": true,
    "allowed_ips": [
        "52.89.214.238",
        "34.212.75.30",
        "54.218.53.128",
        "52.32.178.7"
    ]
}

# 저장 후 재시작
sudo systemctl restart kjbot
```

---

#### 5️⃣ **TradingView Webhook URL 확인**

**올바른 형식:**
```
http://YOUR_SERVER_IP/webhook
```

**잘못된 형식:**
- `http://YOUR_SERVER_IP:5000/webhook` ❌ (포트 번호 불필요)
- `https://YOUR_SERVER_IP/webhook` ❌ (https 아님)
- `http://YOUR_SERVER_IP` ❌ (/webhook 경로 필수)

---

#### 6️⃣ **TradingView Alert Message 형식 확인**

**올바른 JSON 형식:**
```json
{
    "action": "long_entry",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "leverage": 10,
    "percent": 50
}
```

**필수 필드:**
- `action`: "long_entry", "short_entry", "long_exit", "short_exit"
- `symbol`: "BTCUSDT" (바이낸스 선물 심볼)
- `exchange`: "binance"

**선택 필드:**
- `leverage`: 레버리지 (기본값: 1)
- `percent`: 진입 시 잔고의 몇 % 사용 (예: 50)
- `amount`: 직접 금액 지정 (USDT)

---

## 🧪 테스트 방법

### 1. 수동 Webhook 테스트
```bash
curl -X POST http://YOUR_SERVER_IP/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": "long_entry",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "leverage": 1,
    "amount": 11
  }'
```

**예상 응답:**
- 성공: `{"success": true, "message": "🟢 롱 진입 성공"}`
- 실패: `{"success": false, "message": "오류 메시지"}`

### 2. 서비스 상태 확인
```bash
# KJBot 서비스 상태
sudo systemctl status kjbot

# 최근 로그 확인
sudo journalctl -u kjbot -n 50 --no-pager
```

---

## 📊 일반적인 오류 메시지와 해결 방법

| 오류 메시지 | 원인 | 해결 방법 |
|------------|------|----------|
| `⚠️ 거래가 비활성화되어 있습니다` | enable_trading = false | Cockpit에서 거래 활성화 ON |
| `❌ binance 거래소가 연결되지 않았습니다` | API 키 미등록 | Cockpit에서 API 키 등록 |
| `Unauthorized IP address` | IP 화이트리스트 차단 | 일반모드로 변경 또는 IP 추가 |
| `JSON required` | TradingView 메시지 형식 오류 | Alert Message를 JSON 형식으로 수정 |
| `Missing action` | action 필드 누락 | Alert Message에 action 추가 |

---

## 🔧 완전 초기화 (최후의 수단)

```bash
# 설정 파일 삭제
sudo rm /etc/kjbot/config.json
sudo rm /etc/kjbot/secret.key

# 서비스 재시작 (기본 설정으로 초기화됨)
sudo systemctl restart kjbot

# Cockpit에서 다시 API 키 등록
```

---

## 📞 추가 지원

문제가 계속되면 다음 정보를 수집하여 문의:
1. `/var/log/kjbot/webhook.log` 내용
2. `sudo systemctl status kjbot` 결과
3. TradingView Alert 설정 스크린샷
