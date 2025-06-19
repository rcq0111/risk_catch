# 🛠️ Risk-Catch 

## 목차  
### 1. 프로잭트 구조
### 2. 업체 등록 API ← (수정 필요)
### 3. 파일 등록 API ← (수정 필요)
### 4. Django 서버 외부 접속 허용 설정
### 5. PostgreSQL 
- PostgreSQL 원격 접속 방법
### 6. 프로잭트 setting 방법 

---
## 프로젝트 구조


    company_project/
        ├── company_project/              ← Django 프로젝트 설정 디렉토리
        │   ├── __init__.py
        │   ├── settings.py               ← 전체 설정 파일 (앱 등록, DB 등)
        │   ├── urls.py                   ← 전역 URL 라우팅
        │   └── wsgi.py / asgi.py
        
        ├── accounts/                     ← 회원가입 / 로그인 / 업체 관련 기능
        │   ├── __init__.py
        │   ├── views.py                  ← 업체 등록, 수정, 삭제, 로그인 처리
        │   ├── urls.py                   ← /api/accounts/ 엔드포인트
        │   └── (models.py)               ← 마이그레이션 없이 쿼리 직접 처리
        
        ├── files/                        ← CSV 업로드 / 분석 기능
        │   ├── __init__.py
        │   ├── views.py                  ← 분석 실행, 결과 확인
        │   ├── urls.py                   ← /api/files/ 엔드포인트
        │   └── (models.py)
        
        ├── inquiry/                      ← 🔹 새로 추가된 문의하기 앱
        │   ├── __init__.py
        │   ├── views.py                  ← 문의 등록 처리 (POST)
        │   ├── urls.py                   ← /api/inquiry/ 엔드포인트
        │   └── (models.py)               ← 마이그레이션 없이 쿼리로 사용
        
        ├── manage.py                     ← Django 명령어 실행 도구
        └── patch.txt                     ← Project 에 설치해야할 목록들 (README.md 마지막 현재 버전 참고바람)

---
# 📦 Django 기반 업체 등록 API

> 사업자 회원 등록 및 업체코드 발급을 위한 Django REST API

---

## ✅ 요청 방식

### [POST] `/api/accounts/signup`

- `Content-Type`: `application/json`

#### 📨 Request Body (예시)

```jsonc
{
  "name": "한글ABC123",             // 상호명 (한글, 영문, 숫자만 허용)
  "ceo_name": "홍길동",             // 대표자 이름
  "manager": "홍길동",              // 관리자
  "email": "test@example.com",     // 이메일 (@.com 형식)
  "phone": "010-1234-5678"         // 전화번호 (010-0000-0000 형식)
}
```
 ✅ 예시 응답
```json
{
  "code": "953091"
}

```
code는 랜덤하게 생성된 6자리 업체코드


## 📌 GET /api/accounts/get-code/

### ✅ 설명
업체 정보를 입력하면 등록된 업체의 `업체코드`를 반환합니다.  
입력된 정보가 정확히 일치해야 조회됩니다.

---

### 🔗 요청 방식

- **Method**: `GET`
- **Endpoint**: `/api/accounts/get-code`
- **Content-Type**: 없음 (쿼리 스트링 방식)

---

### 🧾 요청 파라미터 (쿼리 스트링)

| 파라미터 이름    | 설명              | 예시                     |
|------------|-------------------|--------------------------|
| `email`    | 이메일 주소       | `test@example.com`       |
| `phone`    | 전화번호          | `010-1234-5678`          |

---

### 📤 요청 예시
GET http://localhost:8000/api/accounts/get-code/?name=ABC123상호&ceo_name=홍길동&email=test@example.com&phone=010-1234-5678


> 또는 Postman에서 위 URL을 그대로 입력하거나, Params 탭에 키-값을 넣어도 됩니다.

---

### ✅ 성공 응답 예시 (200 OK)

```json
{
  "code": "953091"
}
```
### ❌ 실패 응답 예시 (404 Not Found)
```json
{
  "error": "해당 업체 없음"
}
```
---
## ✅  이메일 중복 확인

- **URL**: `/api/accounts/duplicate/email`
- **Method**: `POST`
- **설명**: 사업자 이메일 중복 여부 확인

