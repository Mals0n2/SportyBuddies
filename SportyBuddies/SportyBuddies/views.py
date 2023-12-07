from datetime import datetime
from re import A, S
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
import math

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

already_matched_users=0


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

    cursor.execute("SELECT user_id, rank FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()

    cursor.close()
    if user_data:
        user = User(user_data[0])
        if user_data[1] >= 3:
            user.is_admin = True
        else:
            user.is_admin = False
        return user
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

    cursor.close()
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
    cursor.close()
    

@app.route("/mainpagelogged/<int:next_match>")
@app.route("/mainpagelogged")
def mainpagelogged(next_match=0):
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))
    
    global already_matched_users
    
    if next_match==1:
        already_matched_users+=1
        

    current_username, current_age, current_sport_icons, current_latitude, current_longitude, current_info = get_user_info_for_mainpagelogged(current_user.id)
    if len(current_sport_icons) == 0:
        return redirect(url_for("user_profile"))
    matched_user_id= get_matched_user_id()
    matched_username,matched_age, matched_sport_icons,matched_latitude, matched_longitude, current_info = get_user_info_for_mainpagelogged(matched_user_id)
    
    #get distance
    distance = haversine(current_latitude, current_longitude, matched_latitude, matched_longitude)
    distance_string = f"{round(distance)} km"
    

    return render_template(
        "mainpagelogged.html",
        current_user_id=current_user.id,
        current_username=current_username,
        current_age = current_age,
        current_sport_icons = current_sport_icons,
        matched_username=matched_username,
        matched_age = matched_age,
        matched_sport_icons = matched_sport_icons,
        matched_user_id=matched_user_id,
        distance=distance_string,
        current_info=current_info
    )

def haversine(lat1, lon1, lat2, lon2):
    # Konwersja stopni na radiany
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # Różnice między szerokościami i długościami geograficznymi
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Obliczanie odległości przy użyciu formuły haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    R = 6371  # Promień Ziemi w kilometrach. Można użyć 3958.8 dla mil morskich.
    distance = R * c

    return distance


def get_matched_user_id():
    cursor = db.cursor()
    
    #get current user sport ids
    cursor.execute("SELECT sport_id FROM user_sports WHERE user_id=%s;", (current_user.id,))
    current_sport_ids_from_db=cursor.fetchall()
    print(current_sport_ids_from_db)
    current_sport_ids=[]
    for sport_id in current_sport_ids_from_db:
        current_sport_ids.append(sport_id[0])
    print(current_sport_ids)
    
    # Convert list to tuple
    current_sport_ids_tuple = tuple(current_sport_ids)

    # Format tuple for SQL IN clause
    formatted_sport_ids = ', '.join(['%s'] * len(current_sport_ids_tuple))

    # Use formatted tuple in SQL statement
    cursor.execute(f"SELECT user_id FROM user_sports WHERE sport_id IN ({formatted_sport_ids}) AND user_id != %s;", (*current_sport_ids_tuple, current_user.id))
    matched_users_ids_by_sport_from_db=cursor.fetchall()
    print(matched_users_ids_by_sport_from_db)
    matched_users_ids_by_sport=[]
    for user_id in matched_users_ids_by_sport_from_db:
        matched_users_ids_by_sport.append(user_id[0])
    print(matched_users_ids_by_sport)

    #calculate distance and get closest user
    cursor.execute("SELECT latitude FROM users WHERE user_id = %s", (current_user.id,))
    current_latitude = cursor.fetchone()[0]
    cursor.execute("SELECT longitude FROM users WHERE user_id = %s", (current_user.id,))
    current_longitude = cursor.fetchone()[0]
    
    matched_users_sorted_by_distance=[]
    for user_id in matched_users_ids_by_sport:
        cursor.execute("SELECT latitude FROM users WHERE user_id = %s", (user_id,))
        matched_latitude = cursor.fetchone()[0]
        cursor.execute("SELECT longitude FROM users WHERE user_id = %s", (user_id,))
        matched_longitude = cursor.fetchone()[0]
        distance = haversine(current_latitude, current_longitude, matched_latitude, matched_longitude)
        matched_users_sorted_by_distance.append((user_id,distance))
        matched_users_sorted_by_distance.sort(key=lambda x: x[1])
        
    print(matched_users_sorted_by_distance)

    global already_matched_users
    if already_matched_users >= len(matched_users_sorted_by_distance):
        already_matched_users = 0

    #get closest user from database
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (matched_users_sorted_by_distance[already_matched_users][0],))
    user_id = cursor.fetchone()[0]
    
    cursor.close()
    return user_id

