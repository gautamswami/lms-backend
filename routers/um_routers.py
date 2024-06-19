import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, BackgroundTasks, Header
from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

import auth
import crud
from auth import oauth2_scheme
from config import EMAIL_ADDRESS, EMAIL_PASSWORD
from dependencies import get_db
from schemas import UserCreate, UserUpdate, UserDisplay
from typing import Annotated, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response, status, Cookie

app = APIRouter(prefix="/um", tags=["User Management"])


def send_reset_email(email: str, token: str):
    msg = EmailMessage()
    msg.set_content(f"Please use the following link to reset your password: \n{token}")

    msg["Subject"] = "Reset Your Password"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


@app.post("/users/forgot-password/")
def forgot_password(
    email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """

    :type db: object
    :type email: object
    :type background_tasks: object
    """
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = auth.create_password_reset_token(email=email)
    background_tasks.add_task(send_reset_email, email, token)
    return {"message": "Check your email for the reset link"}


@app.post("/users/reset-password/")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=400, detail="Invalid token")
    try:
        email = auth.verify_token(token).username
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.Password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password has been reset successfully"}


@app.post("/users/", response_model=UserDisplay, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    authorization: Annotated[
        Union[str, None], Header()
    ] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTcxODc5NDEzOX0.IzHb87ebl9lr0MIzJK-8hRFlVf8ZI8ubFq1eHUzS8F4",
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = authorization.replace("Bearer ", "")
    print("\n\n\nGot Access token")
    token_data = auth.verify_token(access_token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/{user_id}", response_model=UserDisplay)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    authorization: Annotated[
        Union[str, None], Header()
    ] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTcxODc5NDEzOX0.IzHb87ebl9lr0MIzJK-8hRFlVf8ZI8ubFq1eHUzS8F4",
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = authorization.replace("Bearer ", "")
    token_data = auth.verify_token(access_token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    print(logged_in_user.email, logged_in_user.role_name)
    if logged_in_user.role_name != "Admin":
        raise HTTPException(status_code=404, detail="unauthorised ")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=UserDisplay)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    authorization: Annotated[
        Union[str, None], Header()
    ] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTcxODc5NDEzOX0.IzHb87ebl9lr0MIzJK-8hRFlVf8ZI8ubFq1eHUzS8F4",
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = authorization.replace("Bearer ", "")
    token_data = auth.verify_token(access_token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    print(user.__dict__)
    update_data = user.dict(exclude_unset=True)
    db_user = crud.update_user(db, user_id=user_id, user=update_data)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", response_model=UserDisplay)
def delete_user(
    user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token.replace("Bearer ", "")
    token_data = auth.verify_token(token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