### 📤 Request
```json
{
  "email": "test@example.com"
}
```
### 📥 Response
```jsonc
{
  "duplicate": true // true : 중복
}
```
---
## ✅  전화번호 중복 확인

- **URL**: `/api/accounts/duplicate/phone`
- **Method**: `POST`
- **설명**: 사업자 전화번호 중복 여부 확인

### 📤 Request
```json
{
  "phone": "010-1234-5678"
}
```
### 📥 Response
```jsonc
{
  "duplicate": false // false : 중복 X
}
```
---
## ✅  업체 정보 수정 API

- **URL**: `/api/accounts/update/`
- **Method**: `PUT`

**설명**:
- JWT 토큰에서 업체 idx를 자동 추출해서
- 해당 업체 정보를 수정합니다.
- 수정 항목은 name, ceo_name, email, phone 중 일부 또는 전부 수정 가능.
- email, phone은 정규표현식 검사 진행.

### 📥 요청 Header
```http request
Authorization: Bearer <access_token>
Content-Type: application/json
```
### 📥 요청 Body 예시
- 1개 항목만 수정:
```json
{
  "phone": "010-1234-1234"
}
```
- 2개 항목 수정:
```json
{
  "email": "hello@example.com",
  "phone": "010-2222-3333"
}
```
- 4개 전부 수정:
```json
{
  "name": "새로운상호",
  "ceo_name": "이사장",
  "email": "newceo@example.com",
  "phone": "010-8888-9999"
}
```
---
### ✅ 성공 응답
```json
{
  "message": "업체 정보 수정 완료"
}
```
### ❌ 실패 응답 예시
- 인증 실패 (토큰 없거나 유효하지 않음)
```json
{
  "error": "인증 실패"
}
```
- 정규표현식 위반 (이메일/전화번호)
```json
{
  "error": "유효하지 않은 이메일 형식"
}
```
- 수정 대상 없음
```json
{
  "error": "수정할 항목이 없습니다"
}
```
---
## ✅  업체 정보 삭제 API

- **URL**: `/api/accounts/delete/`
- **Method**: `DELETE`
- **설명**: JWT 토큰에서 idx를 추출해 해당 업체 정보 삭제. 삭제 전 confirm 등의 절차는 없음 (주의 필요).

### 📥 요청 Header
```http request
Authorization: Bearer <access_token>
```
### 📥 요청 Body 예시
```json
{}
```
※ 삭제는 body 필요 없음 (idx는 토큰에서 추출)

---
### ✅ 성공 응답
```json
{
  "message": "업체 정보 삭제 완료"
}
```
### ❌ 실패 응답 예시
- 인증 실패
```json
{
  "error": "인증 실패"
}
```
- 존재하지 않는 업체
```json
{
  "error": "해당 업체 없음"
}
```
---
## ✅  코드번호 인증 및 Access Token 발급

- **URL**: `/api/accounts/signin`
- **Method**: `POST`
- **설명**: 업체 코드로 인증 후 JWT Access Token 발급, 🔒 유효기간 2시간으로 설정

### 📤 Request
```json
{
  "code": "953091"
}
```
### 📥 Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```
- access_token은 이후 인증이 필요한 API 요청 시 Authorization: Bearer <token> 헤더로 사용 가능
---
## ✅  코드로 업체 조회

- **URL**: `/api/accounts/find-by-code/`
- **Method**: `POST`
- **설명**: 6자리 업체 코드로 업체 상호명 조회

### 📤 Request
```json
{
  "code": "953091"
}
```
### 📥 Response (성공)
```json
{
  "name": "한글ABC123",
  "ceo_name": "홍길동",
  "email": "test@example.com",
  "phone": "010-1234-5678"
}
```
### 📥 Response (실패)
```json
{
  "error": "업체 없음"
}
```
---
## 📦 Files API

업체코드를 기반으로 생산량 및 판매량 CSV 파일을 업로드하고,  
해당 데이터를 분석하여 결과를 조회할 수 있는 API입니다.

---

## 📤 [POST] /api/files/register/

### ✅ 설명
- JWT 토큰에 포함된 business_idx를 기반으로 제품 생산/판매 데이터를 서버에 등록합니다.
- type_idx가 1이면 생산량, 2면 판매량을 의미합니다.