def get_user_info_for_mainpagelogged(user_id):
    
    cursor = db.cursor()
    
    cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
    username = cursor.fetchone()[0]
    
    cursor.execute("SELECT age FROM users WHERE user_id = %s", (user_id,))
    user_age = cursor.fetchone()[0]
    
    cursor.execute("SELECT sports.iconlink FROM sports JOIN user_sports ON sports.sport_id = user_sports.sport_id WHERE user_sports.user_id = %s", (user_id,))
    sport_id = cursor.fetchall()
    
    #get distance
    cursor.execute("SELECT latitude FROM users WHERE user_id = %s", (user_id,))
    latitude = cursor.fetchone()[0]
    
    cursor.execute("SELECT longitude FROM users WHERE user_id = %s", (user_id,))
    longitude = cursor.fetchone()[0]

    cursor.execute("SELECT info FROM users WHERE user_id = %s", (user_id,))
    info = cursor.fetchone()[0]
    
    cursor.close()
    return username, user_age, sport_id,latitude, longitude, info
    


@app.route("/get_user_photo/<int:user_id>")
@login_required
def get_user_photo(user_id):
    cursor = db.cursor()
    cursor.reset()
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
            "SELECT user_id, rank FROM users WHERE name = %s AND password = %s",
            (username, password),
        )
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            user = User(user_data[0])

            username = request.form["username"]
            cursor = db.cursor()
            cursor.execute(
            "UPDATE `users` SET `status` = 'online' WHERE name = %s",
            (username,)
        )
            db.commit()
            cursor.close()

            if user_data[1] >= 3:
                user.is_admin = True
            login_user(user)
            global already_matched_users
            already_matched_users=0
            return redirect(url_for("user_profile"))
        else:
            error_message = "Nieprawidłowa nazwa użytkownika lub hasło."
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

    cursor=db.cursor(dictionary=True)
    cursor.execute("SELECT user_id, name FROM users WHERE user_id != %s", (current_user.id,))
    users = cursor.fetchall()

    if receiver_id is not None:
        if request.method == 'POST':
            content = request.form.get('content')
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)",
                            (current_user.id, receiver_id, content, timestamp)
                        )
            db.commit()

        cursor.execute("SELECT messages.id, messages.sender_id, users.name AS sender_name, messages.receiver_id, messages.content, messages.timestamp FROM messages JOIN users ON messages.sender_id = users.user_id WHERE (messages.sender_id = %s AND messages.receiver_id = %s) OR (messages.sender_id = %s AND messages.receiver_id = %s) ORDER BY messages.timestamp",(current_user.id, receiver_id, receiver_id, current_user.id))
        messages = [Messages(**msg) for msg in cursor.fetchall()]

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
        cursor.close()

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

    try:
        email = serializer.loads(token, max_age=3600)  
    except BadSignature:
        flash("Nieprawidłowy token resetowania hasła.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password')

        update_query = "UPDATE users SET password = %s WHERE email = %s"
        cursor = db.cursor()
        cursor.execute(update_query, (new_password, email))
        db.commit()
        cursor.close()

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
    cursor.close()
    # Log the user out after deletion
    logout_user()
    return redirect(url_for("home"))


@app.route("/admin_panel")
@login_required
def admin_panel():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("logged"))
    else:
        return render_template("admin_panel.html", title="Panel Admina", year=datetime.now().year)

@app.route("/display_users")
@login_required
def display_users():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("logged"))

    cursor = db.cursor()
    cursor.execute("SELECT user_id, name, email FROM users")
    users = cursor.fetchall()
    cursor.close()

    return render_template("display_users.html", users=users)

@app.route("/delete_user/<int:user_id>")
@login_required
def delete_selected_user(user_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("logged"))

    cursor = db.cursor()

    # Delete associated records from user_sports table
    cursor.execute("DELETE FROM user_sports WHERE user_id = %s", (user_id,))
    # Delete user from the users table
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

    db.commit()
    cursor.close()

    return redirect(url_for("display_users"))