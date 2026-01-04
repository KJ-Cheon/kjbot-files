#!/bin/bash
# KJBot Cockpit GUI 빌드 스크립트

echo "🔨 KJBot Cockpit GUI 빌드 시작..."

# cockpit-kjbot 디렉토리로 이동
cd "$(dirname "$0")/../cockpit-kjbot" || exit 1

# Node 모듈 설치
echo "📦 Node 모듈 설치 중..."
npm install

# 빌드 실행
echo "🏗️  빌드 중..."
npm run build

# 빌드 완료 확인
if [ -d "dist" ]; then
    echo "✅ 빌드 완료!"
    echo "📂 빌드 파일 위치: $(pwd)/dist"
    echo ""
    echo "📋 다음 단계:"
    echo "1. dist 폴더를 서버의 /usr/share/cockpit/kjbot에 복사"
    echo "2. manifest.json을 같은 위치에 복사"
    echo "3. systemctl restart cockpit"
else
    echo "❌ 빌드 실패!"
    exit 1
fi
