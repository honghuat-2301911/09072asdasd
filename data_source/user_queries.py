from datetime import datetime, timedelta, timezone

import mysql.connector
from flask import current_app

from data_source.db_connection import get_connection


# process user reset passwrd request
def get_id_by_email(email: str):

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM user WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    return result[0] if result else None


def delete_reset_password(user_id):
    """Delete reset password request by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM reset_password WHERE user_id=%s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()


def insert_into_reset_password(user_id, token_hash, expires_at):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO reset_password (user_id, token_hash, expires_at) "
            "VALUES (%s, %s, %s)",
            (user_id, token_hash, expires_at),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error inserting reset password request: {e}")
        return False


# retrieve hashed token by token hash
def get_user_by_token_hash(token_hash):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, expires_at, used
            FROM reset_password
            WHERE token_hash = %s
            ORDER BY expires_at DESC
            LIMIT 1
            """,
            (token_hash,),
        )
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            return {"user_id": result[0], "expires_at": result[1], "used": result[2]}
        else:
            return None
    except Exception as e:
        current_app.logger.error(f"Error retrieving reset token info: {e}")
        return None


def update_user_password_by_id(user_id, hashed_password):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET password = %s WHERE id = %s", (hashed_password, user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error updating password: {e}")
        return False


def update_reset_link_used(token_hash):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE reset_password SET used = 1 WHERE token_hash = %s", (token_hash,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error updating reset link usage: {e}")
        return False


def disable_otp_by_user_id(user_id):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET otp_enabled=0, otp_secret=NULL WHERE id=%s", (user_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error disabling OTP: {e}")
        return False


def update_user_verification_status(email):
    verified = True
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET email_verified = %s WHERE email = %s",
            (int(verified), email),
        )
        connection.commit()
        updated_rows = cursor.rowcount
        return updated_rows > 0
    except Exception as e:
        return False
    finally:
        cursor.close()
        connection.close()


def set_otp_secret(otp_secret, user_id):
    try:
        connection = get_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute(
            "UPDATE user SET otp_secret=%s WHERE id=%s", (otp_secret, user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error setting OTP secret: {e}")
        return False


def enable_2fa(user_id):
    try:
        connection = get_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("UPDATE user SET otp_enabled=1 WHERE id=%s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error enabling 2FA: {e}")
        return False


# Account Lock out Code
def record_failed_login(user_id):
    """Insert a failed login record for the user."""
    connection = get_connection()
    cursor = connection.cursor()
    UTC_PLUS_8 = timezone(timedelta(hours=8))
    now = datetime.now(UTC_PLUS_8).replace(tzinfo=None)
    cursor.execute(
        "INSERT INTO user_failed_login (user_id, failed_at) VALUES (%s, %s)",
        (user_id, now),
    )
    connection.commit()
    cursor.close()
    connection.close()


def get_user_failed_attempts_count(user_id, window_minutes=10):
    """Count failed logins for user in the last window_minutes."""
    connection = get_connection()
    cursor = connection.cursor()
    UTC_PLUS_8 = timezone(timedelta(hours=8))
    window_start = datetime.now(UTC_PLUS_8) - timedelta(minutes=window_minutes)
    window_start = window_start.replace(tzinfo=None)
    cursor.execute(
        "SELECT COUNT(*) FROM user_failed_login WHERE user_id=%s AND failed_at >= %s",
        (user_id, window_start),
    )
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return count


def update_user_lockout(user_id, locked_until):
    """
    Update the locked_until field in the user table.
    Args:
        user_id (int): The user's ID.
        locked_until (datetime or None): The datetime until which the account is locked, or None to unlock.
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET locked_until=%s WHERE id=%s", (locked_until, user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error updating locked_until: {e}")
        return False


def clear_failed_logins(user_id):
    """Delete all failed login records for the user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM user_failed_login WHERE user_id=%s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()


def get_user_by_email(email: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_data


"""Insert a new user into the database"""


def insert_user(user_data: dict) -> bool:
    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO user (name, password, email, role)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                user_data["name"],
                user_data["password"],
                user_data["email"],
                user_data.get("role", "user"),
            ),
        )
        connection.commit()
        return True
    except Exception as e:
        print("Insert failed:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_user_by_id(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_data


def get_username_by_id(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name FROM user WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_data


def update_user_profile_by_id(
    user_id: int, name: str, password: str, profile_picture: str = None
) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if profile_picture is not None:
            query = "UPDATE user SET name = %s, password = %s, profile_picture = %s WHERE id = %s"
            cursor.execute(query, (name, password, profile_picture, user_id))
        else:
            query = "UPDATE user SET name = %s, password = %s WHERE id = %s"
            cursor.execute(query, (name, password, user_id))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print("Update failed:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def search_users_by_name(search_term: str, limit: int = 10):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT id, name, email, profile_picture
            FROM user 
            WHERE name LIKE %s 
            ORDER BY name 
            LIMIT %s
        """
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, limit))
        users = cursor.fetchall()
        return users
    except Exception as e:
        print(f"Search failed: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def remove_user_profile_picture(user_id: int) -> bool:
    connection = get_connection()
    if connection is None:
        print("[DB ERROR] Connection failed in remove_user_profile_picture")
        return False
    cursor = connection.cursor()
    try:
        query = "UPDATE user SET profile_picture = '' WHERE id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print("Remove profile picture failed:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_user_session_token(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT current_session_token FROM user WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result["current_session_token"] if result else None


def update_user_session_token(user_id: int, token: str):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE user SET current_session_token = %s WHERE id = %s", (token, user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()
