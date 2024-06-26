from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Optional, Type

from sqlalchemy.orm import Session

from models import *
from schemas import UserCreate, UserUpdate
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Dict, Any, List
from passlib.context import CryptContext


def add_roles_if_not_exists(db: Session):
    # Fetch all existing roles as Role objects, not just the names
    existing_roles = db.query(Role).all()

    # Create a set of existing role names for easy lookup
    existing_role_names = {role.RoleName for role in existing_roles}

    roles_to_add = [
        Role(RoleName="Super Admin", Description="Manages the whole system"),
        Role(RoleName="Admin", Description="Manages a specific LOB or department"),
        Role(
            RoleName="Instructor",
            Description="Manages own courses and can propose new ones",
        ),
        Role(RoleName="Employee", Description="Can view and enroll in courses"),
    ]

    # Add new roles only if they are not already present
    for role in roles_to_add:
        if role.RoleName not in existing_role_names:
            db.add(role)

    db.commit()  # Commit all changes at once


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users_by_filter(db: Session, filters: Dict[str, Any]) -> list[Type[User]]:
    query = db.query(User)
    conditions = []
    for attr, condition in filters.items():
        column = getattr(User, attr)
        if isinstance(condition, dict):
            for operator, value in condition.items():
                if operator == "eq":
                    conditions.append(column == value)
                elif operator == "lt":
                    conditions.append(column < value)
                elif operator == "gt":
                    conditions.append(column > value)
                # Add more operators as needed
        else:
            conditions.append(column == condition)
    return query.filter(and_(*conditions)).all()


def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        try:
            if db_user.dp_file_id:
                db_user.dp_file_id = user["dp_file_id"]
            if db_user.email:
                db_user.email = user["email"]
            if db_user.designation:
                db_user.designation = user["designation"]
            if db_user.service_line_id:
                db_user.service_line_id = user["service_line_id"]
            db.commit()
            db.refresh(db_user)
        except Exception as e:
            db.rollback()
            raise e
        return db_user


def delete_user(db: Session, user_id: int) -> User:
    db_user = (
        db.query(User)
        .options(joinedload(User.counselor))
        .filter(User.id == user_id)
        .first()
    )
    if db_user:
        try:
            # Remove or update related records
            db.query(Enrollment).filter(Enrollment.user_id == user_id).delete()
            db.query(Feedback).filter(Feedback.user_id == user_id).delete()
            db.query(association_table).filter(
                association_table.c.user_id == user_id
            ).delete()
            db.query(user_learning_paths).filter(
                user_learning_paths.c.user_id == user_id
            ).delete()

            # Handle team members (set their counselor_id to NULL)
            db.query(User).filter(User.counselor_id == user_id).update(
                {User.counselor_id: None}
            )

            # Now delete the user
            db.delete(db_user)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[Type[User]]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    from auth import get_password_hash

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.password = pwd_context.hash(user.password)
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def enroll_users(course_id: int, user_ids: list[int], db: Session) -> dict:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for user_id in user_ids:
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id,
            enroll_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=course.expected_time_to_complete),
            year=datetime.now().year,
            status="Enrolled",
        )
        db.add(enrollment)
    db.commit()
    return {
        "message": "Users successfully enrolled",
        "course_id": course_id,
        "user_ids": user_ids,
    }


def enroll_users_lp(learning_path_id: int, user_id: int, due_date: datetime, db: Session) -> dict:
    lp = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = LearningPathEnrollment(
        user_id=user_id,
        learning_path_id=learning_path_id,
        enroll_date=datetime.now(),
        due_date=due_date,
        year=datetime.now().year,
        status="Enrolled",
    )
    db.add(enrollment)
    db.commit()
    return {
        "message": "Users successfully enrolled",
        "course_id": learning_path_id,
        "user_ids": user_id,
    }
