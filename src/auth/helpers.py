from datetime import datetime, timedelta, timezone
import string
import secrets
from typing import Union
from fastapi import Depends, HTTPException, Header, status
from typing_extensions import Annotated
import jwt #should use both pyjwt and jwcrypto or change to all jcrypto?
import jwcrypto.jwk
import jwcrypto.jwt
import jwcrypto.jwe
import json
import time
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from src.schemas.pydantic_schemas import TokenData
from src.db.models import User
from src.db.database import get_db, redis_client
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY_LOGIN = os.environ.get('SECRET_KEY_LOGIN')
SECRET_KEY_EMAIL = os.environ.get('SECRET_KEY_EMAIL')
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

#helper methods
def verify_hash(plain_input, hashed_input):
    """Check user input matches the hashed input"""

    return pwd_context.verify(plain_input, hashed_input)

def get_hash(input):
    """Convert the input into a hashed string"""

    return pwd_context.hash(input)

def authenticate_user(db, name: str, password: str):
    """Check the user inputted username and password matches the username and its corresponding
    hashed password queried from database"""

    from src.db.crud import get_user_by_username

    user = get_user_by_username(db, name) #circular import issue?
    if not user:
        return False
    if not verify_hash(password, user.password):
        return False
    return user

def create_access_token(data: dict, type: str, expires_delta: Union[timedelta, None] = None):
    """Create encoded jwt token using pyjwt"""

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update([("exp", expire)])
    if type == "login":
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY_LOGIN, algorithm=ALGORITHM)
    elif type == "email":
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY_EMAIL, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_user_logged_in(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """Authorizes user with valid login token to be allowed to use endpoints
    this function gets dependency injected into"""

    from src.db.crud import get_user_by_id

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        if is_token_blacklisted(token):
            raise HTTPException(status_code=403, detail="Token is blacklisted")
        payload = jwt.decode(token, SECRET_KEY_LOGIN, algorithms=[ALGORITHM])
        print("the payload",payload)
        id = payload.get("sub")
        if id is None:
            raise credentials_exception
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception
    user = get_user_by_id(db, id) #circular import issue
    if user is None:
        raise credentials_exception
    return user

async def verify_is_admin(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """Verify the logged in user has the status of admin to be authorized for certain operations"""

    user = await verify_user_logged_in(token, db)
    print("curr user's role:", user.role.value)
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privilege is required for request")

def verify_id_token(token: str) -> bool:
    """Decode email jwt and return user id from payload using pyjwt"""
    try:
        payload = jwt.decode(token, SECRET_KEY_EMAIL, algorithms=[ALGORITHM])
        print("payload", payload)
        id = payload.get("sub")
        return id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Email link has expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid email link")

def generate_random_password() -> str:
    """create random password for first """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        if (any(char.islower() for char in password)
                and any(char.isupper() for char in password)
                and any(char.isdigit() for char in password)):
            break
    return password

def blacklist_token(token):
    """Decode the jwt token to obtain expiration time and set the difference between it
    and the current time to be the expiration time of the corresponding key in the redis database blacklist"""

    decoded_token = jwt.decode(token, SECRET_KEY_LOGIN, algorithms=[ALGORITHM])
    token_expiration = decoded_token["exp"]
    print("exp", token_expiration)
    remaining_time = token_expiration - int(time.time()) + 3600 #might want to change buffer time later
    redis_client.setex(token, remaining_time, "blacklisted")

def is_token_blacklisted(token):
    """Check if the token can be found in the redis database blacklist"""

    return redis_client.exists(token) == 1
