import os
import uuid

from flask import current_app, flash, g
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from data_source.social_feed_queries import (
    add_comment,
    add_like,
    add_post,
    decrement_like,
)
from data_source.social_feed_queries import delete_post as ds_delete_post
from data_source.social_feed_queries import (
    get_all_posts,
    get_featured_posts,
    get_like_count,
    get_post_by_id,
    get_posts_by_user_id,
    increment_like,
    remove_like,
    update_post,
)
from domain.entity.social_post import Comment, Post

"""Check if the uploaded file has an allowed image extension """


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "png",
        "jpg",
        "jpeg",
        "gif",
    }


"""Convert database rows to Post entities using actual DB field names """


def create_entity_from_row(result):

    post_list = []

    for row in result:
        # Convert comments to Comment entities
        comments = []
        for comment_data in row.get("comments", []):
            comment = Comment(
                id=comment_data["id"],
                post_id=row["id"],
                user=comment_data.get("user", ""),
                content=comment_data.get("content", ""),
                profile_picture=comment_data.get("profile_picture", ""),
            )
            comments.append(comment)

        # Create Post entity using only DB field names
        post = Post(
            id=row["id"],
            user=row.get("user_name", ""),
            content=row.get("caption", ""),
            image_url=row.get("image_path", ""),
            likes=get_like_count(row["id"]),
            comments=comments,
            like_user_ids=row.get("like_user_ids", ""),
        )
        # Attach profile_picture to the post object
        post.profile_picture = row.get("profile_picture", "")
        post_list.append(post)

    g.post_list = post_list
    return post_list


def get_all_posts_control():
    """Get all posts for display in the social feed

    Returns:
        list: List of Post entities
    """
    result = get_all_posts()
    if not result:
        return []

    post_list = create_entity_from_row(result)
    return post_list


"""Get featured posts (top 5 by likes) for display"""


def get_featured_posts_control():

    result = get_featured_posts()
    if not result:
        return []

    # Convert raw DB data to Post entities
    featured_list = []
    for row in result:
        # Create Post entity using only DB field names
        post = Post(
            id=row["id"],
            user=row.get("user_name", ""),
            content=row.get("caption", ""),
            image_url=row.get("image_path", ""),
            likes=get_like_count(row["id"]),
            comments=[],  # Featured posts don't need comments
            like_user_ids=row.get("like_user_ids", ""),
        )
        # Attach profile_picture to the post object
        post.profile_picture = row.get("profile_picture", "")
        featured_list.append(post)

    return featured_list


"""Get a specific post by ID"""


def get_post_by_id_control(post_id):
    result = get_post_by_id(post_id)
    if not result:
        return None

    # Convert raw DB data to Post entity
    row = result[0] if isinstance(result, list) else result

    # Get comments for this post
    comments = []
    for comment_data in row.get("comments", []):
        comment = Comment(
            id=comment_data["id"],
            post_id=row["id"],
            user=comment_data.get("user", ""),
            content=comment_data.get("content", ""),
            profile_picture=comment_data.get("profile_picture", ""),
        )
        comments.append(comment)

    # Create Post entity using only DB field names
    post = Post(
        id=row["id"],
        user=row.get("user_name", ""),
        content=row.get("caption", ""),
        image_url=row.get("image_path", ""),
        likes=get_like_count(row["id"]),
        comments=comments,
        like_user_ids=row.get("like_user_ids", ""),
    )
    # Attach profile_picture to the post object
    post.profile_picture = row.get("profile_picture", "")

    return post


"""Handle creation of a new post with optional image upload"""


def create_post_control(user_id, content, image_file=None):
    image_url = None

    if image_file and image_file.filename:
        try:
            image_file.seek(0)
            image = Image.open(image_file)
            image.verify()
            image_file.seek(0)
        except (UnidentifiedImageError, Exception):
            return False

        # Get the original file extension
        _, ext = os.path.splitext(secure_filename(image_file.filename))
        # Generate a unique filename with uuid4
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        upload_folder = current_app.config.get(
            "UPLOAD_FOLDER", "presentation/static/images/social"
        )
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        image_file.save(filepath)
        image_url = f"/static/images/social/{unique_filename}"

    return add_post(user_id, content, image_url)


"""Handle creation of a new comment on a post"""


def create_comment_control(post_id, user_id, content):

    return add_comment(post_id, user_id, content)


def like_post_control(post_id, user_id):
    return add_like(post_id, user_id)


def unlike_post_control(post_id, user_id):
    return remove_like(post_id, user_id)


"""Get formatted display data for posts"""


def get_posts_display_data():
    post_list = g.get("post_list")
    if not post_list:
        return []

    display_data = []
    for post in post_list:
        display_data.append(
            {
                "id": post.get_id(),
                "user": post.get_user(),
                "content": post.get_content(),
                "image_url": post.get_image_url(),
                "likes": post.get_likes(),
                "comments": [
                    {
                        "id": comment.get_id(),
                        "user": comment.get_user(),
                        "content": comment.get_content(),
                    }
                    for comment in post.get_comments()
                ],
            }
        )

    return display_data


def edit_post(
    user_id: int, post_id: int, updated_content: str, remove_image: bool = False
) -> tuple[bool, str]:
    post = get_post_by_id(post_id)
    if not post or int(post["user_id"]) != user_id:
        return False, "Post not found or unauthorized."

    image_filename = post.get("image_path")
    # Remove image if requested
    if remove_image and image_filename:
        image_path = os.path.join(
            "presentation", "static", "uploads", os.path.basename(image_filename)
        )
        if os.path.exists(image_path):
            os.remove(image_path)
        image_filename = None

    # Update post in DB
    result = update_post(post_id, updated_content, image_filename)
    if result:
        return True, "Post updated successfully."
    else:
        return False, "Failed to update post."


def delete_post(user_id: int, post_id: int) -> bool:
    post = get_post_by_id(post_id)
    if not post or int(post["user_id"]) != user_id:
        return False
    image_filename = post.get("image_path")
    if image_filename:
        image_path = os.path.join(
            "presentation", "static", "uploads", os.path.basename(image_filename)
        )
        if os.path.exists(image_path):
            os.remove(image_path)
    return ds_delete_post(post_id)


"""Get all posts by a specific user ID"""


def get_posts_by_user_id_control(user_id):

    result = get_posts_by_user_id(user_id)
    if not result:
        return []

    post_list = create_entity_from_row(result)
    return post_list
