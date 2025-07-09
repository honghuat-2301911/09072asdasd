import functools

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from domain.control.admin_management import remove_social_post, remove_sports_activity
from domain.control.bulletin_management import (
    get_bulletin_display_data,
    get_bulletin_listing,
    search_bulletin,
)
from domain.control.social_feed_management import get_all_posts_control
from domain.entity.forms import DeleteActivityForm, DeletePostForm, SearchForm

ADMIN_BULLETIN_PAGE = "admin.bulletin_page"  # Name of the admin bulletin page route


# Create a blueprint for the admin page
admin_bp = Blueprint(
    "admin", __name__, url_prefix="/admin", template_folder="../templates"
)


def admin_required(func):
    """
    Custom decorator to check if the current user is authenticated and is an admin.
    This decorator should only be used to protect admin routes.
    """

    @functools.wraps(func)
    def admin_check(*args, **kwargs):
        # Check if the user is logged in and is an admin
        if current_user.role != "admin":
            # Redirect to a different page if not admin
            return redirect(url_for("bulletin.bulletin_page"))
        return func(
            *args, **kwargs
        )  # Call the original function if authenticated as admin

    return admin_check  # Return the wrapped function


@admin_bp.route("/bulletin", methods=["GET", "POST"])
@login_required
@admin_required
def bulletin_page():
    search_form = SearchForm()
    delete_activity_form = DeleteActivityForm()

    query = None
    if search_form.validate_on_submit():
        query = search_form.query.data
        result = search_bulletin(query)
    else:
        result = get_bulletin_listing()

    # No results or validation error on search?
    if not result and (query or search_form.errors):
        error = search_form.errors.get("query", ["No activities found."])[0]
        return render_template(
            "admin/bulletin.html",
            bulletin_list=[],
            error=error,
            query=query,
            search_form=search_form,
            delete_activity_form=delete_activity_form,
        )

    bulletin_list = get_bulletin_display_data()
    return render_template(
        "admin/bulletin.html",
        bulletin_list=bulletin_list,
        query=query,
        search_form=search_form,
        delete_activity_form=delete_activity_form,
    )


@admin_bp.route("/delete_activity", methods=["POST"])
@login_required
@admin_required
def delete_activity():
    form = DeleteActivityForm()
    if not form.validate_on_submit():
        flash("Invalid or missing CSRF token.", "error")
        return redirect(url_for(ADMIN_BULLETIN_PAGE))

    activity_id = form.activity_id.data
    if not activity_id:
        flash("Activity ID is required.", "error")
        return redirect(url_for(ADMIN_BULLETIN_PAGE))

    success = remove_sports_activity(activity_id)
    if success:
        flash("Activity deleted successfully.", "success")
    else:
        flash(
            "Failed to delete the activity. It may not exist or you may not have permission.",
            "error",
        )
    return redirect(url_for(ADMIN_BULLETIN_PAGE))


@admin_bp.route("/feed", methods=["GET", "POST"])
@login_required
@admin_required
def feed_page():
    posts = get_all_posts_control()
    delete_forms = {post.id: DeletePostForm(post_id=post.id) for post in posts}
    return render_template(
        "admin/social_feed.html", posts=posts, delete_forms=delete_forms
    )


@admin_bp.route("/delete_post", methods=["POST"])
@login_required
@admin_required
def delete_post():
    form = DeletePostForm()
    if not form.validate_on_submit():
        flash("Invalid delete request.", "error")
        return redirect(url_for("admin.feed_page"))

    post_id = form.post_id.data
    success = remove_social_post(post_id)
    if success:
        flash("Post deleted successfully.", "success")
    else:
        flash(
            "Failed to delete the post. It may not exist or you may not have permission.",
            "error",
        )
    return redirect(url_for("admin.feed_page"))
