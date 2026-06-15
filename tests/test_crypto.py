def test_encrypt_decrypt():
    from crypto import encrypt, decrypt
    plaintext = "my-telegram-token-123"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext

def test_different_values_produce_different_ciphertext():
    from crypto import encrypt
    assert encrypt("token-a") != encrypt("token-b")

def test_encrypt_is_not_deterministic():
    from crypto import encrypt
    # Fernet incluye timestamp+nonce, así que dos cifrados del mismo texto difieren
    assert encrypt("same") != encrypt("same")
