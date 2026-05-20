import uuid
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt

from app.config import settings

# Algoritmo usado para firmar los JWT
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """
    Genera un hash seguro bcrypt para una contraseña en texto plano.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash bcrypt.
    """
    plain_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def create_token(subject: str | uuid.UUID, expires_delta: timedelta, token_type: str) -> str:
    """
    Función base para crear un token JWT con fecha de emisión, expiración, tipo y sujeto.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
        "type": token_type,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_access_token(subject: str | uuid.UUID) -> str:
    """
    Genera un token de acceso JWT (de corta duración).
    """
    return create_token(
        subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(subject: str | uuid.UUID) -> str:
    """
    Genera un token de renovación JWT (de larga duración).
    """
    return create_token(
        subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def verify_token(token: str, expected_type: str) -> str | None:
    """
    Verifica la autenticidad y vigencia de un token JWT.
    Retorna el sujeto (sub) si el token es válido y del tipo esperado, None de lo contrario.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
        subject = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        return None
