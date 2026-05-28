import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'todo_project_secret_key_2026'
DATABASE = 'todo.db'

# --- 🌐 MySQL 접속 설정 (가상 서버 이전 시 여기만 수정) ---
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'user',
    'password': 'password',
}
MYSQL_DB_NAME = 'todo_log_db'


# --- 📝 MySQL 쿼리 로그 기록 함수 ---
def log_to_mysql(sql_query, query_args=None):
    try:
        clean_sql = " ".join(sql_query.split()).strip()
        first_word = clean_sql.split()[0].upper() if clean_sql else 'UNKNOWN'if clean_sql else 'UNKNOWN'
        
        full_sql = clean_sql
        if query_args:
            for arg in query_args:
                full_sql = full_sql.replace('?', f"'{str(arg)}'", 1)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 데이터베이스 지정하여 연결
        config = MYSQL_CONFIG.copy()
        config['database'] = MYSQL_DB_NAME
        
        mysql_conn = mysql.connector.connect(**config)
        mysql_conn.autocommit = True 
        
        with mysql_conn.cursor() as cursor:
            insert_query = "INSERT INTO query_logs (type, sql_text, datetime) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (first_word, full_sql, now))
            
        mysql_conn.close()
    except Exception as e:
        print(f"[MySQL Log Error] 로그 기록 실패: {e}")


# --- 🛠️ SQLite 데이터베이스 연결 관리 ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# --- 🗄️ SQLite & MySQL DDL 자동 생성 및 초기화 ---
def init_db():
    print("🚀 데이터베이스 자동 초기화 및 DDL 스크립트를 실행합니다...")
    
    # 1️⃣ [MySQL DDL] 데이터베이스 및 로그 테이블 자동 생성
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_conn.autocommit = True
        cursor = mysql_conn.cursor()
        
        # 데이터베이스 스키마 생성
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {MYSQL_DB_NAME}")
        
        # 로그 테이블 생성 DDL
        mysql_ddl = '''
            CREATE TABLE IF NOT EXISTS query_logs (
                idx INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(10) NOT NULL,
                sql_text TEXT NOT NULL,
                datetime DATETIME NOT NULL
            )
        '''
        cursor.execute(mysql_ddl)
        
        cursor.close()
        mysql_conn.close()
        print("✅ MySQL 데이터베이스 및 로그 테이블 초기화 완료.")
    except Exception as e:
        print(f"❌ MySQL DDL 초기화 실패 (서버가 켜져있는지 확인하세요): {e}")

    # 2️⃣ [SQLite DDL] 서비스 테이블 및 기본 관리자 계정 생성
    with app.app_context():
        db = get_db()
        
        # 회원 테이블 DDL
        member_ddl = '''
            CREATE TABLE IF NOT EXISTS member (
                idx INTEGER PRIMARY KEY AUTOINCREMENT,
                uname TEXT NOT NULL,
                uid TEXT UNIQUE NOT NULL,
                upwd TEXT NOT NULL,
                datetime TEXT NOT NULL
            )
        '''
        db.execute(member_ddl)
        log_to_mysql(member_ddl)

        # 할 일 목록 테이블 DDL
        todolist_ddl = '''
            CREATE TABLE IF NOT EXISTS todolist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                uid TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                datetime TEXT NOT NULL,
                FOREIGN KEY(uid) REFERENCES member(uid)
            )
        '''
        db.execute(todolist_ddl)
        log_to_mysql(todolist_ddl)
        
        # 관리자 기본 계정 자동 등록 데이터 생성
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_check_sql = 'SELECT * FROM member WHERE uid = ?'
        admin_user = db.execute(user_check_sql, ('admin',)).fetchone()
        log_to_mysql(user_check_sql, ('admin',))

        if not admin_user:
            ins_admin_sql = 'INSERT INTO member (uname, uid, upwd, datetime) VALUES (?, ?, ?, ?)'
            db.execute(ins_admin_sql, ('관리자', 'admin', '1234', now))
            log_to_mysql(ins_admin_sql, ('관리자', 'admin', '1234', now))
        
        db.commit()
        print("✅ SQLite 데이터베이스 및 기본 계정 세팅 완료.\n")


# --- 🖥️ 화면 렌더링 라우트 영역 ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page(): return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_action():
    uid, upwd = request.form.get('username'), request.form.get('password')
    db = get_db()
    
    query = 'SELECT * FROM member WHERE uid = ? AND upwd = ?'
    user = db.execute(query, (uid, upwd)).fetchone()
    log_to_mysql(query, (uid, upwd))
    
    if user:
        session['user_id'], session['username'] = user['uid'], user['uname']
        return redirect(url_for('index'))
    return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# --- 📝 Todo RESTful API 영역 (조회, 추가, 수정, 삭제) ---
@app.route('/todos', methods=['GET'])
def get_todos():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    query = 'SELECT * FROM todolist WHERE uid = ? ORDER BY id DESC'
    rows = db.execute(query, (session['user_id'],)).fetchall()
    log_to_mysql(query, (session['user_id'],))
    
    todos_list = [{'id': r['id'], 'title': r['title'], 'uid': r['uid'], 'completed': bool(r['completed']), 'datetime': r['datetime']} for r in rows]
    return jsonify(todos_list), 200

@app.route('/todos', methods=['POST'])
def create_todo():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data or 'title' not in data: return jsonify({'error': 'Bad Request'}), 400
    
    title, uid = data['title'], session['user_id']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    db = get_db()
    query = 'INSERT INTO todolist (title, uid, completed, datetime) VALUES (?, ?, 0, ?)'
    cursor = db.execute(query, (title, uid, now))
    db.commit()
    log_to_mysql(query, (title, uid, now))
    
    return jsonify({'id': cursor.lastrowid, 'title': title, 'uid': uid, 'completed': False, 'datetime': now}), 201

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    db = get_db()
    
    sel_query = 'SELECT * FROM todolist WHERE id = ? AND uid = ?'
    todo = db.execute(sel_query, (todo_id, session['user_id'])).fetchone()
    log_to_mysql(sel_query, (todo_id, session['user_id']))
    
    if not todo: return jsonify({'error': 'Not Found'}), 404
        
    new_title = data.get('title', todo['title'])
    new_completed = 1 if data.get('completed', todo['completed']) else 0
        
    upd_query = 'UPDATE todolist SET title = ?, completed = ? WHERE id = ?'
    db.execute(upd_query, (new_title, new_completed, todo_id))
    db.commit()
    log_to_mysql(upd_query, (new_title, new_completed, todo_id))
    
    return jsonify({'id': todo_id, 'title': new_title, 'completed': bool(new_completed)}), 200

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    
    sel_query = 'SELECT * FROM todolist WHERE id = ? AND uid = ?'
    todo = db.execute(sel_query, (todo_id, session['user_id'])).fetchone()
    log_to_mysql(sel_query, (todo_id, session['user_id']))
    
    if not todo: return jsonify({'error': 'Not Found'}), 404
        
    del_query = 'DELETE FROM todolist WHERE id = ?'
    db.execute(del_query, (todo_id,))
    db.commit()
    log_to_mysql(del_query, (todo_id,))
    
    return jsonify({'result': 'success'}), 200


if __name__ == '__main__':
    init_db()  
    app.run(debug=True)