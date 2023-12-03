from datetime import datetime
from flask_socketio import SocketIO, emit
from math import e
from SportyBuddies import app
from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import Response, jsonify, render_template, request, redirect, url_for,flash
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from io import BytesIO
from PIL import Image
import secrets
import requests

######### MAIL ##########

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 465  # Port for SMTP (SSL)
app.config['MAIL_USE_SSL'] = True  
app.config['MAIL_USERNAME'] = 'infosportybuddies@gmail.com'
app.config['MAIL_PASSWORD'] = 'htysutkbluguliwy'

mail = Mail(app)


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
        username=username,
        user_sports=sports,
        age = user_age,
        gender = user_gender,
        status = user_status,
        current_user_id=current_user.id,
    )

@app.route("/update_user_location", methods=["POST"])
def update_user_location():
    
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET latitude = %s, longitude = %s where user_id = %s", (latitude, longitude, current_user.id)
    )
    db.commit()
    

    
@app.route("/mainpagelogged")
def mainpagelogged():
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    current_username, current_age, current_sport_icons = get_user_info_for_mainpagelogged(current_user.id)
    if len(current_sport_icons) == 0:
        return redirect(url_for("user_profile"))
    matched_user_id= get_matched_user_id()
    matched_username,matched_age, matched_sport_icons = get_user_info_for_mainpagelogged(matched_user_id)
    
    return render_template(
        "mainpagelogged.html",
        current_user_id=current_user.id,
        current_username=current_username,
        current_age = current_age,
        current_sport_icons = current_sport_icons,
        matched_username=matched_username,
        matched_age = matched_age,
        matched_sport_icons = matched_sport_icons,
        matched_user_id=matched_user_id
    )

def get_matched_user_id():
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM user_sports WHERE sport_id = (SELECT sport_id FROM user_sports WHERE user_id=%s limit 1) limit 1;", (current_user.id,))
    user_id = cursor.fetchone()[0]
    
    return user_id

def get_user_info_for_mainpagelogged(user_id):
    
    cursor = db.cursor()
    
    cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
    username = cursor.fetchone()[0]
    
    cursor.execute("SELECT age FROM users WHERE user_id = %s", (user_id,))
    user_age = cursor.fetchone()[0]
    
    cursor.execute("SELECT sports.iconlink FROM sports JOIN user_sports ON sports.sport_id = user_sports.sport_id WHERE user_sports.user_id = %s", (user_id,))
    sport_id = cursor.fetchall()
    
    return username, user_age, sport_id
    


