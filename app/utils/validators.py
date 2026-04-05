import re

import validators


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    return bool(validators.url(url))


def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False
    return bool(validators.email(email))


def is_valid_username(username: str) -> bool:
    if not isinstance(username, str):
        return False
    # Allow word chars (letters, digits, _), dots, and hyphens — common in
    # real-world usernames (e.g. john.doe, jane-doe). Spaces are still rejected.
    return bool(re.match(r"^[\w.\-]{1,150}$", username))
