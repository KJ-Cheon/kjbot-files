# KJBot Vultr 서버 생성 체크리스트

## ✅ 수정 완료 사항

### 🔧 수정된 문제들
1. ✅ **YAML 파싱 오류 수정** - 440-473번 라인의 불필요한 HTML 코드 제거
2. ✅ **보안 설정 확인** - `require_ip_whitelist: False` (일반모드)
3. ✅ **Final Message 수정** - "General Mode (All IPs allowed)"로 변경
4. ✅ **GitHub 업로드 완료** - 모든 수정사항 반영

---

## 🚀 Vultr 서버 생성 절차 (정확히 따라하세요!)

### Step 1: Vultr 로그인
- https://my.vultr.com 접속

### Step 2: Deploy New Server
1. **Choose Server Type**: Cloud Compute
2. **Choose Location**: 원하는 지역 (Seoul 권장)
3. **Choose Image**: 
   - **Ubuntu 22.04 LTS** ⭐ (반드시 이 버전)
4. **Choose Plan**: 
   - 최소 **1GB RAM** 이상 (2GB 권장)
   - CPU: 1 vCPU 이상

### Step 3: ⭐ Cloud-Init User Data 입력 (가장 중요!)

**"Additional Features" 또는 "Startup Script" 섹션을 찾으세요:**

1. **"Enable Cloud-Init User Data"** 체크박스 클릭
2. 또는 **"Add Startup Script"** → **"Cloud-init"** 선택

3. **텍스트 박스에 다음 파일의 내용을 전체 복사/붙여넣기:**
   ```
   파일 위치: c:\Users\KJCheon\Desktop\KJ-Auto\KJ-Bot\deployment\kjbot-cloud-init.yaml
   ```

   **⚠️ 주의사항:**
   - 파일 **전체 내용**을 복사하세요 (1번 라인부터 마지막까지)
   - `#cloud-config`로 시작해야 합니다
   - 들여쓰기가 정확히 유지되어야 합니다

### Step 4: Server Hostname & Label
- **Server Hostname**: `KJ-Bot` (또는 원하는 이름)
- **Server Label**: `KJBot Production`

### Step 5: Deploy Now!
- **"Deploy Now"** 버튼 클릭

---

## ⏱️ 설치 대기 시간

### 예상 소요 시간: **5-10분**

**진행 상황:**
1. 서버 생성: 1-2분
2. Cloud-init 실행: 3-8분
3. 서비스 시작: 1분

### 설치 완료 확인 방법:

#### 방법 1: 브라우저 접속
```
http://YOUR_SERVER_IP
```
- ✅ Cockpit 로그인 화면이 나타나면 성공!

#### 방법 2: SSH 접속 후 확인
```bash
ssh root@YOUR_SERVER_IP

# Cloud-init 상태 확인
cloud-init status
# 결과: status: done ✅

# 서비스 상태 확인
systemctl status nginx
systemctl status cockpit.socket
systemctl status kjbot
# 모두 "active (running)" 상태여야 함 ✅
```

---

## 🎯 설치 완료 후 필수 작업

### 1. Cockpit 접속
```
http://YOUR_SERVER_IP
```

**로그인 정보:**
- Username: `root`
- Password: Vultr에서 설정한 root 비밀번호

### 2. KJBOT 메뉴 클릭
- 좌측 하단 **"KJBOT"** 메뉴 클릭

### 3. Binance API 키 등록
- "API 키 설정" 섹션에서:
  - Exchange: `binance`
  - API Key: `YOUR_BINANCE_API_KEY`
  - Secret Key: `YOUR_BINANCE_SECRET_KEY`
- **"저장"** 버튼 클릭

### 4. 거래 활성화 ⭐ (중요!)
- "거래 설정" 섹션에서:
  - **"거래 활성화"** 스위치를 **ON**으로 변경
  - 레버리지, 포지션 크기 등 설정 확인

### 5. TradingView Webhook 설정
```
http://YOUR_SERVER_IP/webhook
```

**Alert Message (JSON 형식):**
```json
{
    "action": "long_entry",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "leverage": 10,
    "percent": 50
}
```

---

## 🧪 테스트

### 1. 수동 Webhook 테스트 (SSH에서)
```bash
curl -X POST http://localhost/webhook \
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
```json
{"success": true, "message": "🟢 롱 진입 성공"}
```

### 2. 로그 확인
```bash
# 실시간 로그 모니터링
sudo tail -f /var/log/kjbot/webhook.log
```

---

## ❌ 문제 발생 시

### 증상: "사이트에 연결할 수 없음"

**체크리스트:**
1. [ ] `http://` (https 아님) 사용했나요?
2. [ ] 서버 생성 후 10분 이상 기다렸나요?
3. [ ] Cloud-init User Data를 입력했나요?
4. [ ] SSH 접속이 가능한가요?

**SSH 접속 후 확인:**
```bash
# Cloud-init 상태
cloud-init status

# 오류 로그 확인
tail -100 /var/log/cloud-init-output.log | grep -i error

# 서비스 상태
systemctl status nginx
systemctl status cockpit.socket
systemctl status kjbot
```

### 증상: "거래가 실행되지 않음"

**체크리스트:**
1. [ ] Cockpit에서 API 키를 등록했나요?
2. [ ] "거래 활성화"가 ON 상태인가요?
3. [ ] Binance API 키가 유효한가요?
4. [ ] TradingView Webhook URL이 정확한가요?

**상세 가이드:**
- `TROUBLESHOOTING.md` 파일 참고

---

## 📊 최종 확인 사항

설치 완료 후 다음을 모두 확인하세요:

- [ ] `http://서버IP`로 Cockpit 접속 가능
- [ ] KJBOT 메뉴가 좌측에 표시됨
- [ ] Binance API 키 등록 완료
- [ ] 거래 활성화 ON
- [ ] 수동 Webhook 테스트 성공
- [ ] TradingView Alert 설정 완료

---

## 🎉 성공!

모든 체크리스트를 완료하셨다면 KJBot이 정상적으로 작동합니다!

**실시간 거래 모니터링:**
```bash
# SSH 접속 후
sudo tail -f /var/log/kjbot/webhook.log
```

TradingView에서 Alert가 발생하면 이 로그에서 실시간으로 확인할 수 있습니다.

---

## 📞 지원

문제가 계속되면:
1. `/var/log/kjbot/webhook.log` 내용 확인
2. `cloud-init status` 결과 확인
3. `TROUBLESHOOTING.md` 참고