@app.route("/get_user_photo/<int:user_id>")
@login_required
def get_user_photo(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT photo FROM users WHERE user_id = %s", (user_id,))
    photo_data = cursor.fetchone()[0]
    cursor.close()

    return Response(photo_data, content_type="image/jpeg")


@app.route("/update_user_sports_intensity", methods=["POST"])
def update_user_sports_intensity():
        cursor = db.cursor()
        sport_id = request.form.get("sportId")
        intensity = request.form.get("intensity")

        cursor.execute(
                "UPDATE user_sports SET intensity=%s WHERE user_id=%s AND sport_id=%s",
                (intensity,current_user.id,sport_id),
            )

        db.commit()
        cursor.close()
        return jsonify({"status": "success"})


@app.route("/update_user_sports", methods=["POST"])
def update_user_sports():
    if request.method == "POST":
        is_checked = request.form.get("isChecked")
        sport_id = request.form.get("sportId")

        cursor = db.cursor()

        if is_checked == "true":
            cursor.execute(
                "INSERT INTO user_sports (user_id,sport_id) VALUES (%s,%s)",
                (current_user.id, sport_id),
            )
        else:
            cursor.execute(
                "DELETE FROM user_sports WHERE user_id = %s AND sport_id=%s",
                (current_user.id, sport_id),
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


        
        photo_url = "https://static.vecteezy.com/system/resources/thumbnails/009/734/564/small/default-avatar-profile-icon-of-social-media-user-vector.jpg"
        response = requests.get(photo_url)
            # Konwertuj zdjęcie do formatu BLOB
        image = Image.open(BytesIO(response.content))
        blob_data = BytesIO()
        image.save(blob_data, format="JPEG")
        photo_blob = blob_data.getvalue()

        cursor.execute(
            "INSERT INTO users (email, password, name, age, gender, info, photo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (email, password, username, age, gender, description, photo_blob),
        )
        db.commit()
        cursor.close()

        msg = Message("Pomyślna rejestracja", sender="your_email@example.com", recipients=[email])
        msg.body = "Dziękujemy za rejestrację w SportyBuddies! Teraz możesz zalogować się na swoje konto."
        mail.send(msg)
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

class Messages:
    def __init__(self, id, sender_id, sender_name, receiver_id, content, timestamp):
        self.id = id
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp
        
socketio = SocketIO(app)
        
@app.route("/chat", defaults={'receiver_id': None}, methods=['GET', 'POST'])
@app.route("/chat/<int:receiver_id>", methods=['GET', 'POST'])
def chat(receiver_id):
    if not current_user.is_authenticated:
        return redirect(url_for("mainpagelogged"))

    users = None
    messages = None

    with mysql.connector.connect(host="localhost", user="root", passwd="", database="sportybuddies") as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT user_id, name FROM users WHERE user_id != %s", (current_user.id,))
            users = cursor.fetchall()

            if receiver_id is not None:
                try:
                    if request.method == 'POST':
                        content = request.form.get('content')
                        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)",
                            (current_user.id, receiver_id, content, timestamp)
                        )
                        db.commit()

                    cursor.execute("""
                    SELECT messages.id, messages.sender_id, users.name AS sender_name, messages.receiver_id, messages.content, messages.timestamp
                    FROM messages
                    JOIN users ON messages.sender_id = users.user_id
                    WHERE (messages.sender_id = %s AND messages.receiver_id = %s) OR (messages.sender_id = %s AND messages.receiver_id = %s)
                    ORDER BY messages.timestamp

                    """,(current_user.id, receiver_id, receiver_id, current_user.id))
                    messages = [Messages(**msg) for msg in cursor.fetchall()]

                finally:
                    cursor.close()

    messages = messages if messages is not None else []

    return render_template(
        "chat.html",
        title="Chat Room" if receiver_id is not None else "Chat SportyBuddies",
        year=datetime.now().year,
        users=users,
        messages=messages,
        receiver_id=receiver_id,
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

        # Mo�esz doda� dowolny kod obs�ugi po zapisaniu zg�oszenia, np. przekierowanie na inn� stron�
        return redirect(url_for("logged"))

serializer = URLSafeTimedSerializer(app.secret_key)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        cursor = db.cursor()
        select_query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(select_query, (email,))
        user = cursor.fetchone()

        if user:
            token_data = {'email': email}
            token = serializer.dumps(email)
            reset_link = url_for('new_pass', token=token, _external=True)

            msg = Message("Reset Password", sender="sportybuddies@wp.pl", recipients=[email])
            msg.body = f"Kliknij w link, aby zresetowac haslo do konta: {reset_link}"
            mail.send(msg)

            flash("Link do zresetownia hasla zostal wyslany na poczte.")

    return render_template('forgot.html')



@app.route('/newpass/<token>', methods=['GET','POST'])
def new_pass(token):
    # Obsługa zmiany hasła na podstawie tokenu
    cursor = db.cursor()

    try:
        email = serializer.loads(token, max_age=3600)  
    except BadSignature:
        flash("Nieprawidłowy token resetowania hasła.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password')

        update_query = "UPDATE users SET password = %s WHERE email = %s"
        cursor.execute(update_query, (new_password, email))
        db.commit()

        flash("Hasło zostało pomyślnie zresetowane.")
        return redirect(url_for('login'))

    return render_template('newpass.html')

@app.route("/newpass")
def newpass():
    
    return redirect(url_for("home"))

@app.route("/forgot")
def forgot():
 
    return render_template("forgot.html", title="Forgotten password", year=datetime.now().year)


@app.route("/delete_user")
@login_required
def delete_user():
    cursor = db.cursor()
    
    # Delete associated records from user_sports table
    cursor.execute("DELETE FROM user_sports WHERE user_id = %s", (current_user.id,))
    # Delete user from the users table
    cursor.execute("DELETE FROM users WHERE user_id = %s", (current_user.id,))
    
    db.commit()
    
    # Log the user out after deletion
    logout_user()
    return redirect(url_for("home"))