from datetime import datetime
from math import e
from SportyBuddies import app
from flask import Response, jsonify, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
import mysql.connector
from datetime import datetime
from flask import request


db = mysql.connector.connect(
    host="localhost", user="root", passwd="", database="sportybuddies"
)
app.secret_key = "secret"

login_manager = LoginManager()
login_manager.init_app(app)


class User:
    def __init__(self, user_id):
        self.id = user_id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    cursor = db.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    if user:
        return User(user[0])
    return None


@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return redirect(request.url)
    photo = request.files["photo"]

    if photo.filename == "":
        return redirect(request.url)

    if photo:
        photo_data = photo.read()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET photo=%s WHERE user_id=%s", (photo_data, current_user.id)
        )
        db.commit()
        cursor.close()

    return redirect(url_for("user_profile"))


@app.route("/user_profile")
def user_profile():
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute("SELECT name FROM users WHERE user_id = %s", (current_user.id,))
    username = cursor.fetchone()[0]
    
    cursor.execute("SELECT age FROM users WHERE user_id = %s", (current_user.id,))
    user_age = cursor.fetchone()[0]
    
    cursor.execute("SELECT gender FROM users WHERE user_id = %s", (current_user.id,))
    user_gender = cursor.fetchone()[0]

    cursor.execute("SELECT status FROM users WHERE user_id = %s", (current_user.id,))
    user_status = cursor.fetchone()[0]

    cursor.execute(
        "SELECT sport_id FROM user_sports WHERE user_id = %s", (current_user.id,)
    )
    results = cursor.fetchall()
    user_sports = [result[0] if result[0] > 0 else 0 for result in results[:15]]
    sports = [0] * 15
    for i in user_sports:
        if i > 0:
            sports[i - 1] = i

    return render_template(
        "user_profile.html",
        result=username,
        user_sports=sports,
          age = user_age,
          gender = user_gender,
          status = user_status
    )

@app.route("/mainpagelogged")
def mainpagelogged():
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute("SELECT name FROM users WHERE user_id = %s", (current_user.id,))
    username = cursor.fetchone()[0]
    
    cursor.execute("SELECT age FROM users WHERE user_id = %s", (current_user.id,))
    user_age = cursor.fetchone()[0]
    
    cursor.execute("SELECT sports.iconlink FROM sports JOIN user_sports ON sports.sport_id = user_sports.sport_id WHERE user_sports.user_id = %s", (current_user.id,))
    sport_id = cursor.fetchall()
    

    return render_template(
        "mainpagelogged.html",
        result=username,
        age = user_age,
        sport = sport_id,
    )

@app.route("/get_user_photo")
@login_required
def get_user_photo():
    cursor = db.cursor()
    cursor.execute("SELECT photo FROM users WHERE user_id = %s", (current_user.id,))
    photo_data = cursor.fetchone()[0]
    cursor.close()

    return Response(photo_data, content_type="image/jpeg")


@app.route("/update_user_sports", methods=["POST"])
def update_user_sports():
    if request.method == "POST":
        sport_ids = request.form.getlist("sportIds[]")
        intensity = request.form.get("intensity")

        cursor = db.cursor()

        # Usuwanie istniej¹cych wpisów dla danego u¿ytkownika
        cursor.execute("DELETE FROM user_sports WHERE user_id = %s", (current_user.id,))

        # Dodawanie nowych wpisów
        for sport_id in sport_ids:
            cursor.execute(
                "INSERT INTO user_sports (user_id, sport_id, intensity) VALUES (%s, %s, %s)",
                (current_user.id, sport_id, intensity),
            )

        db.commit()
        cursor.close()
        return jsonify({"status": "success"})
@app.route("/update_user_status", methods=["POST"])
@login_required
def update_user_status():
    if request.method == "POST":
        status = request.form.get("status")

        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET status=%s WHERE user_id=%s", (status, current_user.id)
        )
        db.commit()
        cursor.close()

        return jsonify({"status": "success"})



@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user_profile"))

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        age = request.form["age"]
        gender = request.form.get("gender")
        description = request.form["description"]
        password = request.form["password"]

        cursor = db.cursor()
        
        # check if username or email already exists
        cursor.execute("SELECT user_id FROM users WHERE name = %s", (username,))
        user_id = cursor.fetchone()
        if user_id:
            error_message = "Nazwa uzytkownika jest juz zajeta."
            return render_template("register.html", error=error_message)
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user_id = cursor.fetchone()
        if user_id:
            error_message = "Email jest juz zajety."
            return render_template("register.html", error=error_message)


        cursor.execute(
            "INSERT INTO users (email, password, name, age, gender, info) VALUES (%s, %s, %s, %s, %s, %s)",
            (email, password, username, age, gender, description),
        )
        db.commit()
        cursor.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user_profile"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT user_id FROM users WHERE name = %s AND password = %s",
            (username, password),
        )
        user_id = cursor.fetchone()
        cursor.close()
        if user_id:
            user = User(user_id[0])
            login_user(user)
            return redirect(url_for("user_profile"))
        
        else:
            error_message = "Nieprawidlowa nazwa uzytkownika lub haslo."
            return render_template("login.html", error=error_message)

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/logged")
def logged():
    return render_template("mainpagelogged.html", title="Home Page", year=datetime.now().year)

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html", title="Home Page", year=datetime.now().year)

@app.route("/contact")
def contact():
    return render_template(
        "contact.html",
        title="Contact",
        year=datetime.now().year,
        message="Your contact page.",
    )


@app.route("/about")
def about():
    return render_template(
        "about.html",
        title="About",
        year=datetime.now().year,
        message="Your application description page.",
    )

@app.route("/bug_report")
def bug_report():
    
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))
    return render_template(
        "bug_report.html",
        title="Zgloszenie Problemow",
        year=datetime.now().year,
        message="Your application description page.",
    )
@app.route("/submit_report", methods=["POST"])
@login_required
def submit_report():

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        user_id = current_user.id
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO reports (user_id, date, title, `desc`) VALUES (%s, %s, %s, %s)",
            (user_id, date, title, description),
        )
        db.commit()
        cursor.close()

        # Mo¿esz dodaæ dowolny kod obs³ugi po zapisaniu zg³oszenia, np. przekierowanie na inn¹ stronê
        return redirect(url_for("home"))

