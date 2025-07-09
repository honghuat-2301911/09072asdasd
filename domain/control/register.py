"""User registration control logic and business rules"""

import os

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from data_source.user_queries import (
    get_user_by_email,
    insert_user,
    update_user_verification_status,
)


def register_user(user_data: dict) -> bool:
    existing_user = get_user_by_email(user_data["email"])
    if existing_user:
        print("User already exists with this email.")
        return False
    return insert_user(user_data)


def send_verification_email(user_email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps(user_email, salt="email-verify")
    verify_url = url_for("register.verify_email", token=token, _external=True)
    message = Mail(
        from_email="buddiesfinder@gmail.com",
        to_emails=user_email,
        subject="Verify Your Email",
        html_content=f'<p>Click to verify: <a href="{verify_url}">{verify_url}</a></p>',
    )
    try:
        api_key = os.getenv("EMAILVERIFICATION_API_KEY")
        sg = SendGridAPIClient(api_key)
        sg.send(message)
    except Exception as e:
        current_app.logger.error(f"Error sending verification email: {e}")


def update_verification_status(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="email-verify", max_age=3600)
        if update_user_verification_status(email):
            return True, email  # Success
        else:
            return False, "User not found or verification update failed."
    except SignatureExpired:
        return False, "Verification link has expired."
    except BadSignature:
        return False, "Verification link is invalid."
    except Exception as e:
        return False, str(e)
