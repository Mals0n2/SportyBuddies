import random
from SportyBuddies.database import *
from SportyBuddies.utils import haversine


def match_users(user_id):
    matches = get_all_matches(user_id)
    if matches is None:
        return None
    matched_users = [get_matched_user(match.matched_user_id) for match in matches]

    matched_users_without_status = []
    for index, user in enumerate(matched_users):
        if matches[index].status == None:
            matched_users_without_status.append(user)

    return matched_users_without_status


def get_matched_user_and_distance(current_user: User):
    matched_users = match_users(current_user.id)
    if matched_users is None:
        return None
    matched_users_and_distance = [
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
        matched_users_and_distance, key=lambda x: x[1]
    )
    if matched_users_sorted_by_distance == []:
        return None
    matched_user = random.choice(matched_users_sorted_by_distance)
    return matched_user


def on_profile_change(current_user: User):
    current_sport_ids = get_user_sport_ids(current_user.id)
    if current_sport_ids == []:
        delete_user_matches(current_user.id)
        return
    matched_user_ids = get_user_ids_by_sports(current_sport_ids, current_user.id)
    matched_users = [get_matched_user(user_id) for user_id in matched_user_ids]

    delete_user_matches(current_user.id)
    for user in matched_users:
        insert_match(current_user.id, user.id)

    # matched_users_sorted_by_distance = sorted(
    #     matched_users_with_distance, key=lambda x: x[1]
    # )