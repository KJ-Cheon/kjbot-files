# 📦 GitHub 업로드 파일

이 폴더에는 GitHub 저장소 `KJ-Cheon/kjbot-files`에 업로드할 파일들이 있습니다.

> ⚠️ **중요**: 이 폴더만 GitHub에 업로드합니다. 다른 위치의 파일은 소스 코드용입니다.

## 📁 프로젝트 폴더 구조

```
KJ-Bot/
├── github-uploads/          ← ✨ GitHub 업로드 전용 (이 폴더!)
│   ├── kjbot-backend.tar.gz
│   ├── kjbot-manager-latest.tar.gz
│   ├── kjbot-cloud-init.yaml
│   └── README.md
├── backend/                 ← 백엔드 소스 코드 (편집용)
│   ├── trading_engine.py
│   ├── webhook_server.py
│   ├── config_manager.py
│   ├── discord_notifier.py
│   └── requirements.txt
├── deployment/              ← 배포 설정 원본
│   ├── kjbot-cloud-init.yaml
│   └── build-cockpit.sh
└── cockpit-kjbot-v2/        ← GUI 소스 코드
```

## 📂 파일 목록

### 1. `kjbot-backend.tar.gz`
- **설명**: KJBot 백엔드 파일 (Python)
- **포함 내용**:
  - `trading_engine.py` - 거래 실행 엔진
  - `webhook_server.py` - 웹훅 서버
  - `config_manager.py` - 설정 관리
  - `discord_notifier.py` - 디스코드 알림
  - `requirements.txt` - Python 패키지 목록
  - `.env.example` - 환경변수 예시
- **생성 방법**: `backend/` 폴더의 모든 파일을 압축
- **최종 수정**: 2026-01-07 23:00

### 2. `kjbot-manager-latest.tar.gz`
- **설명**: KJBot Cockpit GUI (웹 대시보드)
- **포함 내용**: 
  - `manifest.json` - Cockpit 앱 메니페스트
  - `index.html` - 메인 HTML
  - `kjbot.js` - 자바스크립트 로직
  - `kjbot.css` - 스타일시트
- **최종 수정**: 2026-01-07 12:47

### 3. `kjbot-cloud-init.yaml`
- **설명**: Vultr 서버 자동 설치 스크립트
- **용도**: 서버 생성 시 User Data에 붙여넣기
- **포함 기능**:
  - Python, Nginx, Cockpit 자동 설치
  - GitHub에서 백엔드/GUI 다운로드
  - 서비스 자동 시작
  - 방화벽 설정
- **최종 수정**: 2026-01-07 22:01

---

## 🚀 GitHub 업로드 방법

### **웹 브라우저 사용 (권장)**

1. **GitHub 저장소 열기**
   ```
   https://github.com/KJ-Cheon/kjbot-files
   ```

2. **파일 업로드**
   - "Add file" → "Upload files" 클릭
   - `github-uploads` 폴더의 3개 파일 모두 드래그 & 드롭
   - Commit 메시지 입력 (예: "Update: v1.2 - 분할청산 알림 개선")
   - "Commit changes" 클릭

---

## 📝 업데이트 체크리스트

업로드 전 다음 사항을 확인하세요:

- [ ] `kjbot-backend.tar.gz` - 최신 백엔드 코드 반영됨
- [ ] `kjbot-manager-latest.tar.gz` - GUI 변경사항 반영됨
- [ ] `kjbot-cloud-init.yaml` - 설정 변경사항 반영됨
- [ ] 파일 크기 확인 (손상되지 않았는지)
- [ ] GitHub 업로드 완료
- [ ] 새 서버로 배포 테스트

---

## 🔄 파일 재생성 방법

### Backend 재생성
```powershell
cd c:\Users\KJCheon\Desktop\KJ-Auto\KJ-Bot
tar -czf kjbot-backend.tar.gz -C backend .
Copy-Item kjbot-backend.tar.gz github-uploads\ -Force
```

### GUI 재생성
```powershell
cd c:\Users\KJCheon\Desktop\KJ-Auto\KJ-Bot
# cockpit-kjbot 폴더에서 GUI 빌드 후
Copy-Item kjbot-manager-latest.tar.gz github-uploads\ -Force
```

### Cloud-Init 업데이트
```powershell
Copy-Item deployment\kjbot-cloud-init.yaml github-uploads\ -Force
```

---

## 📊 버전 관리

| 날짜 | 버전 | 변경사항 |
|------|------|----------|
| 2026-01-07 | v1.2 | 분할청산 시 포지션 없을 때 디스코드 알림 차단 |
| 2026-01-07 | v1.1 | 초기 배포 (Discord 알림, 분할청산 지원) |

---

**마지막 업데이트**: 2026-01-07 23:04
**유지보수자**: KJ-Cheon
