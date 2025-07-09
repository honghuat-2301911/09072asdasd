import os
import uuid

import bcrypt
from flask import current_app, g
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from data_source.bulletin_queries import (
    get_all_bulletin,
    get_hosted_activities,
    get_joined_activities,
    get_joined_user_names_by_activity_id,
    get_sports_activity_by_id,
    update_sports_activity,
    update_sports_activity_details,
)
from data_source.social_feed_queries import get_posts_by_user_id
from data_source.user_queries import (
    disable_otp_by_user_id,
    get_user_by_id,
    remove_user_profile_picture,
    update_user_profile_by_id,
)
from domain.control.otp_management import generate_otp_for_user, verify_and_enable_otp
from domain.control.social_feed_management import delete_post, edit_post
from domain.entity.social_post import Comment, Post
from domain.entity.sports_activity import SportsActivity
from domain.entity.user import User


class ProfileManagement:
    def update_profile(self, user_id, name, password, profile_picture=None):
        if profile_picture is not None:
            return update_user_profile_by_id(user_id, name, password, profile_picture)
        else:
            return update_user_profile_by_id(user_id, name, password)

    def remove_profile_picture(self, user_id):
        return remove_user_profile_picture(user_id)

    def get_joined_user_names(self, activity_id):
        return get_joined_user_names_by_activity_id(activity_id)

    def get_user_profile(self, user_id):
        user_data = get_user_by_id(user_id)
        if not isinstance(user_data, dict):
            return None
        id_val = user_data.get("id")
        if isinstance(id_val, int):
            user_id_val = id_val
        elif isinstance(id_val, str) and id_val.isdigit():
            user_id_val = int(id_val)
        else:
            user_id_val = 0
        # Safely convert database values to proper types
        otp_secret_val = user_data.get("otp_secret")
        if otp_secret_val is not None:
            otp_secret_val = str(otp_secret_val)

        otp_enabled_val = user_data.get("otp_enabled", 0)
        if isinstance(otp_enabled_val, (int, str)):
            otp_enabled_val = bool(int(otp_enabled_val))
        else:
            otp_enabled_val = False

        user = User(
            id=user_id_val,
            name=(
                str(user_data.get("name")) if user_data.get("name") is not None else ""
            ),
            password=(
                str(user_data.get("password"))
                if user_data.get("password") is not None
                else ""
            ),
            email=(
                str(user_data.get("email"))
                if user_data.get("email") is not None
                else ""
            ),
            role=str(user_data.get("role", "user")),
            profile_picture=str(user_data.get("profile_picture", "")),
            otp_secret=otp_secret_val,
            otp_enabled=otp_enabled_val,
        )
        # Store user data in Flask g object
        g.current_user_profile = user
        return user

    def get_user_posts(self, user_id):
        posts = get_posts_by_user_id(user_id)
        post_objs = []
        for post in posts:
            comments = [
                Comment(
                    id=int(c.get("id", 0) or 0),
                    post_id=int(post.get("id", 0) or 0),
                    user=str(c.get("user", "")),
                    content=str(c.get("content", "")),
                    profile_picture=str(c.get("profile_picture", "")),
                )
                for c in post.get("comments", [])
            ]
            # Handle likes being None or empty string
            likes_val = post.get("likes", 0)
            if likes_val in (None, ""):
                likes_val = 0
            else:
                likes_val = int(likes_val)
            post_obj = Post(
                id=int(post.get("id", 0) or 0),
                user=str(post.get("user", "")),
                content=str(post.get("content", "")),
                image_url=str(post.get("image_url", "")),
                likes=likes_val,
                comments=comments,
                like_user_ids=str(post.get("like_user_ids", "")),
            )
            post_objs.append(post_obj)
        # Store user posts in Flask g object
        g.user_posts = post_objs
        return post_objs

    def create_entity_from_row(self, hosted_activities_raw, joined_activities_raw):
        hosted_activities = [
            {
                "id": a["id"],
                "activity_name": a["activity_name"],
                "activity_type": a["activity_type"],
                "skills_req": a["skills_req"],
                "date": a["date"],
                "location": a["location"],
                "max_pax": a["max_pax"],
            }
            for a in hosted_activities_raw
        ]
        joined_only_activities = [
            {
                "id": a["id"],
                "activity_name": a["activity_name"],
                "activity_type": a["activity_type"],
                "skills_req": a["skills_req"],
                "date": a["date"],
                "location": a["location"],
                "max_pax": a["max_pax"],
            }
            for a in joined_activities_raw
        ]
        g.user_hosted_activities = hosted_activities
        g.user_joined_activities = joined_only_activities

    def set_user_activities(self, user_id):
        hosted_activities_raw = get_hosted_activities(user_id)
        joined_activities_raw = get_joined_activities(user_id)
        self.create_entity_from_row(hosted_activities_raw, joined_activities_raw)
        # No return

    def update_profile_full(self, user_id, form):
        name = form.name.data
        password = form.password.data
        profile_picture_url = None
        remove_picture = form.remove_profile_picture.data

        # Handle file upload
        if form.profile_picture.data:
            file = form.profile_picture.data
            try:
                file.seek(0)
                image = Image.open(file)
                image.verify()  # Raises if not a valid image
                file.seek(0)  # Reset pointer for saving
            except (UnidentifiedImageError, Exception):
                current_app.logger.error(
                    "Uploaded profile picture is not a valid image."
                )
                return False

            ext = os.path.splitext(secure_filename(file.filename))[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            image_path = os.path.join(
                "presentation", "static", "images", "profile", unique_filename
            )
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            file.save(image_path)
            profile_picture_url = f"/static/images/profile/{unique_filename}"
        elif remove_picture:
            profile_picture_url = ""
        # Password logic
        if password:
            hashed_password = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            if profile_picture_url is not None:
                result = self.update_profile(
                    user_id, name, hashed_password, profile_picture_url
                )
            else:
                result = self.update_profile(user_id, name, hashed_password)
        else:
            user_data = get_user_by_id(user_id)
            current_password = (
                user_data["password"]
                if isinstance(user_data, dict) and "password" in user_data
                else ""
            )
            if profile_picture_url is not None:
                result = self.update_profile(
                    user_id, name, current_password, profile_picture_url
                )
            else:
                result = self.update_profile(user_id, name, current_password)
        return result

    def edit_activity(self, user_id, activity_id, form):
        activity = get_sports_activity_by_id(activity_id)

        def get_val(r, key, default=None):
            if isinstance(r, dict):
                return r.get(key, default)
            return getattr(r, key, default)

        def safe_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        if not activity:
            return False, "Activity not found."
        activity_user_id = safe_int(get_val(activity, "user_id", 0))
        if activity_user_id != user_id:
            return False, "You can only edit activities you created."
        activity_obj = SportsActivity(
            id=safe_int(get_val(activity, "id", 0)),
            user_id=activity_user_id,
            activity_name=str(get_val(activity, "activity_name", "")),
            activity_type=str(get_val(activity, "activity_type", "")),
            skills_req=str(get_val(activity, "skills_req", "")),
            date=str(get_val(activity, "date", "")),
            location=str(get_val(activity, "location", "")),
            max_pax=safe_int(get_val(activity, "max_pax", 0)),
            user_id_list_join=str(get_val(activity, "user_id_list_join", "")),
        )
        if form.validate_on_submit():
            activity_obj.activity_name = form.activity_name.data
            activity_obj.activity_type = form.activity_type.data
            activity_obj.skills_req = form.skills_req.data
            activity_obj.date = form.date.data
            activity_obj.location = form.location.data
            activity_obj.max_pax = form.max_pax.data
            result = update_sports_activity_details(
                activity_obj.id,
                activity_obj.activity_name,
                activity_obj.activity_type,
                activity_obj.skills_req,
                activity_obj.date,
                activity_obj.location,
                activity_obj.max_pax,
                activity_obj.user_id_list_join,
            )
            if result:
                return True, "Activity updated successfully."
            else:
                return False, "Failed to update activity."
        return False, "Invalid form data."

    def edit_post(self, user_id, post_id, form):
        return edit_post(user_id, post_id, form.content.data, form.remove_image.data)

    def leave_activity(self, user_id, activity_id):
        activity = get_sports_activity_by_id(activity_id)

        def get_val(r, key, default=None):
            if isinstance(r, dict):
                return r.get(key, default)
            return getattr(r, key, default)

        def safe_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        if not activity:
            return False, "Activity not found."
        joined_ids = [
            uid.strip()
            for uid in (get_val(activity, "user_id_list_join", "") or "").split(",")
            if uid.strip()
        ]
        if str(user_id) not in joined_ids:
            return False, "You are not a participant in this activity."
        joined_ids.remove(str(user_id))
        new_join_list = ",".join(joined_ids)
        result = update_sports_activity(activity_id, new_join_list)
        if result:
            return True, "Successfully left the activity."
        else:
            return False, "Failed to leave the activity."

    def delete_post(self, user_id, post_id):
        success = delete_post(user_id, post_id)
        if success:
            return True, "Post deleted successfully."
        else:
            return False, "Failed to delete post."

    def generate_otp(self, user_id):
        return generate_otp_for_user(user_id)

    def verify_otp(self, user_id, otp_code):
        return verify_and_enable_otp(user_id, otp_code)

    def disable_otp(self, user_id):
        return disable_otp_by_user_id(user_id)

    def get_profile_display_data(self):
        """
        Retrieve display data for the current user profile

        Returns:
            dict: User profile display information, or None if no user is logged in
        """
        user = g.get("current_user_profile")
        if not user:
            return None

        return {
            "id": user.get_id(),
            "name": user.get_name(),
            "email": user.get_email(),
            "role": user.get_role(),
            "profile_picture": user.get_profile_picture(),
            "otp_enabled": user.get_otp_enabled(),
        }

    def get_user_posts_display_data(self):
        """
        Retrieve display data for the current user's posts

        Returns:
            list: List of user posts display information, or empty list if no posts
        """
        posts = g.get("user_posts", [])
        if not posts:
            return []

        return [
            {
                "id": post.get_id(),
                "user": post.get_user(),
                "content": post.get_content(),
                "image_url": post.get_image_url(),
                "created_at": post.get_created_at(),
                "likes": post.get_likes(),
                "comments_count": len(post.get_comments()),
                "like_user_ids": post.get_like_user_ids(),
            }
            for post in posts
        ]

    def get_user_activities_display_data(self):
        hosted_activities = g.get("user_hosted_activities", [])
        joined_only_activities = g.get("user_joined_activities", [])
        return hosted_activities, joined_only_activities