### 🔗 요청 방식

- **Method**: POST
- **Endpoint**: `/api/files/register/`
- **Authorization**: `Bearer <access_token>`


### 📥 요청 필드
```json
{
  "type_idx": 1,
  "name": "제품A",
  "number": 500,
  "date": "2023-01-02"
}
```
※ business_idx, date는 서버에서 자동으로 처리됨
- business_idx: JWT 토큰에서 추출
- date: 오늘 날짜로 자동 입력됨 (datetime.date.today())


### ✅ 성공 응답

```json
{
  "message": "제품 등록 완료"
}
```
### ❌ 에러 응답 예시
1. 요청 Body에 필요한 값 누락 시:
```json
{
  "error": "type_idx, name, number는 필수입니다."
}
```
2. JWT 토큰 누락 또는 잘못된 경우:
```json
{
  "error": "유효하지 않은 인증 토큰입니다."
}
```
3. 내부 오류:
```jsonc
{
  "error": "서버 내부 오류",
  "detail": "데이터베이스 연결 실패"  // 예시
}
```
## ✅ 1. 분석 실행 API

### 🔹 [POST] `/api/files/analyze-files/`

> 업로드된 CSV 파일(생산량, 판매량)을 기반으로 분석을 실행합니다.  
> 모델을 돌린 결과로 CSV 파일 2개랑 이미지 파일 4개가 나온다.
---

### 🔗 요청 방식

- Method: `POST`
- Content-Type: `ultipart/form-data`

Form-data 필드:
    
    file1: 생산량 CSV 파일1
    
    file2: 판매량 CSV 파일2
    
    code: 기준 코드 (예: "069931")
---

### 📥 요청 Body 예시


| 필드명     | 타입        | 설명         |
|---------|-----------|------------|
| `file1` | 파일 (File) | 생산량 CSV 파일 |
| `file2` | 파일 (File) | 판매량 CSV 파일 |
```json
{
  "code": "초코소라빵"
}
```
### ✅ 성공 응답 예시 (multipart/mixed 형식)
🔹 응답 헤더
```bash
HTTP/1.1 200 OK
Content-Type: multipart/mixed; boundary=boundary123
```
🔹 응답 바디 (본문)
```http request
--boundary123
Content-Type: text/csv
Content-Disposition: attachment; filename="result1.csv"

제품,수량
A,10
B,20

--boundary123
Content-Type: text/csv
Content-Disposition: attachment; filename="result2.csv"

지역,판매량
서울,100
부산,80

--boundary123
Content-Type: image/png
Content-Disposition: attachment; filename="chart1.png"

(binary PNG data)

--boundary123
Content-Type: image/png
Content-Disposition: attachment; filename="chart2.png"

(binary PNG data)

--boundary123
Content-Type: image/png
Content-Disposition: attachment; filename="chart3.png"

(binary PNG data)

--boundary123
Content-Type: image/png
Content-Disposition: attachment; filename="chart4.png"

(binary PNG data)

--boundary123--
```
### ❌ 실패 응답 예시 (입력값 누락 시)

```json
{
  "error": "서버 오류",
  "detail": "Exception 메시지 출력됨"
}
```

## 📤 model pip install 목록
    numpy
    pandas
    matplotlib
    seaborn
    scikit-learn
    xgboost
    pip install -r patch.txt

    python -m pip install --upgrade pip
    pip install setuptools
    pip install -r patch.txt


---
# 📦 문의하기 API

## ✅ 1. 문의 등록 API

### 🔹 [POST] `/api/inquiry/question/`

> 사용자가 문의를 등록합니다. access_token으로 인증해야 하며, 
> title, message, category_idx를 입력합니다.

---

### 🔗 요청 방식

- Method: `POST`
- Content-Type: `application/json`
- Headers: `Authorization: Bearer {access_token}`

---

### 📥 요청 Body 예시

```json
{
  "title": "납기일 관련 문의",
  "message": "납품 기한을 연장할 수 있을까요?",
  "category_idx": 2
}

```
### ✅ 성공 응답

```json
{
  "message": "문의 등록 완료"
}
```
### ❌ 에러 응답 예시

