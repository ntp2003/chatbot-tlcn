from fastapi import APIRouter, Response, status

import random

router = APIRouter()

die = False
id = random.randint(0, 999)


@router.get("/")
async def root():
    return {"api": "happy response", "id": id}


@router.get("/health")
async def health(response: Response):
    if die:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "shutdown"}
    else:
        response.status_code = status.HTTP_200_OK
        return {"status": "ok"}


@router.get("/shutdown")
async def shutdown():
    global die
    die = True
    return {"shutdown": True}
