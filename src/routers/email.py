from datetime import timedelta
from email.message import EmailMessage
import smtplib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auth.helpers import generate_random_password, create_access_token, verify_id_token, verify_is_admin
from src.config.load import load_email_config, save_email_config
from src.db import crud
from src.db.database import get_db
from src.schemas.pydantic_schemas import EmailConfig, EmailRequest
import os
from dotenv import load_dotenv

load_dotenv()

ACTIVATION_EMAIL_EXPIRE_MINUTES = 720

router = APIRouter()


@router.post("/api/v1/config", dependencies=[Depends(verify_is_admin)]) #, dependencies=[Depends(verify_user_logged_in)]
async def email_config(config: EmailConfig):
    """
    Set the username and password for the email address that will send the welcome emails. Requires Bearer token auth and admin role.
    """
    save_email_config(config.model_dump())
    return {"Email configs successfully saved"}


@router.post("/api/v1/send-email", dependencies=[Depends(verify_is_admin)]) #, dependencies=[Depends(verify_user_logged_in)]
async def send_email(request: EmailRequest, db: Session = Depends(get_db)):
    """
    Send a welcome email to a customer. Requires Bearer token auth and admin role. Configure the
    email sender using the /config endpoint

    Input:
        **body**: message content of email.
        **subject**: subject line of email.
        **user_id**: id of the recipient of the email.
    Output:
        A JSON string acknowledging the email was successfully sent.
    """

    data = load_email_config()
    sender_email = data.get("email_user")
    password = data.get("email_pass")
    port = data.get("port", 587)
    server = data.get("server")

    msg = EmailMessage()
    msg['Subject'] = request.subject
    msg['From'] = sender_email
    recipient_user= crud.get_user_by_id(db, user_id=request.user_id)
    if recipient_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    msg['To'] = recipient_user.email

    new_password = generate_random_password()
    crud.update_user(
        db=db,
        user=recipient_user,
        update_user=
        {
            "password": new_password,
            "status": "invited"
        }
    )

    token = create_access_token(data={"sub": recipient_user.id}, type="email", expires_delta=timedelta(minutes=ACTIVATION_EMAIL_EXPIRE_MINUTES))
    activation_link = f"http://{os.environ.get('EMAIL_HOSTNAME')}/activate/{token}"
    msg.set_content(request.body
                    + f"\nYour temporary password is {new_password}"
                    + f"\nClick to activate account: {activation_link}")

    try:

        with smtplib.SMTP(server, port) as server:

            server.starttls() #email encryption needed to send message
            server.login(sender_email, password)
            server.send_message(msg)
            return {"message": "Email sent successfully!"}
    except Exception as e: #could add more details to error messages and catch different errors
        raise HTTPException(status_code=500, detail=str(e))


#this route does not use the /api/v2 prefix
@router.get("/activate/{token}")
async def activate_email_link(token: str, db: Session = Depends(get_db)):
    """
    Reached upon user clicking the activation link sent to email.
    Verifies token in link is authentic and not expired and then changes status of user to active
    """
    id = verify_id_token(token)
    #now with the token verified find user in db and change status to active
    user= crud.get_user_by_id(db, user_id=id)
    crud.update_user(
        db=db,
        user=user,
        update_user=
        {
            "status": "active"
        }
    )
    return {
        "msg": "Account activated successfully"
    }