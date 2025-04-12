from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, get_db
from . import models
from threading import Thread
import uvicorn
from bot import send_login_2fa_buttons
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

@app.get("/tg")
async def test_tg_inline():
    send_login_2fa_buttons("7810898438")
    return {"link": "https://t.me/flagship01_bot"}



def run_fastapi():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
