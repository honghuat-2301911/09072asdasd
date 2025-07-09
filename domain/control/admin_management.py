import os

from flask import current_app, g
from flask_login import current_user

from data_source.admin_queries import (
    delete_social_post,
    delete_sports_activity,
    get_social_post_by_id,
)
from data_source.bulletin_queries import get_sports_activity_by_id
from domain.entity.sports_activity import SportsActivity

"""Deletes an activity from the bulletin board by its ID. Returns True if successful, False otherwise."""


def remove_sports_activity(activity_id: int):
    try:
        # Fetch the current activity to check if it exists
        activity = get_sports_activity_by_id(activity_id)
        if not activity:
            return False

        # Delete the activity
        return delete_sports_activity(activity_id)

    except Exception as e:
        print(f"Error deleting activity: {e}")
        return False


"""Deletes a social post by its ID. Returns True if successful, False otherwise."""


def remove_social_post(post_id: int):
    try:
        # Fetch the current post to check if it exists and remove the image if it exists
        post = get_social_post_by_id(post_id)
        if not post:
            return False

        post_id, user_id, image_path, caption, like_count = post
        # If the post has an image, remove it from the filesystem
        if image_path:
            rel_path = image_path.lstrip("/")  # Remove leading slash if present

            image_path = os.path.join(current_app.root_path, "presentation", rel_path)

            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete the post
        return delete_social_post(post_id)

    except Exception as e:
        print(f"Error deleting post: {e}")
        return False
