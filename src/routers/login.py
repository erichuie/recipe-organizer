from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from sqlalchemy.orm import Session
from src.auth.helpers import authenticate_user, create_access_token, oauth2_scheme, blacklist_token, verify_user_logged_in
from src.db.database import get_db
from src.schemas.pydantic_schemas import Token

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
    ):
    """
    Authenticates user credentials using a username and passwordinputted by user.
    Returns an access token to be sent in with other requests that require authentication.

    """

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id
        },
        type="login",
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout", dependencies=[Depends(verify_user_logged_in)])
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Logs the user out from platform by blacklisting token passed.
    Requires Bearer token auth.
    """
    blacklist_token(token)
    return {"msg": "Successfully logged out."}
