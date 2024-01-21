from datetime import datetime
import mysql.connector
from .models import MatchedUser, Matches, Preferences, User
from werkzeug.security import generate_password_hash, check_password_hash


db = mysql.connector.connect(
    host="localhost", user="root", passwd="", database="sportybuddies"
)


def get_user(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchall()
    cursor.close()
    if user_data:
        user = User(*user_data[0])
        return user

    return None


def get_matched_user(user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id,name,age,gender,info,status,photo,latitude,longitude FROM users WHERE user_id = %s",
        (user_id,),
    )
    user_data = cursor.fetchall()
    cursor.close()

    if user_data:
        user = MatchedUser(*user_data[0])
        return user

    return None


def get_user_id_by_credentials(username, password):
    cursor = db.cursor()
    cursor.execute(
        "SELECT password FROM users WHERE name = %s",
        (username,),
    )
    user_data = None
    password1 = cursor.fetchone()[0]
    if check_password_hash(password1,password):
        cursor.execute(
            "SELECT user_id FROM users WHERE name = %s",
            (username,),
        )
        user_data = cursor.fetchall()
    cursor.close()

    return user_data[0][0] if user_data else None


def update_user_photo(user_id, photo_data):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET photo = %s WHERE user_id = %s", (photo_data, user_id)
    )
    cursor.close()
    db.commit()


def get_user_sport_ids(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT sport_id FROM user_sports WHERE user_id = %s", (user_id,))
    sport_data = cursor.fetchall()
    cursor.close()
    sport_ids = [sport[0] for sport in sport_data]
    return sport_ids


def update_user_location(user_id, latitude, longitude):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET latitude = %s, longitude = %s WHERE user_id = %s",
        (latitude, longitude, user_id),
    )
    cursor.close()
    db.commit()


def get_user_ids_by_sports(sport_ids, user_id):
    sport_ids_tuple = tuple(sport_ids)
    formatted_sport_ids = ", ".join(["%s"] * len(sport_ids_tuple))

    cursor = db.cursor()
    cursor.execute(
        f"SELECT user_id FROM user_sports WHERE sport_id IN ({formatted_sport_ids}) AND user_id != %s;",
        (*sport_ids_tuple, user_id),
    )
    users_data = cursor.fetchall()
    cursor.close()
    matched_user_ids = set(user_id[0] for user_id in users_data)
    return matched_user_ids


def get_sport_icons(user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT sports.iconlink FROM sports JOIN user_sports ON sports.sport_id = user_sports.sport_id WHERE user_sports.user_id = %s",
        (user_id,),
    )
    sport_icons = cursor.fetchall()
    cursor.close()

    return sport_icons


def update_user_sport_intensivity(user_id, sport_id, intensivity):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE user_sports SET intensity = %s WHERE user_id = %s AND sport_id = %s",
        (intensivity, user_id, sport_id),
    )
    cursor.close()
    db.commit()


def update_user_sports(user_id, sport_id, is_checked):
    cursor = db.cursor()
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
    cursor.close()
    db.commit()


def check_existing_user(username, email):
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users WHERE name = %s", (username,))
    user_id_by_username = cursor.fetchone()

    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    user_id_by_email = cursor.fetchone()
    cursor.close()
    return user_id_by_username, user_id_by_email


def insert_new_user(email, password, username, age, gender, description, photo_blob):
    cursor = db.cursor()
    password=generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (email, password, name, age, gender, info, photo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (email, password, username, age, gender, description, photo_blob),
    )
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    user_id = cursor.fetchone()[0]
    cursor.execute(
            "INSERT INTO preferences (user_id, min_age, max_age, preferred_distance, gender_preference) VALUES (%s, %s, %s, %s, %s)",
            (user_id,18, 25, 50,'Wszyscy',),
        )
    cursor.close()
    db.commit()


def get_users_except_current_user(current_user_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       "SELECT u.user_id, u.name, u.photo FROM users u "
    "WHERE u.user_id != %s "
    "AND u.user_id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id = %s) "
    "AND %s NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id = u.user_id) "
    "AND EXISTS ("
    "   SELECT 1 FROM matches m1 "
    "   WHERE m1.user_id = %s AND m1.matched_user_id = u.user_id AND m1.status = 1 "
    ") "
    "AND EXISTS ("
    "   SELECT 1 FROM matches m2 "
    "   WHERE m2.user_id = u.user_id AND m2.matched_user_id = %s AND m2.status = 1 "
    ")",
    (current_user_id, current_user_id, current_user_id, current_user_id, current_user_id,)
    )
    users = cursor.fetchall()
    cursor.close()
    return users


def insert_message(sender_id, receiver_id, content):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO messages (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)",
        (sender_id, receiver_id, content, timestamp),
    )
    cursor.close()
    db.commit()


