import base64
import io

import pyotp
import pyqrcode

from data_source.user_queries import enable_2fa, get_user_by_id, set_otp_secret


def generate_otp_for_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None, "User not found"

    otp_secret = pyotp.random_base32()
    if not set_otp_secret(otp_secret, user_id):
        return None, "Failed to update user with OTP secret"

    uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(
        name=user["email"], issuer_name="BuddiesFinders"
    )
    qr = pyqrcode.create(uri)
    buffer = io.BytesIO()
    qr.png(buffer, scale=5)
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    qr_data_url = f"data:image/png;base64,{qr_b64}"

    return {"qr": qr_data_url, "secret": otp_secret}, None


def verify_and_enable_otp(user_id, otp_code):
    user = get_user_by_id(user_id)
    if not user or not user.get("otp_secret"):
        return False, "No OTP secret set"
    totp = pyotp.TOTP(user["otp_secret"])
    if totp.verify(otp_code):
        if enable_2fa(user_id):
            return True, None
        else:
            return False, "Failed to enable 2FA"
    return False, "Invalid OTP code"
