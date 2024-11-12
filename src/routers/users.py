from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth.helpers import verify_user_logged_in
from src.db import crud
from src.db.database import get_db
from src.schemas.pydantic_schemas import UpdateUser, UserCreation, UserInDB, UserInfo

router = APIRouter()


@router.post("/users", status_code=201, response_model=UserCreation, dependencies=[Depends(verify_user_logged_in)]) #, dependencies=[Depends(verify_user_logged_in)] is for non admin users
def create_user(user: UserCreation, db: Session = Depends(get_db)):
    """
    Create a new user account. Requires Bearer token auth and admin role.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.get("/users", response_model=list[UserInfo], dependencies=[Depends(verify_user_logged_in)]) #, dependencies=[Depends(verify_user_logged_in)] is for non admin users
def read_users(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of all user accounts including admins. Requires Bearer token auth and admin role.
    """
    users = crud.get_users(db, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserInfo, dependencies=[Depends(verify_user_logged_in)]) #, dependencies=[Depends(verify_user_logged_in)] is for non admin users
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user account corresponding to the id. Return 404 code if not found. Requires Bearer token auth and admin role.
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", dependencies=[Depends(verify_user_logged_in)]) #, dependencies=[Depends(verify_user_logged_in)] is for non admin users
def update_user(user_id: int, update_user: UpdateUser, db: Session = Depends(get_db)):
    """
    Update user account information corresponding to the id. Return 404 code if not found. Requires Bearer token auth and admin role.
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db=db, user=db_user, update_user=update_user)


@router.delete("/users/{user_id}", dependencies=[Depends(verify_user_logged_in)]) #, dependencies=[Depends(verify_user_logged_in)] is for non admin users
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Sets user account status to 'deleted' corresponding to the id. Return 404 code if not found. Requires Bearer token auth and admin role.
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.delete_user(db=db, user=db_user)

