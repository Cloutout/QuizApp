import os
import random
from datetime import datetime, timedelta

import requests
from flask import Flask, session, jsonify
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'quizdbsqlite.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.secret_key = 'verysecretkey@1'
api_key = '70d41dbe3e61a8b67ab6e296a8d53054'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Integer, default=0)

    def __init__(self, username, email, password, nickname):
        self.username = username
        self.email = email
        self.password = password
        self.nickname = nickname


def get_weather_data(city_name):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric',
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'sehir': data['name'],
            'tarih': datetime.now().strftime('%Y-%m-%d'),
            'gun': datetime.now().strftime('%A'),
            'gun_sicaklik': data['main']['temp_max'],
            'gece_sicaklik': data['main']['temp_min'],
        }
        bugunun_tarihi = datetime.now()
        bugunun_gunu = bugunun_tarihi.strftime('%A')
        gunler = [bugunun_gunu]

        for i in range(1, 3):
            gun = (bugunun_tarihi + timedelta(days=i)).strftime('%A')
            gunler.append(gun)

        weather_data['gunler'] = gunler
        return weather_data
    else:
        return None


def get_three_day_forecast(city_name):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric',
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        forecast = data['list'][:3]
        return forecast
    else:
        return None


@app.route('/')
def ana_sayfa():
    return render_template('index.html', hava_durumu=None)


