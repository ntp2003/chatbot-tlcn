from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from typing import List
from service.messenger import messenger as messenger_service
from fastapi import APIRouter
from env import env

router = APIRouter()


# Request Models.
class WebhookRequestData(BaseModel):
    object: str = ""
    entry: List = []


@router.get("/webhook")
async def verify(request: Request):
    """
    On webook verification VERIFY_TOKEN has to match the token at the
    configuration and send back "hub.challenge" as success.
    """
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get(
        "hub.challenge"
    ):
        if not request.query_params.get("hub.verify_token") == env.FB_VERIFY_TOKEN:
            return Response(content="Verification token mismatch", status_code=403)
        return Response(content=request.query_params["hub.challenge"])

    return Response(content="Required arguments haven't passed.", status_code=400)


@router.post("/webhook")
async def webhook(data: WebhookRequestData):
    """
    Messages handler.
    """

    print("Received webhook data:", data)

    try:
        if data.object == "page":
            messenger_service.handle(data.model_dump())
    except Exception as e:
        print("Error handling webhook data:", e)

    return Response(content="ok")
