from typing import Union, Optional
from pydantic import BaseModel, EmailStr


class UserCreation(BaseModel):
    name: str
    email: str

class UserInDB(UserCreation):
    password: str

class UpdateUser(UserCreation):
    password: str

class UserLoginOutput(UserCreation):
    id: int

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Union[str, None] = None

class UserInfo(BaseModel):
    name: Union[str, None] = None
    email: Union[str, None] = None
    id: int

class EmailConfig(BaseModel):
    email_user: EmailStr
    email_pass: str
    port: int
    server: str #how to verify they are inputting a valid server for config?

class EmailRequest(BaseModel):
    user_id: int
    subject: str
    body: str