"""User login management for authentication and session handling"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import pyotp
from flask import current_app, flash, g, redirect, render_template, url_for
from flask_login import login_user as flask_login_user
from flask_login import logout_user as flask_logout_user
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from data_source.user_queries import (
    clear_failed_logins,
    delete_reset_password,
    get_id_by_email,
    get_user_by_email,
    get_user_by_token_hash,
    get_user_failed_attempts_count,
    insert_into_reset_password,
    record_failed_login,
    update_reset_link_used,
    update_user_lockout,
    update_user_password_by_id,
)
from domain.entity.user import User

FAILED_ATTEMPT_LIMIT = 10
LOCKOUT_MINUTES = 15
LOGIN_VIEW = "login.login"


def login_user(email: str, password: str):
    """
    Attempt to authenticate a user by email and password

    Args:
        email (str): User's email address
        password (str): User's password

    Returns:
        User: The authenticated User object if found, else None
    """
    result = get_user_by_email(email)
    if not result:
        return None

    # Get current time
    utc_plus_8 = timezone(timedelta(hours=8))
    now = datetime.now(utc_plus_8)

    # Check if account is locked
    if result.get("locked_until"):
        db_locked_until = result["locked_until"].replace(tzinfo=utc_plus_8)
        if db_locked_until > now:
            lock_time = db_locked_until.strftime("%Y-%m-%d %H:%M:%S")
            current_app.logger.warning(
                f"Locked account login attempt: {email} (locked until {lock_time})"
            )
            return None

    # Check password hash
    stored_hash = result["password"]
    password_valid = bcrypt.checkpw(
        password.encode("utf-8"), stored_hash.encode("utf-8")
    )

    # If password doesn't match, log failed attempt into DB
    if not password_valid:
        record_failed_login(result["id"])
        # Check failed attempts in past 10 minutes
        recent_failures = get_user_failed_attempts_count(
            result["id"], window_minutes=10
        )
        locked_until = None
        if recent_failures >= FAILED_ATTEMPT_LIMIT:
            locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            update_user_lockout(result["id"], locked_until.replace(tzinfo=None))
            current_app.logger.warning(
                f"Account locked: {email} after {recent_failures} failed attempts in 10 minutes"
            )
        current_app.logger.warning(
            f"Failed login for {email} (attempt {recent_failures}/{FAILED_ATTEMPT_LIMIT})"
        )
        return None

    # On successful login, clear failed logins and unlock account
    clear_failed_logins(result["id"])
    update_user_lockout(result["id"], None)

    user = User(
        id=result["id"],
        name=result["name"],
        password=result["password"],
        email=result["email"],
        role=result.get("role", "user"),
        profile_picture=result.get("profile_picture", ""),
        locked_until=result.get("locked_until"),
        otp_secret=result.get("otp_secret"),
        otp_enabled=bool(int(result.get("otp_enabled", 0))),
        current_session_token=result.get("current_session_token"),
        email_verified=bool(int(result.get("email_verified", 0))),
    )
    # flask_login_user(user)
    return user


# Get generate OTP
def verify_user_otp(user, otp_code):
    """
    Verifies the OTP code for the user.
    Args:
        user (User): The user object
        otp_code (str): The OTP code entered by the user
    Returns:
        bool: True if valid, False otherwise
    """
    if not user.otp_secret:
        return False
    totp = pyotp.TOTP(user.otp_secret)
    return totp.verify(otp_code)


def logout_user():
    """Log out the current user using flask_login"""
    flask_logout_user()


def get_user_display_data():
    """
    Retrieve display data for the currently logged-in user

    Returns:
        dict: User display information, or None if no user is logged in
    """
    user = g.get("current_user")
    if not user:
        return None

    return {
        # "id": user.get_id(),  # Uncomment if you want to display user ID
        "name": user.get_name(),
        "email": user.get_email(),
        "role": user.get_role(),
    }


def process_reset_password_request(email):

    # get user id by email
    if not email:
        return None

    user_id = get_id_by_email(email)

    # generate a unique token for the password reset and store in the database
    if user_id:

        delete_reset_password(user_id)

        token = str(uuid.uuid4())
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        utc_plus_8 = timezone(timedelta(hours=8))
        now = datetime.now(utc_plus_8)
        expires_at = now + timedelta(minutes=60)

        insert_into_reset_password(user_id, token_hash, expires_at.replace(tzinfo=None))

        # Send the reset email with the token
        reset_url = url_for("login.reset_password", token=token, _external=True)
        message = Mail(
            from_email="buddiesfinder@gmail.com",
            to_emails=email,
            subject="Reset Your Password for buddiesfinder",
            html_content=f'<p>Click <a href="{reset_url}">here</a> to reset your password.</p>',
        )
        try:
            api_key = os.getenv("EMAILVERIFICATION_API_KEY")
            sg = SendGridAPIClient(api_key)
            sg.send(message)
        except Exception as e:
            current_app.logger.error(f"Error sending verification email: {e}")


def process_reset_password(token, form):

    if form.validate_on_submit():

        user_token_hash = hashlib.sha256(token.encode()).hexdigest()

        token_data = get_user_by_token_hash(user_token_hash)

        if not token_data:
            flash(
                "Invalid or expired reset link. Please request a new password reset.",
                "danger",
            )
            return redirect(url_for(LOGIN_VIEW))

        if token_data["used"]:
            flash(
                "This reset link has been used. Please request a new password reset.",
                "danger",
            )
            return redirect(url_for(LOGIN_VIEW))

        utc_plus_8 = timezone(timedelta(hours=8))
        now = datetime.now(utc_plus_8)

        expires_at = token_data["expires_at"]
        if isinstance(expires_at, str):
            expires_at_with_timezone = datetime.strptime(
                expires_at, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=utc_plus_8)
        elif expires_at.tzinfo is None:
            expires_at_with_timezone = expires_at.replace(tzinfo=utc_plus_8)
        else:
            expires_at_with_timezone = expires_at.astimezone(utc_plus_8)

        if now > expires_at_with_timezone:
            flash(
                "This reset link has expired. Please request a new password reset.",
                "danger",
            )
            return redirect(url_for(LOGIN_VIEW))

        hashed = bcrypt.hashpw(
            form.password.data.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        update_user_password_by_id(token_data["user_id"], hashed)
        update_reset_link_used(user_token_hash)
        flash("Your password has been updated. You can now log in.", "success")
        return redirect(url_for(LOGIN_VIEW))
    return render_template("reset_password.html", form=form)
