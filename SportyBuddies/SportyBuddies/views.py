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
from SportyBuddies.matching import get_matched_user_and_distance, on_profile_change
from SportyBuddies.models import *
from SportyBuddies.database import *
from SportyBuddies.utils import *
from SportyBuddies.mail import *
from flask_socketio import SocketIO, emit
import base64
from flask import render_template


socketio = SocketIO(app)

app.secret_key = "secret"

serializer = URLSafeTimedSerializer(app.secret_key)

login_manager = LoginManager()
login_manager.init_app(app)


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

    error_message = request.args.get("error", "")

    user_sports = get_user_sport_ids(current_user.id)
    user_sports = process_user_sports(user_sports)
    current_user_photo = base64.b64encode(current_user.photo).decode("utf-8")
    
    preferences=get_user_preferences(current_user.id)

    return render_template(
        "user_profile.html",
        user=current_user,
        current_user_id=current_user.id,
        user_sports=user_sports,
        error=error_message,
        user_photo=current_user_photo,
        preferences=preferences,
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
def mainpagelogged(next_match=None):
    if current_user.is_authenticated == False:
        return redirect(url_for("login"))

    global matched_user

    if next_match is None:
        pass
    elif next_match == 0:
        update_match_status(current_user.id, matched_user.id, False)
    elif next_match == 1:
        update_match_status(current_user.id, matched_user.id, True)

    x1 = get_matched_user_and_distance(current_user)
    if x1 is None:
        error_message = "Nie znaleziono dla ciebie pary"
        return redirect(url_for("user_profile", error=error_message))

    matched_user, distance = x1

    current_sport_icons = get_sport_icons(current_user.id)

    matched_sport_icons = get_sport_icons(matched_user.id)

    distance_string = f"{round(distance)} km"

    current_user_photo = base64.b64encode(current_user.photo).decode("utf-8")
    matched_user_photo = base64.b64encode(matched_user.photo).decode("utf-8")

    return render_template(
        "mainpagelogged.html",
        current_user=current_user,
        matched_user=matched_user,
        current_sport_icons=current_sport_icons,
        current_user_photo=current_user_photo,
        matched_sport_icons=matched_sport_icons,
        matched_user_photo=matched_user_photo,
        distance=distance_string,
    )


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
        on_profile_change(current_user)

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

    senders, last_messages, messages = None, None, None
    users = get_users_except_current_user(current_user.id)

    if receiver_id is not None:
        if request.method == "POST":
            content = request.form.get("content")
            insert_message(current_user.id, receiver_id, content)

            # Emit message to SocketIO
            socketio.emit(
                "message",
                {
                    "sender_name": current_user.name,
                    "content": content,
                    "receiver_id": receiver_id,
                },
            )

        senders, last_messages, messages = get_messages(current_user.id, receiver_id)

    senders = senders if senders is not None else []
    last_messages = last_messages if last_messages is not None else []
    messages = messages if messages is not None else []

    for user in users:
        if "photo" in user and user["photo"]:
            user["photo_base64"] = base64.b64encode(user["photo"]).decode("utf-8")

    return render_template(
        "chat.html",
        title="Chat Room" if receiver_id is not None else "Chat SportyBuddies",
        year=datetime.now().year,
        users=users,
        senders=senders,
        last_messages=last_messages,
        messages=messages,
        receiver_id=receiver_id,
    )


if __name__ == "__main__":
    socketio.run(app)


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
    if current_user.id != 1:
        return redirect(url_for("user_profile"))
    else:
        return render_template(
            "admin_panel.html", title="Panel Admina", year=datetime.now().year
        )


@app.route("/display_users")
@login_required
def display_users():
    if current_user.id != 1:
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
    if current_user.id != 1:
        return redirect(url_for("user_profile"))

    delete_user(user_id)

    return redirect(url_for("display_users"))


@app.route('/save_preferences', methods=['POST'])
def save_preferences():
    if request.method == 'POST':
        data = request.get_json()

        min_age = data.get('min_age')
        max_age = data.get('max_age')
        preferred_distance = data.get('preferred_distance')
        gender_preference = data.get('gender_preference')

        set_preferences(current_user.id,min_age,max_age,preferred_distance,gender_preference)

        return jsonify({'status': 'success'})