def get_messages(current_user_id, receiver_id):
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT users.user_id, users.name AS sender_name, MAX(messages.timestamp) AS max_timestamp "
        "FROM users "
        "JOIN messages ON users.user_id = messages.sender_id "
        "WHERE messages.receiver_id = %s "
        "AND messages.sender_id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id = messages.receiver_id) "
        "AND messages.receiver_id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id = messages.sender_id) "
        "GROUP BY users.user_id;",
        (current_user_id,)
    )
    senders = cursor.fetchall()

    last_messages = []
    for sender in senders:
        cursor.execute(
            "SELECT messages.id, messages.sender_id, users.name AS sender_name, messages.receiver_id, messages.content, messages.timestamp "
            "FROM messages "
            "JOIN users ON messages.sender_id = users.user_id "
            "WHERE (messages.receiver_id = %s AND messages.sender_id = %s) "
            "OR (messages.sender_id = %s AND messages.receiver_id = %s) "
            "ORDER BY messages.timestamp DESC "
            "LIMIT 1",
            (current_user_id, sender['user_id'], sender['user_id'], current_user_id),
        )
        last_message = cursor.fetchone()
        if last_message:
            last_messages.append(last_message)

    # Fetch all messages for the current conversation
    cursor.execute(
        "SELECT messages.id, messages.sender_id, users.name AS sender_name, messages.receiver_id, messages.content, messages.timestamp "
        "FROM messages "
        "JOIN users ON messages.sender_id = users.user_id "
        "WHERE (messages.sender_id = %s AND messages.receiver_id = %s) OR (messages.sender_id = %s AND messages.receiver_id = %s) "
        "ORDER BY messages.timestamp",
        (current_user_id, receiver_id, receiver_id, current_user_id),
    )
    messages = cursor.fetchall()

    cursor.close()

    return senders, last_messages, messages


def get_user_by_email(email):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()

    return user


def update_user_password(email, password):
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (password, email))
    cursor.close()
    db.commit()


def delete_user(user_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM user_sports WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM matches WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    cursor.close()
    db.commit()


def get_all_users():
    cursor = db.cursor()
    cursor.execute("SELECT user_id, name, email FROM users")
    users = cursor.fetchall()
    cursor.close()
    return users


def get_all_reports():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports")
    reports = cursor.fetchall()
    cursor.close()
    return reports

def get_all_user_reports():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user_reports")
    user_reports = cursor.fetchall()
    cursor.close()
    return user_reports

def insert_match(user_id, matched_user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM matches WHERE user_id=%s AND matched_user_id=%s",
        (user_id, matched_user_id),
    )
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO matches (user_id, matched_user_id) VALUES (%s, %s)",
            (user_id, matched_user_id),
        )
    cursor.close()
    db.commit()


def get_all_matches(user_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM matches WHERE user_id = %s", (user_id,))
    matches = cursor.fetchall()
    cursor.close()

    if matches:
        matches = [Matches(*match) for match in matches]
        return matches
    return None


def delete_user_matches(user_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM matches WHERE user_id = %s AND status is NULL", (user_id,))
    cursor.close()
    db.commit()


def update_match_status(user_id, matched_user_id, status):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE matches SET status = %s WHERE user_id = %s AND matched_user_id = %s",
        (status, user_id, matched_user_id),
    )
    cursor.close()
    db.commit()
    

def set_preferences(user_id, min_age, max_age, preferred_distance, gender_preference):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE preferences SET min_age=%s,max_age=%s,preferred_distance=%s,gender_preference=%s WHERE user_id=%s",
        (min_age, max_age, preferred_distance, gender_preference,user_id),
        )
    cursor.close()
    db.commit()
    

def get_user_preferences(user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM preferences WHERE user_id = %s",
        (user_id,),
    )
    preferences = cursor.fetchall()
    cursor.close()
    if preferences:
        preferences = Preferences(*preferences[0])
        return preferences
    return None

def block_user_db(blocker_id,blocked_id):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO blocked_users (blocker_id, blocked_id) VALUES (%s, %s)",
        (blocker_id, blocked_id,),
    )
    cursor.close()
    db.commit()
    return None

def update_user_info(user_id,info):
    cursor = db.cursor()
    cursor.execute("UPDATE users SET info = %s WHERE user_id = %s", (info,user_id))
    cursor.close()
    db.commit()


def insert_report(title, description, user_id):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO reports (user_id, date, title, `desc`) VALUES (%s, %s, %s, %s)",
        (user_id, date, title, description),
    )
    cursor.close()
    db.commit()
    

def insert_user_report(title, description, reporter_id,reported_id):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO user_reports (reporter_id,reported_id,title,description,date) VALUES (%s, %s, %s, %s, %s)",
        (reporter_id,reported_id,title,description,date),
    )
    cursor.close()
    db.commit()


#def get_user_rating_from_db():
#    try:
#        connection = mysql.connector.connect(**db_config)
#        cursor = connection.cursor(dictionary=True)


#        query = "SELECT rating FROM users WHERE user_id = 1"
#        cursor.execute(query)
#        result = cursor.fetchone()

#        return result['rating'] if result else 0

#    except mysql.connector.Error as err:
#        print(f"Error: {err}")
#    finally:
#        if connection.is_connected():
#            cursor.close()
#            connection.close()

#def save_user_rating_to_db(new_rating):
#    try:
#        connection = mysql.connector.connect(**db_config)
#        cursor = connection.cursor(dictionary=True)

#        query = "UPDATE users SET rating = %s WHERE user_id = 1"
#        cursor.execute(query, (new_rating,))
#        connection.commit()

#    except mysql.connector.Error as err:
#        print(f"Error: {err}")
#    finally:
#        if connection.is_connected():
#            cursor.close()
#            connection.close()

#def calculate_new_rating(current_rating, new_rating):
#    return (current_rating + new_rating) / 2