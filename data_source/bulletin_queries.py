from flask_login import current_user

from data_source.db_connection import get_connection


def get_host_id(activity_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM sports_activity WHERE id = %s", (activity_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result


def get_all_bulletin():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sports_activity WHERE date >= CURDATE()")
    bulletin_data = cursor.fetchall()
    cursor.close()
    connection.close()
    return bulletin_data


def get_bulletin_via_name(activity_name: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM sports_activity WHERE activity_name LIKE %s AND date >= CURDATE()",
        (f"%{activity_name}%",),
    )
    bulletin_data = cursor.fetchall()
    cursor.close()
    connection.close()
    return bulletin_data


def get_sports_activity_by_id(activity_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM sports_activity WHERE id = %s AND date >= CURDATE()",
        (activity_id,),
    )
    activity_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return activity_data


def update_sports_activity(activity_id: int, user_id_list_join: str) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    query = """
        UPDATE sports_activity
        SET user_id_list_join = %s
        WHERE id = %s
    """
    cursor.execute(query, (user_id_list_join, activity_id))
    connection.commit()
    success = cursor.rowcount > 0  # True if at least one row was updated
    cursor.close()
    connection.close()
    return success


def insert_new_activity(activity_data):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO sports_activity (
        user_id, activity_name, activity_type, skills_req, date, location, max_pax
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            activity_data["user_id"],
            activity_data["activity_name"],
            activity_data["activity_type"],
            activity_data["skills_req"],
            activity_data["date"],
            activity_data["location"],
            activity_data["max_pax"],
        ),
    )

    connection.commit()
    cursor.close()
    connection.close()
    return True


def get_bulletin_by_types(activity_types):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    format_strings = ",".join(["%s"] * len(activity_types))
    query = f"SELECT * FROM sports_activity WHERE activity_type IN ({format_strings}) AND date >= CURDATE()"

    cursor.execute(query, tuple(activity_types))
    data = cursor.fetchall()

    cursor.close()
    connection.close()
    return data


def update_sports_activity_details(
    activity_id,
    activity_name,
    activity_type,
    skills_req,
    date,
    location,
    max_pax,
    user_id_list_join,
):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
        UPDATE sports_activity
        SET activity_name=%s, activity_type=%s, skills_req=%s, date=%s, location=%s, max_pax=%s, user_id_list_join=%s
        WHERE id=%s
    """
    cursor.execute(
        query,
        (
            activity_name,
            activity_type,
            skills_req,
            date,
            location,
            max_pax,
            user_id_list_join,
            activity_id,
        ),
    )
    connection.commit()
    cursor.close()
    connection.close()
    return True


def get_joined_user_names_by_activity_id(activity_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Check if current user is the host
    cursor.execute(
        "SELECT user_id, user_id_list_join FROM sports_activity WHERE id = %s",
        (activity_id,),
    )
    result = cursor.fetchone()
    if not result:
        cursor.close()
        connection.close()
        return []
    # Only allow the host to see the joined users
    if str(result["user_id"]) != str(current_user.get_id()):
        cursor.close()
        connection.close()
        return []
    # Get the user_id_list_join for the activity
    if not result.get("user_id_list_join"):
        cursor.close()
        connection.close()
        return []
    user_id_list = [
        uid.strip() for uid in result["user_id_list_join"].split(",") if uid.strip()
    ]
    if not user_id_list:
        cursor.close()
        connection.close()
        return []
    # Fetch only user names for these IDs
    format_strings = ",".join(["%s"] * len(user_id_list))
    query = f"SELECT name FROM user WHERE id IN ({format_strings})"
    cursor.execute(query, tuple(user_id_list))
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    # Return only the names as a list
    return [user["name"] for user in users]


def get_hosted_activities(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT sa.id, sa.activity_name, sa.activity_type, sa.skills_req, sa.date, sa.location, sa.max_pax
        FROM sports_activity sa
        WHERE sa.user_id = %s AND sa.date >= CURDATE()
        """,
        (user_id,),
    )
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data


def get_joined_activities(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT sa.id, sa.activity_name, sa.activity_type, sa.skills_req, sa.date, sa.location, sa.max_pax
        FROM sports_activity sa
        WHERE sa.user_id != %s AND sa.date >= CURDATE() AND FIND_IN_SET(%s, sa.user_id_list_join)
        """,
        (user_id, user_id),
    )
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data
