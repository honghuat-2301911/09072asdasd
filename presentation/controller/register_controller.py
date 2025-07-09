import bcrypt
from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from itsdangerous import URLSafeTimedSerializer

from domain.control.register import (
    register_user,
    send_verification_email,
    update_verification_status,
)
from domain.entity.forms import RegisterForm

register_bp = Blueprint(
    "register", __name__, url_prefix="/", template_folder="../templates/"
)


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Prepare user data
        hashed = bcrypt.hashpw(
            form.password.data.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user_data = {
            "name": form.name.data,
            "email": form.email.data,
            "password": hashed,
            "role": "user",
        }

        if register_user(user_data):
            send_verification_email(form.email.data)
            return render_template("register/verify_email.html", email=form.email.data)

        flash("Something went wrong. Please try again.", "error")
        return redirect(url_for("register.register"))

    # If GET or validation failed, render form with errors
    return render_template("register/register.html", form=form)


@register_bp.route("/verify/<token>")
def verify_email(token):
    success, result = update_verification_status(token)
    if success:
        flash("Your email has been verified! You can now log in.", "success")
    else:
        flash(result, "danger")
    return redirect(url_for("login.login"))
