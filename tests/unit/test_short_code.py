from app.utils.short_code import generate_short_code


def test_short_code_length_is_six():
    code = generate_short_code()
    assert len(code) == 6


def test_short_code_is_alphanumeric():
    code = generate_short_code()
    assert code.isalnum()


def test_short_code_is_unique_across_calls():
    codes = {generate_short_code() for _ in range(100)}
    assert len(codes) == 100
