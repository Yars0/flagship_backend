import threading
from app.main import app, run_fastapi
from bot import run_bot

if __name__ == "__main__":
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    run_bot()
