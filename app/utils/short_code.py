import random
import string

from app.models import ShortURL


def generate_short_code(length=6) -> str:
    """Return a short code that is guaranteed unique in the database."""
    chars = string.ascii_letters + string.digits
    current_length = length
    while True:
        code = "".join(random.choices(chars, k=current_length))
        if not ShortURL.select().where(ShortURL.short_code == code).exists():
            return code
        # After every 10 failed attempts at this length, grow by one character
        # so we never spin forever even if the space fills up.
        current_length = min(current_length + 1, 12)
