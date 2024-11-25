import logging
import time
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.db import models
from src.db.database import engine
from src.routers import login, email, users
from src.logs.logging_config import setup_logging


logging.getLogger('passlib').setLevel(logging.ERROR) #silences a warning between passlib and bcrypt
setup_logging()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recipe Organizer API",
    version="0.0.1"
)

origins = [
    "http://localhost",
    "http://localhost:8080",
]

#might want to remove later
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


#endpoints

app.include_router(login.router, prefix="/api/v1", tags=["login"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])

#currently disabling email routes
# app.include_router(email.router, tags=["email"])


if __name__ == '__main__':
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8080,
                reload=True)
