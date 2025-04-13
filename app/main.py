from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, get_db
from . import models
from threading import Thread
import uvicorn
from .auth import router as auth_router
from .organizations import router as org_router
from bot import send_login_2fa_buttons
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)
app.include_router(org_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def status():
    return {"status": "alive"}

def run_fastapi():
    uvicorn.run("app.main:app", host="26.81.14.93", port=8080)
