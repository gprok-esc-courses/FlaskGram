from flask import Flask, render_template, request, g, redirect, flash, session
import sqlite3 
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['DATABASE'] = 'flaskgram.db'


def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.cli.command('create-db')
def create_db():
    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        sql_file = app.open_resource('tables.sql')
        db.executescript(sql_file.read().decode('utf-8'))
        db.commit()


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        error = None
        username = request.form['username']
        password = request.form['password']
        description = request.form['description']
        db = get_db_connection()
        result = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if result is not None:
            error = "Username already registered"
        else:
            db.execute("INSERT INTO users (username, password, description, created_at) VALUES (?,?,?,?)",
                       (username, generate_password_hash(password), description, datetime.datetime.now()))
            db.commit()
            return redirect('/login')
        flash(error)
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        error = None
        username = request.form['username']
        password = request.form['password']
        db = get_db_connection()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user is None:
            error = "Invalid username"
        elif not check_password_hash(user['password'], password):
            error = "Wrong password"
        else: 
            session.clear()
            session['user_id'] = user['id']
            return redirect('/')
        
        flash(error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None 
    else:
        db = get_db_connection()
        g.user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


if __name__ == '__main__':
    app.run(debug=True)
