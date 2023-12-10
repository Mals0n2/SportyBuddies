from datetime import datetime
import mysql.connector
from .models import MatchedUser, Matches, User

db = mysql.connector.connect(
    host="localhost", user="root", passwd="", database="sportybuddies"
)


def get_user(user_id):
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchall()

        if user_data:
            user = User(*user_data[0])
            return user

    return None


def get_matched_user(user_id):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT user_id,name,age,gender,info,status,photo,latitude,longitude FROM users WHERE user_id = %s",
            (user_id,),
        )
        user_data = cursor.fetchall()

    if user_data:
        user = MatchedUser(*user_data[0])
        return user

    return None


def get_user_id_by_credentials(username, password):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT user_id FROM users WHERE name = %s AND password = %s",
            (username, password),
        )
        user_data = cursor.fetchall()

    return user_data[0][0] if user_data else None


def update_user_photo(user_id, photo_data):
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET photo = %s WHERE user_id = %s", (photo_data, user_id)
        )
        db.commit()


def get_user_sport_ids(user_id):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT sport_id FROM user_sports WHERE user_id = %s", (user_id,)
        )
        sport_data = cursor.fetchall()
        sport_ids = [sport[0] for sport in sport_data]
    return sport_ids


def update_user_location(user_id, latitude, longitude):
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET latitude = %s, longitude = %s WHERE user_id = %s",
            (latitude, longitude, user_id),
        )
        db.commit()


def get_user_ids_by_sports(sport_ids, user_id):
    sport_ids_tuple = tuple(sport_ids)
    formatted_sport_ids = ", ".join(["%s"] * len(sport_ids_tuple))

    with db.cursor() as cursor:
        cursor.execute(
            f"SELECT user_id FROM user_sports WHERE sport_id IN ({formatted_sport_ids}) AND user_id != %s;",
            (*sport_ids_tuple, user_id),
        )
        users_data = cursor.fetchall()
        matched_user_ids = set(user_id[0] for user_id in users_data)
    return matched_user_ids


def get_sport_icons(user_id):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT sports.iconlink FROM sports JOIN user_sports ON sports.sport_id = user_sports.sport_id WHERE user_sports.user_id = %s",
            (user_id,),
        )
        sport_icons = cursor.fetchall()

    return sport_icons


def update_user_sport_intensivity(user_id, sport_id, intensivity):
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE user_sports SET intensity = %s WHERE user_id = %s AND sport_id = %s",
            (intensivity, user_id, sport_id),
        )
        db.commit()


def update_user_sports(user_id, sport_id, is_checked):
    with db.cursor() as cursor:
        if is_checked == "true":
            cursor.execute(
                "INSERT INTO user_sports (user_id, sport_id) VALUES (%s, %s)",
                (user_id, sport_id),
            )
        else:
            cursor.execute(
                "DELETE FROM user_sports WHERE user_id = %s AND sport_id = %s",
                (user_id, sport_id),
            )
        db.commit()


def check_existing_user(username, email):
    with db.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE name = %s", (username,))
        user_id_by_username = cursor.fetchone()

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user_id_by_email = cursor.fetchone()

    return user_id_by_username, user_id_by_email


def insert_new_user(email, password, username, age, gender, description, photo_blob):
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (email, password, name, age, gender, info, photo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (email, password, username, age, gender, description, photo_blob),
        )
        db.commit()


def get_users_except_current_user(current_user_id):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT user_id, name FROM users WHERE user_id != %s", (current_user_id,)
        )
        users = cursor.fetchall()

    return users


def insert_message(sender_id, receiver_id, content):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)",
            (sender_id, receiver_id, content, timestamp),
        )
        db.commit()


def get_messages(current_user_id, receiver_id):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT messages.id, messages.sender_id, users.name AS sender_name, messages.receiver_id, messages.content, messages.timestamp FROM messages JOIN users ON messages.sender_id = users.user_id WHERE (messages.sender_id = %s AND messages.receiver_id = %s) OR (messages.sender_id = %s AND messages.receiver_id = %s) ORDER BY messages.timestamp",
            (current_user_id, receiver_id, receiver_id, current_user_id),
        )
        messages = cursor.fetchall()

    return messages


def insert_report(title, description, user_id):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO reports (user_id, date, title, `desc`) VALUES (%s, %s, %s, %s)",
            (user_id, date, title, description),
        )
        db.commit()


def get_user_by_email(email):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

    return user


def update_user_password(email, password):
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET password = %s WHERE email = %s", (password, email)
        )
        db.commit()


def delete_user(user_id):
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM user_sports WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        db.commit()


def get_all_users():
    with db.cursor() as cursor:
        cursor.execute("SELECT user_id, name, email FROM users")
        users = cursor.fetchall()
    return users


def insert_match(user_id, matched_user_id):
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO matches (user_id, matched_user_id) VALUES (%s, %s)",
            (user_id, matched_user_id),
        )
        db.commit()


def get_all_matches(user_id):
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM matches WHERE user_id = %s", (user_id,))
        matches = cursor.fetchall()

        if matches:
            matches = [Matches(*match) for match in matches]
            return matches
    return None


def delete_user_matches(user_id):
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM matches WHERE user_id = %s", (user_id,))
        db.commit()


def update_match_status(user_id, matched_user_id, status):
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE matches SET status = %s WHERE user_id = %s AND matched_user_id = %s",
            (status, user_id, matched_user_id),
        )
        db.commit()