@app.route('/hava_durumu', methods=['POST'])
def hava_durumu():
    sehir = request.form['sehir']
    hava_durumu = get_weather_data(sehir)

    if hava_durumu:
        hava_durumu['tahminler'] = get_three_day_forecast(sehir)
        return render_template('index.html', hava_durumu=hava_durumu)
    else:
        flash('Hava durumu verileri alınamadı. Lütfen geçerli bir şehir adı girin.', 'danger')
        return redirect(url_for('ana_sayfa'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]

        user = User.query.filter_by(username=uname).first()

        if user is None or not bcrypt.check_password_hash(user.password, passw):
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
            return redirect(url_for("login"))

        session['user_authenticated'] = True
        session['username'] = uname
        session['score'] = user.score

        flash('Başarıyla giriş yapıldı', 'success')
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.pop('user_authenticated', None)
    session.pop('username', None)
    session.pop('score', None)
    flash('Başarıyla çıkış yaptınız', 'success')
    return redirect(url_for("index"))


from flask import request, render_template, redirect, url_for, flash

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']
        passw_confirm = request.form['passw_confirm']  # Get the password confirmation field
        nickname = request.form['nickname']

        # Check if passwords match
        if passw != passw_confirm:
            flash('Şifre ve şifre doğrulama uyuşmuyor.', 'danger')
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(username=uname).first()
        existing_email = User.query.filter_by(email=mail).first()
        existing_nickname = User.query.filter_by(nickname=nickname).first()

        if existing_user or existing_email or existing_nickname:
            flash('Bu kullanıcı adı, e-posta veya takma ad zaten kullanılıyor.', 'danger')
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(passw).decode('utf-8')
        new_user = User(username=uname, email=mail, password=hashed_password, nickname=nickname)
        db.session.add(new_user)
        db.session.commit()

        flash('Başarıyla kayıt oldunuz. Şimdi giriş yapabilirsiniz.', 'success')

        return redirect(url_for("login"))

    return render_template("register.html")


questions = [
        {
            "question_text": "Soru : Bir doğal dil işleme projesi üzerinde çalışıyorsunuz ve metin verileri üzerinde sınıflandırma yapmanız gerekiyor. Hangi derin öğrenme (deep learning) modelini kullanmayı tercih edersiniz ve bu seçiminizi etkileyen faktör nedir?",
            "choices": [" Rekürren Sinir Ağı (RNN)", " Evrişimli Sinir Ağı (CNN)",
                        " Dikkat Mekanizması (Attention Mechanism)", " Derin Doğrusal Model (Deep Linear Model)"],
            "correct_answer": "C"
        },
        {
            "question_text": "Soru : Bir nesne tanıma projesi üzerinde çalışıyorsunuz ve bilgisayar görüşü teknikleri kullanarak nesneleri tanımanız gerekiyor. Hangi derin öğrenme modelini veya mimarisini kullanmayı tercih edersiniz ve bu seçiminizi etkileyen faktör nedir?",
            "choices": [" Convolutional Neural Network (CNN)", " Recurrent Neural Network (RNN)",
                        " Farklı Derin Öğrenme Mimarilerinin Kombine Edilmesi (Ensemble Learning)",
                        " Geleneksel Görüntü İşleme Teknikleri"],
            "correct_answer": "A"
        },
        {
            "question_text": "Soru : Bir doğal dil işleme (NLP) projesi üzerinde çalışıyorsunuz ve metin verileri üzerinde dil modeli geliştirmeniz gerekiyor. Hangi derin öğrenme modelini veya mimarisini kullanmayı tercih edersiniz ve bu seçiminizi etkileyen faktör nedir?",
            "choices": [" Transformer Mimarisi", " Recurrent Neural Network (RNN)",
                        " Convolutional Neural Network (CNN)", " Geleneksel İstatistiksel Modeller"],
            "correct_answer": "A"
        },
        {
            "question_text": "Soru : Bir Python uygulamasında bir yapay zeka (AI) modeli uygulamayı düşünüyorsunuz. Aşağıdaki dört yaklaşımdan hangisi AI modelini uygularken en mantıklı olmayan seçenektir?",
            "choices": [" Modeli sıfırdan kendiniz oluşturmak", " Önceden eğitilmiş bir modeli kullanmak",
                        " AI modeli eğitimini farklı bir programlama dilinde gerçekleştirmek",
                        " Kütüphaneler ve Framework'lerden yararlanmak"],
            "correct_answer": "C"
        }
    ]

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    global current_question_index
    if not session.get('user_authenticated'):
        flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
        return redirect(url_for("login"))

    if 'score' not in session:
        session['score'] = 0

    if 'current_question_index' not in session or request.method == 'POST':

        random.shuffle(questions)
        session['questions'] = questions
        session['current_question_index'] = 0

    if 'current_question_index' in session:
        current_question_index = session['current_question_index']
        if current_question_index < len(session['questions']):
            current_question = session['questions'][current_question_index]
        else:
            current_question = None
    else:
        current_question = None

    if request.method == 'POST':
        user_answer = request.form.get('user_answer')

        if current_question and user_answer == current_question['correct_answer']:
            session['score'] += 10
            flash('Doğru cevap!', 'success')
        else:
            session['score'] -= 5
            flash('Yanlış cevap!', 'danger')

        if current_question_index < len(session['questions']) - 1:
            session['current_question_index'] += 1
        else:
            session.pop('current_question_index', None)
            session.pop('questions', None)

            if 'username' in session:
                db_user = User.query.filter_by(username=session['username']).first()
                db_user.score = session['score']
                db.session.commit()

    return render_template("exam.html", question=current_question, current_score=session['score'])

@app.route('/update_score', methods=['POST'])
def update_score():
    if session.get('user_authenticated'):
        if 'current_question_index' in session:
            current_question_index = session['current_question_index']
            if current_question_index < len(session['questions']):
                user_answer = request.form.get('user_answer')
                correct_answer = session['questions'][current_question_index]['correct_answer']

                if user_answer == correct_answer:
                    session['score'] += 10
                    db_user = User.query.filter_by(username=session['username']).first()
                    if db_user:
                        db_user.score = session['score']
                        db.session.commit()
                    return jsonify({'message': 'Puan başarıyla güncellendi.'})

                else:
                    session['score'] -= 5
                    db_user = User.query.filter_by(username=session['username']).first()
                    if db_user:
                        db_user.score = session['score']
                        db.session.commit()
                    return jsonify({'message': 'Yanlış cevap. Puan eksiltildi.'})

    return jsonify({'message': 'Puan güncelleme işlemi başarısız.'}), 400




def calculate_score(user_answers):
    score = 0
    for index, user_answer in enumerate(user_answers):
        correct_answer = questions[index]["correct_answer"]
        if user_answer == correct_answer:
            score += 10
        else:
            score -= 5
    return score


@app.route("/leaderboard")
def leaderboard():
    if not session.get('user_authenticated'):
        flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
        return redirect(url_for("login"))

    users = User.query.order_by(User.score.desc()).all()

    leaderboard_data = []
    for index, user in enumerate(users, start=1):
        leaderboard_data.append({"index": index, "username": user.username, "score": user.score})

    return render_template("leaderboard.html", leaderboard_data=leaderboard_data)


@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)