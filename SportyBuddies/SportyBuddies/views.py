from datetime import datetime
from SportyBuddies import app
from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask import Response, jsonify, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from flask import render_template, request, redirect, url_for
from SportyBuddies.models import *
from SportyBuddies.database import *
from SportyBuddies.utils import *
from SportyBuddies.mail import *


app.secret_key = "secret"

serializer = URLSafeTimedSerializer(app.secret_key)


login_manager = LoginManager()
login_manager.init_app(app)

already_matched_users = 0
global matched_user


@login_manager.user_loader
def load_user(user_id):
    user = get_user(user_id)

    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user_profile"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = get_user_id_by_credentials(username, password)

        if user_id:
            user = get_user(user_id)
            login_user(user)
            return redirect(url_for("user_profile"))
        else:
            error_message = "Nieprawidłowa nazwa użytkownika lub hasło."
            return render_template("login.html", error=error_message)

    return render_template("login.html")


@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return redirect(request.url)

    photo = request.files["photo"]

    if photo.filename == "":
        return redirect(request.url)

    if photo:
        photo_data = photo.read()
        update_user_photo(current_user.id, photo_data)

    return redirect(url_for("user_profile"))


@app.route("/user_profile")
def user_profile():
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    user_sports = get_user_sport_ids(current_user.id)
    user_sports = process_user_sports(user_sports)

    return render_template(
        "user_profile.html",
        current_user_id=current_user.id,
        username=current_user.name,
        user_sports=user_sports,
        gender=current_user.gender,
        status=current_user.status,
        age=current_user.age,
    )


@app.route("/update_user_location", methods=["POST"])
def handle_user_location_update():
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    update_user_location(current_user.id, latitude, longitude)

    return jsonify({"message": "User location updated successfully"})


@app.route("/mainpagelogged/<int:next_match>")
@app.route("/mainpagelogged")
def mainpagelogged(next_match=0):
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    match_users()
    global already_matched_users

    if next_match == 1:
        already_matched_users += 1

    current_sport_icons = get_sport_icons(current_user.id)

    if len(current_sport_icons) == 0:
        return redirect(url_for("user_profile"))

    matched_sport_icons = get_sport_icons(matched_user.id)

    distance = haversine(
        current_user.latitude,
        current_user.longitude,
        matched_user.latitude,
        matched_user.longitude,
    )
    distance_string = f"{round(distance)} km"

    return render_template(
        "mainpagelogged.html",
        current_user_id=current_user.id,
        current_username=current_user.name,
        current_age=current_user.age,
        current_sport_icons=current_sport_icons,
        matched_username=matched_user.name,
        matched_age=matched_user.age,
        matched_sport_icons=matched_sport_icons,
        matched_user_id=matched_user.id,
        distance=distance_string,
        matched_info=matched_user.info,
    )


def match_users():
    current_sport_ids = get_user_sport_ids(current_user.id)

    matched_user_ids = get_user_ids_by_sports(current_sport_ids, current_user.id)

    matched_users = [get_user(user_id) for user_id in matched_user_ids]

    matched_users_with_distance = [
        (
            user,
            haversine(
                current_user.latitude,
                current_user.longitude,
                user.latitude,
                user.longitude,
            ),
        )
        for user in matched_users
    ]

    matched_users_sorted_by_distance = sorted(
        matched_users_with_distance, key=lambda x: x[1]
    )

    global already_matched_users
    if already_matched_users >= len(matched_users_with_distance):
        already_matched_users = 0

    global matched_user

    matched_user = matched_users_sorted_by_distance[already_matched_users][0]

    return matched_user


def get_user_info_for_mainpagelogged(user_id):
    user = get_user(user_id)
    sport_icons = get_sport_icons(user_id)

    return user.name, user.age, sport_icons, user.latitude, user.longitude, user.info


@app.route("/get_user_photo/<int:user_id>")
@login_required
def get_user_photo(user_id):
    if user_id == current_user.id:
        photo_data = current_user.photo
    else:
        photo_data = matched_user.photo

    return Response(photo_data, content_type="image/jpeg")


@app.route("/update_user_sports_intensity", methods=["POST"])
def handle_user_sport_intensivity_update():
    sport_id = request.form.get("sportId")
    intensivity = request.form.get("intensity")

    update_user_sport_intensivity(current_user.id, sport_id, intensivity)

    return jsonify({"status": "success"})


@app.route("/update_user_sports", methods=["POST"])
def handle_user_sports_update():
    if request.method == "POST":
        sport_id = request.form.get("sportId")
        is_checked = request.form.get("isChecked")

        update_user_sports(current_user.id, sport_id, is_checked)

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

        user_id_by_username, user_id_by_email = check_existing_user(username, email)

        if user_id_by_username:
            error_message = "Nazwa użytkownika jest już zajęta."
            return render_template("register.html", error=error_message)

        if user_id_by_email:
            error_message = "Email jest już zajęty."
            return render_template("register.html", error=error_message)

        photo_url = "https://static.vecteezy.com/system/resources/thumbnails/009/734/564/small/default-avatar-profile-icon-of-social-media-user-vector.jpg"
        photo_blob = convert_url_to_blob(photo_url)

        insert_new_user(email, password, username, age, gender, description, photo_blob)
        send_registration_email(email)

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html", title="Home Page", year=datetime.now().year)


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


@app.route("/chat", defaults={"receiver_id": None}, methods=["GET", "POST"])
@app.route("/chat/<int:receiver_id>", methods=["GET", "POST"])
def chat(receiver_id):
    if not current_user.is_authenticated:
        return redirect(url_for("mainpagelogged"))

    messages = None
    users = get_users_except_current_user(current_user.id)

    if receiver_id is not None:
        if request.method == "POST":
            content = request.form.get("content")
            insert_message(current_user.id, receiver_id, content)

        messages = get_messages(current_user.id, receiver_id)

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

        submit_report(title, description, current_user.id)

        return redirect(url_for("user_profile"))


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = get_user_by_email(email)

        if user:
            send_reset_password_email(email, serializer)

    return render_template("forgot.html")


@app.route("/newpass/<token>", methods=["GET", "POST"])
def new_pass(token):
    try:
        email = serializer.loads(token, max_age=3600)
    except BadSignature:
        flash("Nieprawidłowy token resetowania hasła.")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form.get("password")
        update_user_password(email, new_password)

        flash("Hasło zostało pomyślnie zresetowane.")

        return redirect(url_for("login"))

    return render_template("newpass.html")


@app.route("/newpass")
def newpass():
    return redirect(url_for("home"))


@app.route("/forgot")
def forgot():
    return render_template(
        "forgot.html", title="Forgotten password", year=datetime.now().year
    )


@app.route("/admin_panel")
@login_required
def admin_panel():
    if current_user.rank < 3:
        return redirect(url_for("user_profile"))
    else:
        return render_template(
            "admin_panel.html", title="Panel Admina", year=datetime.now().year
        )


@app.route("/display_users")
@login_required
def display_users():
    if current_user.rank < 3:
        return redirect(url_for("user_profile"))

    users = get_all_users()

    return render_template("display_users.html", users=users)


@app.route("/delete_user")
@login_required
def handle_user_delete():
    delete_user(current_user.id)
    logout_user()

    return redirect(url_for("home"))


@app.route("/delete_user/<int:user_id>")
@login_required
def delete_selected_user(user_id):
    if current_user.rank < 3:
        return redirect(url_for("user_profile"))

    delete_user(user_id)

    return redirect(url_for("display_users"))