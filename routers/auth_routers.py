from datetime import timedelta
from typing import Annotated, Union

from fastapi import APIRouter, Depends, Response, status
from fastapi import HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import crud
import schemas
from dependencies import get_db
from models import User, AppStatus
from schemas import Token, UserDisplay

app = APIRouter(prefix="/auth", tags=["auth"])


@app.post("/token", response_model=Token)
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
    app_status = db.query(AppStatus).first()

    return Token(
        **{
            "access_token": access_token,
            "token_type": "bearer",
            "user_details": UserDisplay.from_orm(user),
            "app_status": app_status.status_update
        }
    )

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
@app.get("/users/me", response_model=schemas.UserDisplay)
def read_users_me(
        response: Response,
        authorization: Annotated[
            Union[str, None], Header()
        ] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTcxODc5NDEzOX0.IzHb87ebl9lr0MIzJK-8hRFlVf8ZI8ubFq1eHUzS8F4",
        db: Session = Depends(get_db),
):
    print("calling token_auth", authorization)
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
