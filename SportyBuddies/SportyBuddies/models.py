
class User:
    def __init__(
        self,
        user_id,
        email,
        password,
        name,
        age,
        gender,
        info,
        status,
        photo,
        latitude,
        longitude,
    ):
        self.id = user_id
        self.email = email
        self.password = password
        self.name = name
        self.age = age
        self.gender = gender
        self.info = info
        self.status = status
        self.photo = photo
        self.latitude = latitude
        self.longitude = longitude

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


class MatchedUser:
    def __init__(
        self,
        user_id,
        name,
        age,
        gender,
        info,
        status,
        photo,
        latitude,
        longitude,
    ):
        self.id = user_id
        self.name = name
        self.age = age
        self.gender = gender
        self.info = info
        self.status = status
        self.photo = photo
        self.latitude = latitude
        self.longitude = longitude


class Messages:
    def __init__(self, id, sender_id, sender_name, receiver_id, content, timestamp):
        self.id = id
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp


class Matches:
    def __init__(self, id, user_id, matched_user_id, status):
        self.id = id
        self.user_id = user_id
        self.matched_user_id = matched_user_id
        self.status = status
        
class Preferences:
    def __init__(self, user_id, min_age, max_age, preferred_distance,gender_preference):
        self.id = id
        self.user_id = user_id
        self.min_age=min_age
        self.max_age=max_age
        self.preferred_distance=preferred_distance
        self.gender_preference=gender_preference