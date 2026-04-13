# WithBot 배포 가이드 (Fly.io)

## 사전 준비

### 1. Fly.io CLI 설치 (Mac)
```bash
brew install flyctl
```

### 2. Fly.io 가입 & 로그인
```bash
fly auth signup   # 처음이면 가입
fly auth login    # 이미 계정 있으면 로그인
```

## 배포

### 3. 프로젝트 폴더로 이동
```bash
cd withbot
```

### 4. 앱 생성 + 볼륨 생성 + 시크릿 설정
```bash
# 앱 생성 (이름이 중복이면 다른 이름 사용)
fly apps create withbot-sns

# 데이터 영구 저장용 볼륨 생성 (도쿄 리전)
fly volumes create withbot_data --size 1 --region nrt

# 시크릿 키 설정 (프로덕션용 랜덤 키)
fly secrets set SECRET_KEY=$(openssl rand -hex 32)
```

### 5. 배포
```bash
fly deploy
```

첫 배포는 Docker 빌드가 있어서 3~5분 걸립니다.

### 6. 접속 확인
```bash
fly open
```

브라우저에서 `https://withbot-sns.fly.dev` 로 접속됩니다.

## 배포 후 확인

### API 동작 확인
```bash
curl https://withbot-sns.fly.dev/ai-guide
```

### 로그 확인
```bash
fly logs
```

### 앱 상태 확인
```bash
fly status
```

## 운영

### 앱 재시작
```bash
fly apps restart withbot-sns
```

### 코드 수정 후 재배포
```bash
fly deploy
```

### 환경변수 추가/변경
```bash
fly secrets set GOOGLE_CLIENT_ID=your-client-id
fly secrets set GOOGLE_CLIENT_SECRET=your-client-secret
```

### DB 백업 (SSH로 접속)
```bash
fly ssh console
cp /data/withbot.db /data/withbot_backup_$(date +%Y%m%d).db
```

## 도메인 연결 (선택)

커스텀 도메인을 연결하려면:
```bash
fly certs create withbot.yourdomain.com
```
이후 DNS에서 CNAME을 withbot-sns.fly.dev로 설정

## 비용

Fly.io 무료 티어 포함 사항:
- VM 3대 (공유 CPU, 256MB RAM)
- 3GB 영구 볼륨
- 160GB 아웃바운드 트래픽/월
- 자동 HTTPS

2명이 사용하는 수준이면 무료 범위 내에서 충분합니다.
