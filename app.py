from flask import Flask, render_template, redirect, request, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'ваш_супер_секретний_ключ'
app.config['DATABASE'] = 'staem.db'

GAMES = {
    "csgo": {"name": "CS:GO", "price": 0, "desc": "Безкоштовний шутер", "tag": "free"},
    "cs2": {"name": "CS2", "price": 599, "desc": "Покращена версія", "tag": "premium"},
    "dota2": {"name": "Dota 2", "price": 0, "desc": "MOBA гра", "tag": "free"},
    "tf2": {"name": "Team Fortress 2", "price": 0, "desc": "Класовий шутер", "tag": "free"}
}

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance INTEGER DEFAULT 2000
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS user_games (
                user_id INTEGER,
                game_id TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        try:
            db.execute(
                'INSERT INTO users (username, password, balance) VALUES (?, ?, ?)',
                ['admin', generate_password_hash('admin123'), 10000]
            )
            db.commit()
        except sqlite3.IntegrityError:
            pass

init_db()

@app.route('/')
def store():
    db = get_db()
    user_games = []
    user = None
    
    if 'user_id' in session:
        user = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']]).fetchone()
        if user:
            games_data = db.execute('SELECT game_id FROM user_games WHERE user_id = ?', [user['id']]).fetchall()
            user_games = [game['game_id'] for game in games_data]
    
    return render_template('store.html', 
                        games=GAMES,
                        user_games=user_games,
                        user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', [request.form['username']]).fetchone()
        
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            return redirect(url_for('store'))
        flash('Невірний логін або пароль!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        try:
            db = get_db()
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, password])
            db.commit()
            flash('Реєстрація успішна!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ім\'я вже заняте!', 'danger')
    return render_template('register.html')

@app.route('/buy/<game_id>')
def buy(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']]).fetchone()
    game = GAMES.get(game_id)
    
    if not game:
        flash('Гра не знайдена!', 'danger')
        return redirect(url_for('store'))
    
    try:
        if game['price'] == 0:
            db.execute('INSERT INTO user_games (user_id, game_id) VALUES (?, ?)', [user['id'], game_id])
            flash(f'Гра "{game["name"]}" додана!', 'success')
        elif user['balance'] >= game['price']:
            db.execute('UPDATE users SET balance = balance - ? WHERE id = ?', [game['price'], user['id']])
            db.execute('INSERT INTO user_games (user_id, game_id) VALUES (?, ?)', [user['id'], game_id])
            flash(f'Ви купили {game["name"]}!', 'success')
        else:
            flash('Недостатньо коштів!', 'danger')
        db.commit()
    except sqlite3.Error:
        flash('Помилка бази даних!', 'danger')
    
    return redirect(url_for('store'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']]).fetchone()
    games = db.execute('SELECT game_id FROM user_games WHERE user_id = ?', [user['id']]).fetchall()
    user_games = [GAMES[game['game_id']] for game in games if game['game_id'] in GAMES]
    
    return render_template('profile.html', 
                         user=user, 
                         games=user_games)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('store'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)