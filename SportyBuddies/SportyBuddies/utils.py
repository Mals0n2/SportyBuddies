from io import BytesIO
from PIL import Image
import math
import requests

from SportyBuddies.database import *


def process_user_sports(results):
    user_sports = [result if result > 0 else 0 for result in results[:15]]
    sports = [0] * 15
    for i in user_sports:
        if i > 0:
            sports[i - 1] = i

    return sports


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371
    distance = R * c

    return distance


def convert_url_to_blob(photo_url):
    response = requests.get(photo_url)
    image = Image.open(BytesIO(response.content))
    blob_data = BytesIO()
    image.save(blob_data, format="JPEG")
    photo_blob = blob_data.getvalue()
    return photo_blob