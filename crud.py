from typing import Optional, Type

from sqlalchemy.orm import Session

from models import User, Role
from schemas import UserCreate, UserUpdate


def add_roles_if_not_exists(db: Session):
    existing_roles = db.query(Role.RoleName).all()  # Fetch all existing role names
    existing_roles = [role.RoleName for role in existing_roles]  # Flatten the list of tuples

    roles_to_add = [
        Role(RoleName='Super Admin', Description='Manages the whole system'),
        Role(RoleName='Admin', Description='Manages a specific LOB or department'),
        Role(RoleName='Instructor', Description='Manages own courses and can propose new ones'),
        Role(RoleName='Employee', Description='Can view and enroll in courses')
    ]

    for role in roles_to_add:
        if role.RoleName not in existing_roles:
            db.add(role)  # Only add the role if it's not already in the database

    db.commit()  # Commit all the new roles at once


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.UserID == user_id).first()


def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(User).filter(User.UserID == user_id).first()
    if db_user:
        db_user.UserName = user.UserName
        db_user.Email = user.Email
        db_user.Role = user.Role
        db_user.Credits = user.Credits
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.UserID == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[Type[User]]:
    return db.query(User).filter(User.Email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    from auth import get_password_hash
    db_user = User(UserName=user.UserName,
                   Email=user.Email,
                   Password=get_password_hash(user.Password),
                   Role=user.Role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
