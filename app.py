from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///games.db'
app.config['SECRET_KEY'] = 'secret123'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))
    cash = db.Column(db.Float, default=100.00)  # Стартовые $100

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))  # Исправлено на title вместо name
    price = db.Column(db.Float)

class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    game_id = db.Column(db.Integer)

# Создаем базу и добавляем игры
with app.app_context():
    db.create_all()
    if Game.query.count() == 0:
        default_games = [
            {"title": "Cyberpunk 2077", "price": 59.99},
            {"title": "Elden Ring", "price": 49.99},
            {"title": "GTA V", "price": 29.99},
            {"title": "The Witcher 3", "price": 19.99},
            {"title": "Stray", "price": 24.99},
            {"title": "RDR 2", "price": 39.99},
            {"title": "CS2", "price": 0},
            {"title": "Dota 2", "price": 0},
            {"title": "Hogwarts Legacy", "price": 59.99}
        ]
        for game in default_games:
            db.session.add(Game(title=game['title'], price=game['price']))
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if 'login' in request.form:
                user = User.query.filter_by(username=username).first()
                if user and check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    return redirect('/store')
                flash('Неверный логин/пароль')
            
            elif 'register' in request.form:
                if not User.query.filter_by(username=username).first():
                    user = User(
                        username=username,
                        password=generate_password_hash(password),
                        cash=100.00
                    )
                    db.session.add(user)
                    db.session.commit()
                    session['user_id'] = user.id
                    return redirect('/store')
                flash('Логин занят')
        
        return render_template('auth.html')
    return redirect('/store')

@app.route('/store', methods=['GET', 'POST'])
def store():
    if 'user_id' not in session:
        return redirect('/')
    
    user = User.query.get(session['user_id'])
    games = Game.query.all()
    my_games = [g.game_id for g in Library.query.filter_by(user_id=user.id).all()]

    if request.method == 'POST':
        if 'add_cash' in request.form:
            user.cash += float(request.form['amount'])
            db.session.commit()
        
        elif 'buy' in request.form:
            game_id = int(request.form['game_id'])
            game = Game.query.get(game_id)
            
            if game_id in my_games:
                flash('Уже куплено')
            elif user.cash < game.price:
                flash('Не хватает денег')
            else:
                user.cash -= game.price
                db.session.add(Library(user_id=user.id, game_id=game_id))
                db.session.commit()
                flash(f'Куплено: {game.title}')
    
    return render_template('store.html', 
                         user=user, 
                         games=games,
                         my_games=my_games)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)