1. 필수 항목 누락 (400 Bad Request)
```json
{
  "error": "필수 항목 누락"
}
```
2. 유효하지 않은 토큰
```json
{
  "error": "유효하지 않은 토큰"
}
```

---
## ✅ 2. 전체 문의 목록 조회

### 🔹 [GET] `/api/inquiry/question/list/`

> 현재 로그인한 사업자의 전체 문의 목록을 반환합니다.

---

### 🔗 요청 방식

- Method: `GET`
- Headers: `Authorization: Bearer {access_token}`

---

### ✅ 응답 예시

```json
[
  {
    "idx": 1,
    "title": "납기일 관련 문의",
    "category": "배송",
    "created_at": "2025-06-18T14:22:11"
  },
  {
    "idx": 2,
    "title": "결제 관련 문의",
    "category": "결제",
    "created_at": "2025-06-18T15:00:00"
  }
]
```
---
## ✅ 3. 문의 상세 조회

### 🔹 [GET] `/api/inquiry/question/1/`

> 문의 ID(idx)로 문의 상세 내용을 조회합니다.

---

### 🔗 요청 방식

- Method: `GET`
- Headers: `Authorization: Bearer {access_token}`

---

### ✅ 응답 예시

```json
{
  "idx": 1,
  "title": "납기일 관련 문의",
  "message": "납품 기한을 연장할 수 있을까요?",
  "category": "배송",
  "created_at": "2025-06-18T14:22:11"
}
```
---
---
## ✅ 4. 문의 카테고리 목록 조회

### 🔹 [GET] `/api/inquiry/categories/`

> 사용 가능한 문의 카테고리 리스트를 반환합니다.

---

### 🔗 요청 방식

- Method: `GET`
- Headers: `Authorization: Bearer {access_token}`

---

### ✅ 응답 예시

```json
[
  {
    "idx": 1,
    "name": "배송"
  },
  {
    "idx": 2,
    "name": "결제"
  },
  {
    "idx": 3,
    "name": "환불"
  }
]
```

## ✅ 1. Django 서버 외부 접속 허용 설정

🔧 settings.py 수정
```jsonc
ALLOWED_HOSTS = ['*']  # 또는 ['내IP주소', 'localhost']
```

### ✅ 2. 서버 실행 시 0.0.0.0으로 열기
```bash
 python manage.py runserver 0.0.0.0:8000
```
이렇게 해야 다른 컴퓨터에서도 접근 가능해
(기본 127.0.0.1이면 자기 컴퓨터만 가능함)


### ✅ 3. 방화벽/윈도우 보안 허용 확인

> 윈도우 보안 알림이 뜨면 공용/개인 네트워크 허용 체크
> 포트 8000이 방화벽에서 허용되어 있어야 함


### ✅ 4. 접속 주소
```cmd
서버 컴퓨터의 IP 주소 확인 (cmd 창에서): ipconfig

→ 예: 192.168.0.17
→ 내 서버 주소: 메모장에 적어둠
        
다른 컴퓨터 Postman에서는 이렇게 접근:

http://192.168.0.17:8000/api/accounts/register/
```

---
# 📦  PostgreSQL

## ✅ 1. psycopg2 드라이버 설치
```bash
pip install psycopg2-binary
```

## ✅ 2. settings.py에 PostgreSQL 설정
```jsonc
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',           # 데이터베이스 이름
        'USER': 'your_db_user',           # PostgreSQL 사용자
        'PASSWORD': 'your_password',      # 비밀번호
        'HOST': 'localhost',              # 또는 DB 서버 IP
        'PORT': '5432',                   # PostgreSQL 기본 포트
    }
}

```

## ✅ 3. PostgreSQL에서 데이터베이스와 사용자 미리 생성

### psql 터미널 접속 (또는 PgAdmin 사용)
```bash
psql -U postgres
```
    
    sql
    
    -- 데이터베이스 생성
    CREATE DATABASE company_db;
    
    -- 사용자 생성 (필요 시)
    CREATE USER myuser WITH PASSWORD 'mypassword';
    
    -- 권한 부여
    GRANT ALL PRIVILEGES ON DATABASE company_db TO myuser;
        
## ✅ 4. Django 마이그레이션 수행
```bash
python manage.py makemigrations
python manage.py migrate
```

## ✅ 5. (선택) 기존 데이터 옮기기

