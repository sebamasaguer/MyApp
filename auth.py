import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_token(user_id: int, remember: bool = False) -> str:
    expire = datetime.now(timezone.utc) + (
        timedelta(days=30) if remember else timedelta(hours=8)
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, os.environ["SECRET_KEY"], algorithms=["HS256"]
        )
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
