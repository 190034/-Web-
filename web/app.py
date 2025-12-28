from flask import (
    Flask, request, render_template,
    redirect, url_for, session, send_from_directory
)
import pyodbc
import os


# Flask 应用初始化

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'


# 文件上传配置

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 数据库连接（SQL Server 2022）
# 使用 Windows 身份验证

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=filedb;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()


# 首页（可选）

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('files'))
    return redirect(url_for('login'))


# 用户注册

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# 用户登录

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['user'] = username
            return redirect(url_for('files'))
        else:
            return "登录失败，请检查用户名或密码"

    return render_template('login.html')


# 用户登出

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# 文件上传

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')

        if file and file.filename:
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)

            cursor.execute(
                "INSERT INTO files (filename, uploader) VALUES (?, ?)",
                (file.filename, session['user'])
            )
            conn.commit()

            return redirect(url_for('files'))

    return render_template('upload.html')


# 文件列表

@app.route('/files')
def files():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT filename FROM files")
    files = cursor.fetchall()

    return render_template('files.html', files=files)


# 文件下载

@app.route('/download/<filename>')
def download(filename):
    if 'user' not in session:
        return redirect(url_for('login'))

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


# 文件删除

@app.route('/delete/<filename>')
def delete(filename):
    if 'user' not in session:
        return redirect(url_for('login'))

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute(
        "DELETE FROM files WHERE filename=?",
        (filename,)
    )
    conn.commit()

    return redirect(url_for('files'))


# 启动 Web 服务

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
