from data_source.db_connection import get_connection


def delete_sports_activity(activity_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM sports_activity WHERE id = %s", (activity_id,))
    connection.commit()
    success = cursor.rowcount > 0
    cursor.close()
    connection.close()
    return success


def get_social_post_by_id(post_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM feed WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    cursor.close()
    connection.close()
    return post


def delete_social_post(post_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM feed WHERE id = %s", (post_id,))
    connection.commit()
    success = cursor.rowcount > 0
    cursor.close()
    connection.close()
    return success
