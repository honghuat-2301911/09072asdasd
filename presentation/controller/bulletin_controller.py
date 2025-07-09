# controller.py
import functools

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from domain.control.bulletin_management import (
    create_activity,
    get_bulletin_display_data,
    get_bulletin_listing,
    get_filtered_bulletins,
    get_host_name,
    join_activity_control,
    search_bulletin,
)
from domain.entity.forms import FilterForm, HostForm, JoinForm, SearchForm

BULLETIN_TEMPLATE = "bulletin/bulletin.html"
BULLETIN_PAGE = "bulletin.bulletin_page"


bulletin_bp = Blueprint(
    "bulletin", __name__, url_prefix="/", template_folder="../templates"
)


def user_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != "user":
            return redirect(url_for("admin.bulletin_page"))
        return func(*args, **kwargs)

    return wrapper


@bulletin_bp.route("/bulletin", methods=["GET", "POST"])
@login_required
@user_required
def bulletin_page():
    search_form = SearchForm()
    filter_form = FilterForm()

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
            BULLETIN_TEMPLATE,
            bulletin_list=[],
            error=error,
            query=query,
            search_form=search_form,
            filter_form=filter_form,
            host_form=HostForm(),
            join_form=JoinForm(),
        )

    bulletin_list = get_bulletin_display_data()
    return render_template(
        BULLETIN_TEMPLATE,
        bulletin_list=bulletin_list,
        query=query,
        search_form=search_form,
        filter_form=filter_form,
        host_form=HostForm(),
        join_form=JoinForm(),
    )


@bulletin_bp.route("/join", methods=["POST"])
@login_required
@user_required
def join_activity():
    join_form = JoinForm()
    if not join_form.validate_on_submit():
        flash("Invalid request to join.", "error")
        return redirect(url_for(BULLETIN_PAGE))

    activity_id = join_form.activity_id.data
    if get_host_name(activity_id):
        flash("You can't join the activities you are hosting", "error")
        return redirect(url_for(BULLETIN_PAGE))

    user_id = int(current_user.get_id())
    if not join_activity_control(activity_id, user_id):
        flash("Failed to join the activity. You may have already joined.", "error")
    else:
        flash(
            "Successfully joined the activity! You may view it in your profile",
            "success",
        )
    return redirect(url_for(BULLETIN_PAGE))


@bulletin_bp.route("/host", methods=["POST"])
@login_required
@user_required
def host_activity():
    host_form = HostForm()
    if not host_form.validate_on_submit():
        # grab first error message
        msg = next(iter(host_form.errors.values()))[0]
        flash(f"Host form error: {msg}", "error")
        return redirect(url_for(BULLETIN_PAGE))

    success = create_activity(
        host_form.activity_name.data,
        host_form.activity_type.data,
        host_form.skills_req.data,
        host_form.date.data,
        host_form.location.data,
        host_form.max_pax.data,
        int(current_user.get_id()),
    )

    if not success:
        flash("Could not create activity. Please try again.", "error")
    else:
        flash("Activity created successfully!", "success")
    return redirect(url_for(BULLETIN_PAGE))


@bulletin_bp.route("/bulletin/filtered", methods=["POST"])
@login_required
@user_required
def filtered_bulletin():
    filter_form = FilterForm()
    if not filter_form.validate_on_submit():
        flash("Invalid filter submission.", "error")
        return redirect(url_for(BULLETIN_PAGE))

    s = filter_form.sports_checkbox.data
    ns = filter_form.non_sports_checkbox.data

    if not s and not ns:
        return render_template(
            BULLETIN_TEMPLATE,
            bulletin_list=[],
            error="Please select at least one category to filter.",
            search_form=SearchForm(),
            filter_form=filter_form,
            host_form=HostForm(),
            join_form=JoinForm(),
        )

    result = get_filtered_bulletins(s, ns)
    if not result:
        return render_template(
            BULLETIN_TEMPLATE,
            bulletin_list=[],
            error="No activities found for the selected categories.",
            search_form=SearchForm(),
            filter_form=filter_form,
            host_form=HostForm(),
            join_form=JoinForm(),
        )

    bulletin_list = get_bulletin_display_data()
    return render_template(
        BULLETIN_TEMPLATE,
        bulletin_list=bulletin_list,
        search_form=SearchForm(),
        filter_form=filter_form,
        host_form=HostForm(),
        join_form=JoinForm(),
    )
