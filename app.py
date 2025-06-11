from flask import Flask, render_template, request, g, redirect, flash, session, abort, jsonify
import sqlite3 
import os
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

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

@app.cli.command('create-comments-table')
def create_comments_table():
    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        sql_file = app.open_resource('comments.sql')
        db.executescript(sql_file.read().decode('utf-8'))
        db.commit()


@app.route('/')
def home():
    db = get_db_connection()
    posts = db.execute("""SELECT p.id, p.content, p.image, p.created_at, u.username, p.users_id, p.likes
                       FROM posts p JOIN users u ON u.id=p.users_id
                       ORDER BY p.created_at DESC""").fetchall()
    return render_template('home.html', posts=posts)

@app.route('/api/posts')
def api_posts():
    db = get_db_connection()
    posts = db.execute("""SELECT p.id, p.content, p.image, p.created_at, u.username
                       FROM posts p JOIN users u ON u.id=p.users_id
                       ORDER BY p.created_at DESC""").fetchall()
    dict = {}
    for row in posts:
        dict[row['id']] = {'content': row['content'], 
                           'image': 'static/uplaods/' + row['image'],
                            'created_at': row['created_at'],
                             'username': row['username'] }

    return jsonify(dict)

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

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        term = request.form['search_term']
        parts = term.split(':')
        db = get_db_connection()
        authors = []
        posts = [] 
        if parts[0] == 'author':
            pattern = '%' + parts[1] + '%'
            authors = db.execute("SELECT * FROM users WHERE username LIKE ?", (pattern,)).fetchall()
        elif parts[0] == 'caption':
            pattern = '%' + parts[1] + '%'
            posts = db.execute("SELECT * FROM posts WHERE content LIKE ?", (pattern,)).fetchall()
        else:
            flash('Not a proper search term ' + parts[0])

    return render_template('search.html', authors=authors, authors_len=len(authors), 
                           posts=posts, posts_len=len(posts), term=term)


@app.route('/create', methods=['GET', 'POST'])
# restrict to registered users only
def create():
    if g.user is None: 
        flash('You need to login first')
        return redirect('/login')
    if request.method == 'POST':
        caption = request.form['caption']
        image = request.files['image']
        filename = secure_filename(image.filename)
        filename = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + '_' + filename
        image_path = os.path.join('static/uploads', filename)
        image.save(image_path)
        db = get_db_connection()
        db.execute("INSERT INTO posts (content, image, created_at, users_id) VALUES (?, ?, ?, ?)",
                   (caption, filename, datetime.datetime.now(), g.user['id']))
        db.commit()
        return redirect('/')

    return render_template('create.html')

@app.route('/like/<int:pid>')
def like(pid):
    if g.user is None: 
        flash('You need to login first')
        return redirect('/login')
    else:
        db = get_db_connection()
        uid = g.user['id']
        already_liked = db.execute("SELECT * FROM likes WHERE users_id=? AND posts_id=?",
                                   (uid, pid)).fetchone()
        if already_liked:
            db.execute("DELETE FROM likes WHERE users_id=? AND posts_id=?", (uid, pid))
            post = db.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
            likes = post['likes'] - 1
            db.execute("UPDATE posts SET likes=? WHERE id=?", (likes, pid))
            db.commit()
        else:
            db.execute("INSERT INTO likes (users_id, posts_id, created_at) VALUES (?, ?, ?)",
                        (uid, pid, datetime.datetime.now()))
            post = db.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
            likes = post['likes'] + 1
            db.execute("UPDATE posts SET likes=? WHERE id=?", (likes, pid))
            db.commit()
    return redirect('/')


@app.route('/post/<int:pid>')
def view_post(pid):
    db = get_db_connection()
    post = db.execute("""SELECT p.id, p.content, p.image, p.created_at, u.username, p.users_id, p.likes
                       FROM posts p JOIN users u ON u.id=p.users_id
                       WHERE p.id=?""", (pid,)).fetchone()
    comments = db.execute("""SELECT c.id, c.content, u.username  FROM comments c 
                          JOIN users u ON c.users_id=u.id
                          WHERE posts_id=?""", 
                          (pid,)).fetchall()
    return render_template('post.html', post=post, comments=comments)

@app.route('/add/comment', methods=['POST'])
def add_comment():
    if g.user is None: 
        flash('You need to login first')
        return redirect('/login')
    comment = request.form['new_comment']
    pid = request.form['post_id']
    db = get_db_connection()

    db.execute("INSERT INTO comments (content, users_id, posts_id, created_at) VALUES (?,?,?,?)",
               (comment, g.user['id'], pid, datetime.datetime.now()))
    db.commit()
    return redirect('/post/' + str(pid))

@app.route('/user/<int:uid>')
def user_page(uid):
    db = get_db_connection()
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

    if user is None:
        abort(404)
    
    posts = db.execute("SELECT * FROM posts WHERE users_id=? ORDER BY created_at DESC", 
                       (uid,)).fetchall()
    
    return render_template('user.html', user=user, posts=posts)


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