### 만약 SQLite에서 옮기는 거면:
```bash
python manage.py dumpdata > data.json
```
### PostgreSQL로 바꾼 뒤:
```bash
python manage.py loaddata data.json
```
---
# 📦  PostgreSQL 원격 접속 방법

## ✅ 1. PostgreSQL 설정 변경
### 📍 postgresql.conf 수정
경로 예시 (Ubuntu):
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```
- 버전에 따라 14 대신 13, 15 등 다를 수 있음

### 수정 항목:
```conf
listen_addresses = '*'
```
- 원래는 'localhost'로 되어 있음 → '*'로 바꿔야 외부에서 접속 가능

## ✅ 2. 클라이언트 IP 허용 (pg_hba.conf)
경로 예시:
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```
### 파일 맨 아래에 추가:
```
conf

# 예: 특정 IP 1개만 허용
host    all             all             192.168.0.55/32         md5

# 예: 전체 사설망 허용 (주의)
host    all             all             192.168.0.0/16          md5
```
- 접속하려는 클라이언트(=너가 Django 돌리는 컴퓨터)의 IP 넣어줘야 함
- 192.168.x.x, 10.x.x.x 같은 내부망 IP 가능

## ✅ 3. PostgreSQL 재시작
```bash
sudo systemctl restart postgresql
```
또는 
```bash
sudo service postgresql restart
```
## ✅ 4. 서버 방화벽 열기
### Ubuntu UFW 사용하는 경우:
```bash
sudo ufw allow 5432/tcp
```

## ✅ 5. Django 설정 변경 (settings.py)
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'company_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': '192.168.0.10',  # PostgreSQL 서버의 IP 주소
        'PORT': '5432',
    }
}
```

## ✅ 6. 접속 테스트

```bash
psql -h 192.168.0.10 -U postgres -d company_db
```
또는 PgAdmin, DBeaver, Postman 등에서 시도해봐도 됨.

## ❗ 접속 안 될 때 체크리스트


| 체크 항목                 | 설명                             |
|-----------------------|--------------------------------|
| `🔒 listen_addresses` | 	'*' 또는 서버 IP로 설정됐는지           |
| `🔓 pg_hba.conf`      | 	클라이언트 IP가 허용됐는지               |
| `🔥 방화벽`              | 	서버에서 5432 포트 열렸는지             |
| `🧱 클라우드 사용 시`        | AWS면 보안 그룹에서 5432 허용했는지        |
| `⚠️ IP 확인`            | ipconfig (Windows) 또는 ip a로 클라이언트 IP 확인 |


---
# 🧱 프로잭트 setting 방법

## ✅ 1. 설치 및 세팅
```bash
pip install django djangorestframework pandas
django-admin startproject company_project
cd company_project
python manage.py startapp accounts
python manage.py startapp files
```
settings.py에 앱과 DRF 추가:
```
INSTALLED_APPS = [
    ...
    'rest_framework',
    'accounts',
    'files',
]
```

## ✅ 2. 업체 인증 후 JWT 발급 API (signin)
🔒 JWT 사용을 위해 pyjwt 설치:
```bash
pip install PyJWT

```
---
## 현재 버전
- 확인 방법:
```bash
pip freeze
```
> 아래 항목은 패치해주길 바람

    asgiref==3.8.1
    contourpy==1.3.2
    cycler==0.12.1
    Django==5.2.1
    django-cors-headers==4.7.0
    djangorestframework==3.16.0
    fonttools==4.58.4
    joblib==1.5.1
    kiwisolver==1.4.8
    matplotlib==3.10.3
    numpy==2.2.3
    packaging==25.0
    pandas==2.3.0
    pillow==11.2.1
    psycopg2-binary==2.9.10
    PyJWT==2.10.1
    pyparsing==3.2.3
    python-dateutil==2.9.0.post0
    pytz==2025.2
    seaborn==0.13.2
    setuptools==80.9.0
    six==1.17.0
    sqlparse==0.5.3
    tzdata==2025.2
    xgboost==2.0.3

> scikit-learn 아래방법으로 패치 해야함

```bash
pip install --upgrade --pre scikit-learn --extra-index-url https://pypi.anaconda.org/scikit-learn-nightly/simple
```

---