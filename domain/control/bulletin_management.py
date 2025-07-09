from flask import g
from flask_login import current_user

from data_source.bulletin_queries import (
    get_all_bulletin,
    get_bulletin_by_types,
    get_bulletin_via_name,
    get_host_id,
    get_sports_activity_by_id,
    insert_new_activity,
    update_sports_activity,
)
from domain.entity.sports_activity import SportsActivity


def create_entity_from_row(result):
    bulletin_list = []

    for row in result:
        user_id_list = row.get("user_id_list_join")
        current_count = len(user_id_list.split(",")) if user_id_list else 0

        if current_count >= row["max_pax"]:
            continue  # Skip adding this activity if full

        activity = SportsActivity(
            id=row["id"],
            user_id=row["user_id"],
            activity_name=row["activity_name"],
            activity_type=row["activity_type"],
            skills_req=row["skills_req"],
            date=row["date"],  # optionally parse as datetime
            location=row["location"],
            max_pax=row["max_pax"],
            user_id_list_join=user_id_list,
        )
        bulletin_list.append(activity)

    g.bulletin_list = bulletin_list
    return bulletin_list


def get_bulletin_listing():
    result = get_all_bulletin()
    if not result:
        return []
    bulletin_list = create_entity_from_row(result)
    return bulletin_list


def get_host_name(activity_id):
    user_id = get_host_id(activity_id).get("user_id")
    return int(user_id) == int(current_user.id) if user_id else False


def get_bulletin_display_data():
    bulletin_list = g.get("bulletin_list")
    if not bulletin_list:
        return []

    display_data = []
    for activity in bulletin_list:
        display_data.append(
            {
                "id": activity.get_id(),
                "activity_name": activity.get_activity_name(),
                "activity_type": activity.get_activity_type(),
                "skills_req": activity.get_skills_req(),
                "date": activity.get_date(),
                "location": activity.get_location(),
                "max_pax": activity.get_max_pax(),
                "count": int(activity.get_max_pax())
                - len(
                    [
                        uid
                        for uid in (activity.get_user_id_list_join() or "").split(",")
                        if uid.strip()
                    ]
                ),
                "host_by_current_user": activity.get_user_id() == current_user.id,
                # "who_joined": [
                #     get_username_by_id(uid.strip()).get("name")
                #     for uid in (activity.get_user_id_list_join() or "").split(",")
                #     if uid.strip()
                # ] if activity.get_user_id() == current_user.id else None,
                #
            }
        )

    return display_data


def search_bulletin(query):
    result = get_bulletin_via_name(query)
    if not result:
        return []
    bulletin_list = create_entity_from_row(result)
    return bulletin_list


def join_activity_control(activity_id, user_id):
    activity_data = get_sports_activity_by_id(activity_id)
    if not activity_data:
        return None
    sports_activity = SportsActivity(
        id=activity_data["id"],
        user_id=activity_data["user_id"],
        activity_name=activity_data["activity_name"],
        activity_type=activity_data["activity_type"],
        skills_req=activity_data["skills_req"],
        date=activity_data["date"],  # optionally parse as datetime
        location=activity_data["location"],
        max_pax=activity_data["max_pax"],
        user_id_list_join=activity_data.get("user_id_list_join"),
    )
    # Check if user is already in the joined list
    joined_users = sports_activity.get_user_id_list_join()
    if joined_users:
        joined_list = [uid.strip() for uid in joined_users.split(",") if uid.strip()]
        if str(user_id) in joined_list:
            return False  # Already joined

    sports_activity.set_user_id_list_join(user_id)
    result = update_sports_activity(
        sports_activity.get_id(), sports_activity.get_user_id_list_join()
    )
    if result:
        return True
    return False


def create_activity(
    activity_name, activity_type, skills_req, date, location, max_pax, user_id
):
    new_data = {
        "user_id": user_id,
        "activity_name": activity_name,
        "activity_type": activity_type,
        "skills_req": skills_req,
        "date": date,
        "location": location,
        "max_pax": max_pax,
    }
    return insert_new_activity(new_data)


def get_filtered_bulletins(sports: bool, non_sports: bool):
    types = []
    if sports:
        types.append("Sports")
    if non_sports:
        types.append("Non Sports")

    result = get_bulletin_by_types(types)
    if not result:
        return None
    bulletin_list = create_entity_from_row(result)
    return bulletin_list
