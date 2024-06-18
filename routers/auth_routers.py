from datetime import timedelta
from typing import Annotated, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import auth
import crud
import schemas
from auth import oauth2_scheme
from dependencies import get_db
from models import User
from schemas import UserCreate, UserInDB
import requests
from fastapi import FastAPI, Request, HTTPException, Header, Body

app = APIRouter(prefix="/auth", tags=["auth"])


@app.post("/token")
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = auth.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response = JSONResponse(
        status_code=200, content={"access_token": access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",  # Ensure this is set to 'none'
        secure=True,
    )
    return response

    # return user


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
def read_users_me(
    response: Response,
    authorization: Annotated[Union[str, None], Header()] = None,
    db: Session = Depends(get_db),
):
    print("calling token_auth")
    token = token_auth(authorization)
    print("got token from token_auth", token)
    token_data = auth.verify_token(token)
    print("after verifying", token_data.username)
    user = crud.get_user_by_email(db, email=token_data.username)
    print("returning user", user.email)
    return user


def token_auth(authorization):
    print("Inside token_auth")
    if not authorization:
        print("No Authorization, Raising Exception")
        raise HTTPException(status_code=400, detail="Authorization Is Required")
    # Getting token from the header
    access_token = authorization.replace("Bearer ", "")
    print("Returning access token", access_token)
    return access_token
