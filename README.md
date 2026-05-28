# 🚀 Flask & SQLite 기반 로케이션 로그 탑재 Todo 서비스

본 프로젝트는 사용자가 할 일(Todo) 목록을 관리할 수 있는 REST API 기반의 웹 애플리케이션입니다. Flask(백엔드)와 jQuery AJAX(프론트엔드)를 연동하여 비동기식 CRUD를 지원하며, 내부에서 일어나는 모든 SQL 실행 구문과 발생 시간을 원격 또는 로컬 MySQL 서버에 실시간으로 기록(Logging)하는 데이터 흐름을 갖추고 있습니다.

---

## 🛠️ 1. 기술 스택 및 환경 요구사항

- **Backend**: Python 3.12 / Flask 3.0.3
- **Frontend**: HTML5, CSS3, jQuery 3.6.0 (CDN)
- **Database**: 
  - **Main**: SQLite (로컬 가볍고 독립적인 파일 기반 `todo.db`)
  - **Log**: MySQL (`mysql-connector-python` 드라이버 사용)

---

## 🚀 2. 실행 방법 (Quick Start)

### 1) 필수 패키지 설치
프로젝트 폴더 내 터미널을 열고 요구사항에 명시된 필수 외부 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt

### 2) 데이터베이스 설정 확인(app.py)
app.py 내부 상단의 MYSQL_CONFIG 상수를 확인하여 접속 대상 MySQL 인스턴스의 계정 및 패키지 사양과 일치시킵니다.

Python
MYSQL_CONFIG = {
    'host': '127.0.0.1',        # 가상 서버 이전 시 public IP로 변경 가능
    'user': 'user',
    'password': 'password',  # 개인 DB 패스워드로 매칭
}


## 🔐 3. 기본 제공 테스트 계정 (관리자 정보)
아이디(uid): admin
비밀번호(upwd): 1234
이름 (uname): 관리자

## 🔌 4. API 엔드포인트 명세서 (REST API)

모든 할 일 관리 기능은 RESTful API 규칙을 따르며, 상태 코드 및 JSON 데이터 포맷을 통해 프론트엔드와 비동기(AJAX) 통신을 수행합니다.

### [1] 로그인 인증 처리
- **HTTP Method**: POST
- **Endpoint**: `/login`
- **설명**: 사용자의 세션 로그인을 검증하고 인증을 처리합니다.
- **요청 데이터 (Form Data)**:
  - `username`: 사용자 아이디
  - `password`: 사용자 비밀번호
- **반환 결과**: 로그인 성공 시 메인 페이지(`/`)로 리다이렉트, 실패 시 경고창 알림 후 이전 페이지 롤백 스크립트 반환.

---

### [2] Todo 목록 조회 (Read)
- **HTTP Method**: GET
- **Endpoint**: `/todos`
- **설명**: 현재 세션에 로그인된 사용자의 전체 할 일 리스트를 최신순으로 조회합니다.
- **요청 데이터**: 없음 (None)
- **반환 데이터 (JSON - 200 OK)**:
  ```json
  [
    {
      "id": 1,
      "title": "할 일 내용",
      "uid": "admin",
      "completed": false,
      "datetime": "2026-05-28 11:00:00"
    }
  ]

### [3] 새로운 할 일 추가 (Create)
- **HTTP Method**: POST
- **Endpoint**: `/todos`
- **설명**: 새로운 할 일 항목을 데이터베이스에 등록합니다. 기본 완료 상태(completed)는 false(0)로 지정됩니다.
- **요청 데이터**: 
  ```json
{
  "title": "새로 추가할 할 일 내용"
}
- **반환 데이터 (JSON - 201 Created):
  ```json
{
  "id": 2,
  "title": "새로 추가할 할 일 내용",
  "uid": "admin",
  "completed": false,
  "datetime": "2026-05-28 11:05:00"
}

### [4] 할 일 내용 수정 및 완료 토글 (Update)
- **HTTP Method**: PUT
- **Endpoint**: `/todos/<int:todo_id>`
- **설명**: 특정 ID를 가진 할 일의 제목을 수정하거나 완료 상태 변동 여부(true/false)를 토글하여 업데이트합니다.
- **요청 데이터**: 
  ```json
{
  "title": "수정할 할 일 내용",
  "completed": true
}
- **반환 데이터 (JSON - 200 OK):
  ```json
{
  "id": 2,
  "title": "수정할 할 일 내용",
  "completed": true
}


### [5] 특정 할 일 내역 삭제 (Delete)
- **HTTP Method**: DELETE
- **Endpoint**: `/todos/<int:todo_id>`
- **설명**: 사용자가 선택한 특정 ID의 할 일 데이터를 SQLite 데이터베이스에서 영구적으로 삭제합니다.
- **요청 데이터**: 없음(None)
- **반환 데이터 (JSON - 200 OK):
  ```json
{
  "result": "success"
}

🧪 5. API 테스트 결과 및 확인 방법 (Postman / 브라우저)
💡 방법: 브라우저 UI를 이용한 실시간 클라이언트 확인
크롬 등 브라우저를 열고 http://127.0.0.1:5000/ 에 접속합니다.

관리자 계정(admin / 1234)으로 로그인을 수행합니다.

메인 대시보드 화면에서 할 일을 추가, 완료, 수정, 삭제해 보며 상단 필터 바(전체 보기, 진행 중, 완료됨)를 클릭해 리스트가 비동기(AJAX)로 유기적으로 바뀐다는 것을 직접 확인합니다.

🗄️ 6. MySQL 원격 로그 적재 현황 검증
백엔드 실행 중 내부 SQLite 트랜잭션이 활성화될 때마다 외부 MySQL 서버 인스턴스의 테이블에는 요구사항 명세 규칙(첫 단어 대문자 파싱 및 완성형 매핑 구문)에 입각하여 다음과 같이 안전하게 영구 로그가 기록됩니다.

데이터 적재 확인용 SQL 규칙
SQL
USE todo_log_db;
SELECT * FROM query_logs ORDER BY idx DESC;
