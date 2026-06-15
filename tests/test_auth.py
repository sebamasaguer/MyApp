def test_hash_and_verify_password():
    from auth import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert verify_password("mysecretpassword", hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_and_decode_token():
    from auth import create_token, decode_token
    token = create_token(user_id=42)
    assert decode_token(token) == 42

def test_invalid_token_returns_none():
    from auth import decode_token
    assert decode_token("not-a-valid-token") is None

def test_tampered_token_returns_none():
    from auth import create_token, decode_token
    token = create_token(user_id=1)
    tampered = token[:-5] + "XXXXX"
    assert decode_token(tampered) is None
