import random
import string

from app.models import ShortURL


def generate_short_code(length=6) -> str:
    chars = string.ascii_letters + string.digits
    for _ in range(10):
        code = "".join(random.choices(chars, k=length))
        if not ShortURL.select().where(ShortURL.short_code == code).exists():
            return code
    return "".join(random.choices(chars, k=length + 2))
