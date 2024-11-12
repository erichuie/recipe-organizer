from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..schemas.pydantic_schemas import UserCreation, UpdateUser

from . import models
from src.auth.helpers import get_hash, generate_random_password

def create_user(db: Session, user: UserCreation):
    password = generate_random_password()
    hashed_password = get_hash(password)
    db_user = models.User(name=user.name, email=user.email,
                          password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int):
    stmt = select(models.User).where(models.User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

def get_user_by_username(db: Session, name: str):
    stmt = select(models.User).where(models.User.name == name)
    return db.execute(stmt).scalar_one_or_none()

def get_user_by_email(db: Session, email: str):
    stmt = select(models.User).where(models.User.email == email)
    return db.execute(stmt).scalar_one_or_none()

def get_users(db: Session, limit: int = 100):
    stmt = select(models.User).limit(limit)
    return db.execute(stmt).scalars().all()

def update_user(db: Session, user, update_user):
    if(not isinstance(update_user, dict)):
        update_user = update_user.dict(exclude_unset=True)
    for key, value in update_user.items():
        print(key)
        if(key == "password"):
            value = get_hash(value)
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    if "password" in update_user:
        del update_user["password"]
    return update_user

def delete_user(db:Session, user: UserCreation):
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}