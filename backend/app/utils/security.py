import re

import bcrypt

PASSWORD_RULE_MESSAGE = (
    "Password must be at least 8 characters and include one uppercase letter, "
    "one number, and one special character"
)
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
)


def normalize_email(value: str) -> str:
    """Store and compare emails in lowercase."""
    return value.strip().lower()


def validate_password_strength(password: str) -> str:
    """Raise ValueError when the password does not meet policy."""
    if not PASSWORD_PATTERN.match(password):
        raise ValueError(PASSWORD_RULE_MESSAGE)
    return password


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
