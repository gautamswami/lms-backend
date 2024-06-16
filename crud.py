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
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.dp_file_id=user.dp_file_id
        db_user.email = user.email
        db_user.designation=user.designation
        db_user.role_name = user.role_name
        db_user.service_line_id = user.service_line_id
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[Type[User]]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    from auth import get_password_hash
    db_user = User(dp_file_id=user.dp_file_id,
                first_name=user.first_name,
                   last_name=user.last_name,
                   email=user.Email,
                   password=get_password_hash(user.password),
                   employee_id=user.employee_id,
                   designation=user.designation,
                   role_name=user.role_name,
                   service_line_id=user.service_line_id,       

                   )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
