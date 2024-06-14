from fastapi import APIRouter

from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

import auth
import crud
from auth import oauth2_scheme
from dependencies import get_db
from schemas import UserCreate, UserInDB, UserUpdate

app = APIRouter(prefix='/um', tags=['User Management'])


@app.post("/users/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token.replace("Bearer ", "")
    token_data = auth.verify_token(token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    db_user = crud.get_user_by_email(db, email=user.Email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/{user_id}", response_model=UserInDB)
def read_user(user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token.replace("Bearer ", "")
    token_data = auth.verify_token(token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    if logged_in_user.Role != "Admin":
        raise HTTPException(status_code=404, detail="unauthorised ")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=UserInDB)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token.replace("Bearer ", "")
    token_data = auth.verify_token(token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    db_user = crud.update_user(db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", response_model=UserInDB)
def delete_user(user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
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
