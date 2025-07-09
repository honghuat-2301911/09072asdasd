import bcrypt

"""Hash plaintext password using bcrypt"""


def hash_password(plain_text_password: str) -> str:
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password (result is in bytes)
    hashed = bcrypt.hashpw(plain_text_password.encode("utf-8"), salt)
    # Return as a decoded string for storage (e.g. in MySQL)
    return hashed.decode("utf-8")


"""Check if a plaintext password matches the given bcrypt hash"""


def check_password(plain_text_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_text_password.encode("utf-8"), hashed_password.encode("utf-8")
    )
