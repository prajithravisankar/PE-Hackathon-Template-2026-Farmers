from unittest.mock import patch, MagicMock

from app.utils.short_code import generate_short_code


@patch("app.utils.short_code.ShortURL")
def test_short_code_length_is_six(mock_model):
    mock_model.select.return_value.where.return_value.exists.return_value = False
    code = generate_short_code()
    assert len(code) == 6


@patch("app.utils.short_code.ShortURL")
def test_short_code_is_alphanumeric(mock_model):
    mock_model.select.return_value.where.return_value.exists.return_value = False
    code = generate_short_code()
    assert code.isalnum()


@patch("app.utils.short_code.ShortURL")
def test_short_code_is_unique_across_calls(mock_model):
    mock_model.select.return_value.where.return_value.exists.return_value = False
    codes = {generate_short_code() for _ in range(100)}
    assert len(codes) == 100
