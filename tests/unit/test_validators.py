from app.utils.validators import is_valid_email, is_valid_url, is_valid_username


def test_valid_url_passes():
    assert is_valid_url("https://example.com") is True


def test_valid_url_with_path_passes():
    assert is_valid_url("https://example.com/path/to/page") is True


def test_invalid_url_rejects():
    assert is_valid_url("not-a-url") is False


def test_empty_url_rejects():
    assert is_valid_url("") is False


def test_valid_email_passes():
    assert is_valid_email("user@example.com") is True


def test_invalid_email_rejects():
    assert is_valid_email("not-an-email") is False


def test_empty_email_rejects():
    assert is_valid_email("") is False


def test_valid_username_passes():
    assert is_valid_username("hello_world") is True


def test_username_alphanumeric_passes():
    assert is_valid_username("user123") is True


def test_username_with_spaces_rejects():
    assert is_valid_username("has spaces") is False


def test_username_integer_rejects():
    assert is_valid_username(12345) is False


def test_username_empty_string_rejects():
    assert is_valid_username("") is False
