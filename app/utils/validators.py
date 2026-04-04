import re

import validators


def is_valid_url(url: str) -> bool:
    return bool(validators.url(url))


def is_valid_email(email: str) -> bool:
    return bool(validators.email(email))


def is_valid_username(username: str) -> bool:
    if not isinstance(username, str):
        return False
    return bool(re.match(r"^[\w]{1,150}$", username))
