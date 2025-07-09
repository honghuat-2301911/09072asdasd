import os
from datetime import datetime

from werkzeug.utils import secure_filename

from data_source.db_connection import get_connection

DB_CONN_ERROR = "[DB ERROR] Could not connect to database."


def get_all_posts():
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return []

    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id, f.user_id, f.caption, f.image_path, f.like_user_ids, u.name as user_name, u.profile_picture
            FROM feed f
            JOIN user u ON f.user_id = u.id
            ORDER BY f.id DESC
        """
        cursor.execute(query)
        posts = cursor.fetchall()
        for post in posts:
            # Get comments for each post (no created_at)
            comment_cursor = connection.cursor(dictionary=True)
            comment_query = """
                SELECT c.id, c.comments, u.name as user_name, u.profile_picture
                FROM comments c
                JOIN user u ON c.user_id = u.id
                WHERE c.feed_id = %s
                ORDER BY c.id ASC
            """
            comment_cursor.execute(comment_query, (post["id"],))
            comments = comment_cursor.fetchall()
            post["comments"] = [
                {
                    "id": c["id"],
                    "user": c["user_name"],
                    "content": c["comments"],
                    "profile_picture": c.get("profile_picture", ""),
                }
                for c in comments
            ]
            comment_cursor.close()
            post["feed_id"] = post["id"]
            post["user"] = post["user_name"]
            post["content"] = post["caption"]
            post["image_url"] = post["image_path"]
            post["likes"] = get_like_count(post["id"])
            post["profile_picture"] = post.get("profile_picture", "")
        return posts
    except Exception as e:
        print(f"[DB ERROR] Error fetching posts: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def add_post(user_id, content, image_url=None):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        query = """
            INSERT INTO feed (user_id, caption, image_path, like_user_ids)
            VALUES (%s, %s, %s, '')
        """
        cursor.execute(query, (user_id, content, image_url))
        connection.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] Error adding post: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def add_comment(feed_id, user_id, content):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        query = """
            INSERT INTO comments (feed_id, user_id, comments)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (feed_id, user_id, content))
        connection.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] Error adding comment: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_posts_by_user(username):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id, f.user_id, f.caption, f.image_path, f.like_user_ids, u.name as user_name
            FROM feed f
            JOIN user u ON f.user_id = u.id
            WHERE u.name = %s
            ORDER BY f.id DESC
        """
        cursor.execute(query, (username,))
        posts = cursor.fetchall()
        for post in posts:
            post["feed_id"] = post["id"]
            post["user"] = post["user_name"]
            post["content"] = post["caption"]
            post["image_url"] = post["image_path"]
            post["likes"] = get_like_count(post["id"])
        return posts
    except Exception as e:
        print(f"[DB ERROR] Error fetching user posts: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_posts_by_user_id(user_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id, f.user_id, f.caption, f.image_path, f.like_user_ids, u.name as user_name, u.profile_picture
            FROM feed f
            JOIN user u ON f.user_id = u.id
            WHERE f.user_id = %s
            ORDER BY f.id DESC
        """
        cursor.execute(query, (user_id,))
        posts = cursor.fetchall()
        for post in posts:
            post["feed_id"] = post["id"]
            post["user"] = post["user_name"]
            post["content"] = post["caption"]
            post["image_url"] = post["image_path"]
            post["likes"] = get_like_count(post["id"])
            post["profile_picture"] = post.get("profile_picture", "")
        return posts
    except Exception as e:
        print(f"[DB ERROR] Error fetching user posts by ID: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def add_post_to_db(user_id, content, image_file=None):
    image_url = None
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(
            "presentation", "static", "images", "social", filename
        )
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)
        image_url = f"/static/images/social/{filename}"
    return add_post(user_id, content, image_url)


def increment_like(post_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE feed SET like_user_ids = CONCAT(like_user_ids, %s) WHERE id = %s",
            (str(post_id), post_id),
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] Error incrementing like: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def decrement_like(post_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE feed SET like_user_ids = REPLACE(like_user_ids, %s, '') WHERE id = %s",
            (str(post_id), post_id),
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] Error decrementing like: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_featured_posts():
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id, f.user_id, f.caption, f.image_path, f.like_user_ids, u.name as user_name, u.profile_picture
            FROM feed f
            JOIN user u ON f.user_id = u.id
            ORDER BY f.like_user_ids DESC, f.id DESC
            LIMIT 5
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"[DB ERROR] Error fetching featured posts: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_post_by_id(post_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT f.id, f.user_id, f.caption, f.image_path, f.like_user_ids, u.name as user_name
            FROM feed f
            JOIN user u ON f.user_id = u.id
            WHERE f.id = %s
        """
        cursor.execute(query, (post_id,))
        post = cursor.fetchone()
        if post:
            post["feed_id"] = post["id"]
            post["user"] = post["user_name"]
            post["content"] = post["caption"]
            post["image_url"] = post["image_path"]
            post["likes"] = get_like_count(post["id"])
        return post
    except Exception as e:
        print(f"[DB ERROR] Error fetching post by id: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def update_post(post_id, content, image_filename):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        query = "UPDATE feed SET caption=%s, image_path=%s WHERE id=%s"
        cursor.execute(query, (content, image_filename, post_id))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[DB ERROR] Error updating post: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def delete_post(post_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor()
    try:
        query = "DELETE FROM feed WHERE id=%s"
        cursor.execute(query, (post_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[DB ERROR] Error deleting post: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def add_like(post_id, user_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT like_user_ids FROM feed WHERE id = %s", (post_id,))
        row = cursor.fetchone()
        if row is None:
            return False
        user_ids = set((row["like_user_ids"] or "").split(","))
        if str(user_id) not in user_ids:
            user_ids.add(str(user_id))
            new_ids = ",".join(user_ids)
            cursor.execute(
                "UPDATE feed SET like_user_ids = %s WHERE id = %s", (new_ids, post_id)
            )
            connection.commit()
            return True
        return False
    except Exception as e:
        print(f"[DB ERROR] Error adding like: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def remove_like(post_id, user_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return False
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT like_user_ids FROM feed WHERE id = %s", (post_id,))
        row = cursor.fetchone()
        if row is None or not row["like_user_ids"]:
            return False
        user_ids = set((row["like_user_ids"] or "").split(","))
        if str(user_id) in user_ids:
            user_ids.remove(str(user_id))
            new_ids = ",".join(user_ids)
            cursor.execute(
                "UPDATE feed SET like_user_ids = %s WHERE id = %s", (new_ids, post_id)
            )
            connection.commit()
            return True
        return False
    except Exception as e:
        print(f"[DB ERROR] Error removing like: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_like_count(post_id):
    connection = get_connection()
    if connection is None:
        print(DB_CONN_ERROR)
        return 0
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT like_user_ids FROM feed WHERE id = %s", (post_id,))
        row = cursor.fetchone()
        if row and row["like_user_ids"] is not None:
            # Only count non-empty user IDs
            return len(
                [uid for uid in (row["like_user_ids"] or "").split(",") if uid.strip()]
            )
        return 0
    except Exception as e:
        print(f"[DB ERROR] Error getting like count: {e}")
        return 0
    finally:
        cursor.close()
        connection.close()
