from datetime import timedelta
from typing import Annotated, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import crud
import schemas
from auth import oauth2_scheme
from dependencies import get_db
from models import User
from schemas import UserCreate, UserInDB

app = APIRouter(prefix='/auth', tags=['auth'])


@app.post("/token", response_model=schemas.UserBase)
def login_for_access_token(response: Response,
                           form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.Email}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",  # Ensure this is set to 'none'
        secure=True
    )
    # return {"access_token": access_token, "token_type": "bearer"}

    return user


@app.post("/register", response_model=schemas.UserDisplay)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    counselor = db.query(User).filter(User.id == user.counselor_id).first()
    if not counselor or counselor.role_name != "Instructor":
        raise HTTPException(status_code=400, detail="Invalid counselor")

    return crud.create_user(db=db, user=user)


# @app.get("/users/me", response_model=schemas.UserBase)
# def read_users_me(
#     db: Session = Depends(get_db),
#     access_token: Union[str, None] = Cookie(None)
# ):
@app.get("/users/me", response_model=schemas.UserBase)
def read_users_me(response: Response, access_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(access_token)
    if access_token:
        token = access_token.replace("Bearer ", "")
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        token_data = auth.verify_token(token)
        user = crud.get_user_by_email(db, email=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    else:
        return {
            "UserName": "NONE",
            "Email": "NONE",
            "Role": "NONE"
        }