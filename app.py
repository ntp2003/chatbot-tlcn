import alembic.config

# from literalai import LiteralClient
from env import env
import subprocess
from fastapi import FastAPI, Request
from chainlit.utils import mount_chainlit
import uvicorn
import logging
import time
from controllers.home import router as home_router
from controllers.fb_webhook import router as fb_webhook_router
from service.wandb import *

rq_command = ["rq", "worker", "--with-scheduler"]
rq_process = subprocess.Popen(
    rq_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])

app = FastAPI(debug=True)

app.include_router(home_router, prefix="", tags=["home"])
app.include_router(fb_webhook_router, prefix="/api", tags=["webhook"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_logger")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request method and URL
    logger.info(f"Incoming request: {request.method} {request.url}")

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(f"Completed in {duration:.2f}s with status {response.status_code}")

    return response


# Specify the target module and the path where Chainlit should be mounted
target_module = "./chainlit_app.py"
mount_path = "/chainlit"

mount_chainlit(app=app, target=target_module, path=mount_path)

if __name__ == "__main__":
    uvicorn.run(app="app:app", reload=True, workers=4)
