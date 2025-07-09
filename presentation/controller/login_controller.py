import os
from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from flask_login import login_user as flask_login_user
from flask_login import logout_user as flask_logout_user
from itsdangerous import URLSafeTimedSerializer

from data_source.user_queries import (
    get_user_by_email,
    get_user_session_token,
    update_user_session_token,
)
from domain.control.login_management import (
    get_user_display_data,
    login_user,
    logout_user,
    process_reset_password,
    process_reset_password_request,
    verify_user_otp,
)
from domain.entity.forms import LoginForm, OTPForm, RequestResetForm, ResetPasswordForm
from domain.entity.user import User

LOGIN_VIEW = "login.login"
BULLETIN_PAGE = "bulletin.bulletin_page"

login_bp = Blueprint(
    "login", __name__, url_prefix="/", template_folder="../templates/login"
)


@login_bp.route("/")
def root_redirect():
    return redirect(url_for(LOGIN_VIEW))


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(BULLETIN_PAGE))

    form = LoginForm()
    if form.validate_on_submit():
        # use form data
        user = login_user(form.email.data, form.password.data)
        if user:
            # Check if email is verified
            if not getattr(user, "email_verified", False):
                form.email.errors.append(
                    "You must verify your email before logging in. Please check your inbox."
                )
                return render_template("login/login.html", form=form)
            # If 2FA is enabled, redirect to OTP verification page
            if getattr(user, "otp_enabled", False):
                session["pre_2fa_user_id"] = user.id
                session["pre_2fa_user_email"] = user.email
                return redirect(url_for("login.otp_verify"))
            # Else perform normal login
            session.clear()  # Force new session on login
            session["init"] = os.urandom(16).hex()  # Force new session file/ID
            session_token = os.urandom(32).hex()
            session["session_token"] = session_token
            update_user_session_token(user.id, session_token)
            flask_login_user(user)
            session["created_at"] = datetime.now(
                timezone.utc
            ).isoformat()  # After user authenticated, time stamp is set
            session["last_activity"] = datetime.now(timezone.utc).isoformat()
            if user.role == "admin":
                return redirect(url_for("admin.bulletin_page"))
            else:
                return redirect(url_for(BULLETIN_PAGE))
        # invalid credentials
        form.email.errors.append("Invalid email or password.")
    # either GET or validation failed
    return render_template("login/login.html", form=form)


@login_bp.route("/logout")
@login_required
def logout():
    logout_user()
    if hasattr(current_user, "id"):
        update_user_session_token(current_user.id, None)
    session.clear()
    return redirect(url_for(LOGIN_VIEW))


@login_bp.route("/otp_verify", methods=["GET", "POST"])
def otp_verify():
    user_id = session.get("pre_2fa_user_id")
    user_email = session.get("pre_2fa_user_email")
    if not user_id or not user_email:
        return redirect(url_for(LOGIN_VIEW))
    user_data = get_user_by_email(user_email)
    if not user_data or not user_data.get("otp_secret"):
        flash("OTP setup not found. Please login again.")
        return redirect(url_for(LOGIN_VIEW))

    form = OTPForm()
    if form.validate_on_submit():
        otp_code = form.otp_code.data
        from domain.entity.user import User

        user = User(
            id=user_data["id"],
            name=user_data["name"],
            password=user_data["password"],
            email=user_data["email"],
            role=user_data.get("role", "user"),
            profile_picture=user_data.get("profile_picture", ""),
            otp_secret=user_data.get("otp_secret"),
            otp_enabled=bool(int(user_data.get("otp_enabled", 0))),
        )
        verified = verify_user_otp(user, otp_code)
        if verified:
            session.clear()  # Force new session after 2FA so that hackers cannot use the same session ID even in 2FA fails
            session["init"] = os.urandom(16).hex()  # Force new session file/ID
            session_token = os.urandom(32).hex()
            session["session_token"] = session_token
            update_user_session_token(user.id, session_token)
            flask_login_user(user)
            session.pop("pre_2fa_user_id", None)
            session.pop("pre_2fa_user_email", None)
            session["created_at"] = datetime.now(timezone.utc).isoformat()
            session["last_activity"] = datetime.now(timezone.utc).isoformat()
            if user.role == "admin":
                return redirect(url_for("admin.bulletin_page"))
            else:
                return redirect(url_for(BULLETIN_PAGE))
        else:
            flash("Invalid OTP code. Please try again.")
    return render_template("login/login_otp.html", form=form)


@login_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        process_reset_password_request(form.email.data)
        flash(
            "If your email is registered, you will receive a password reset link.",
            "info",
        )
        return redirect(url_for("login.login"))
    return render_template("reset_password_request.html", form=form)


@login_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    return process_reset_password(token, form)
