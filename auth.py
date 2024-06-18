from datetime import datetime, timedelta

from fastapi import HTTPException, status, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from dependencies import get_db
from models import User
from schemas import TokenData
from typing import Annotated, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response, status, Cookie

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key_1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    authorization: Annotated[Union[str, None], Header()] = None,
    db: Session = Depends(get_db),
):
    # async def get_current_user(
    #     token: Union[str, None] = Cookie(None), db: Session = Depends(get_db)
    # ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        access_token = authorization.replace("Bearer ", "")
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        # username = "admin@abc.com"
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str):
    from crud import get_user_by_email

    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=500)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        print("token: ", token)
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        print("payload: ", payload)
        username: str = payload.get("sub")
        print("username: ", username)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def create_password_reset_token(email: str):
    expires_delta = timedelta(hours=1)  # Token valid for 1 hour
    return create_access_token(data={"sub": email}, expires_delta=expires_delta)
