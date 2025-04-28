from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import os
import json
import httpx
import logging
import asyncio
from uuid import uuid4
import hmac
import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime, timedelta
from service.store_chatbot_v3 import gen_answer_for_messenger
from openai.types.chat import ChatCompletionMessageParam
from repositories.user import get_user_by_fb_id, create_user
from models.user import CreateUserModel
from models.user_memory import UserMemoryModel
from repositories.user_memory import update_user_memory
from env import env
import time
import uuid
# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(".env")
VERIFY_TOKEN = env.FB_VERIFY_TOKEN  
PAGE_ACCESS_TOKEN = env.FB_PAGE_ACCESS_TOKEN
APP_SECRET = env.FB_APP_SECRET
FB_PAGE_ID = env.FB_PAGE_ID
# Initialize FastAPI app
app = FastAPI()

# data structures for managing conversations and rate limiting
@dataclass
class ConversationState:
    messages: List[Dict[str, str]]
    user_id: uuid4
    thread_id: uuid4
    #db_user_id: uuid4 # lưu user_id từ db
    last_activity: datetime

conversation_history: Dict[str, ConversationState] = {}
message_locks: Dict[str, asyncio.Lock] = {}
message_queue = deque()

# Webhook verification endpoint
@app.get('/webhook')
async def verify_webhook(request: Request):
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    challenge = query_params.get("hub.challenge")
    fb_verify_token = query_params.get("hub.verify_token")

    logger.info(f"Verifying webhook - Token received: {fb_verify_token}")

    if mode and fb_verify_token:
        if mode == "subscribe" and fb_verify_token == VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
    return Response(content="Token không hợp lệ", status_code=403)


# Webhook handling endpoint
@app.post('/webhook')
async def process_webhook(request: Request, background_tasks: BackgroundTasks):
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    body = json.loads(body_str)
    
    logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

    # Verify Facebook signature
    if APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_facebook_signature(body_bytes, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                
                if "message" in messaging_event:
                    message = messaging_event["message"]
                    if message.get("is_echo"):
                        continue
                    if "text" in message:
                        message_text = message["text"]
                        background_tasks.add_task(
                            process_message, 
                            sender_id, 
                            message_text
                        )

    return Response(content="EVENT_RECEIVED")

def verify_facebook_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_header, expected_signature)

async def process_message(sender_id: str, message_text: str):
    logger.info(f"Processing message from {sender_id}: {message_text}")
    persistent_thread_id = uuid.uuid5(uuid.NAMESPACE_DNS, sender_id) # create a persistent thread id from sender_id
    try:
        # Get user info from Facebook
        #conversation_id = await get_conversation_id(sender_id)
        url = f"https://graph.facebook.com/{sender_id}?fields=name&access_token={PAGE_ACCESS_TOKEN}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            fb_user_info = response.json()
            user_name = fb_user_info.get('name')
            logger.info(f"User info retrieved: {user_name}")
            logger.info(f"FB_id: {sender_id}")

        # Check/Create user in database
        user = get_user_by_fb_id(sender_id)
        if not user:
            logger.info(f"User with fb_id {sender_id} not found. Attempting to create.")
            user = create_user(CreateUserModel(
                user_name=user_name,
                fb_id=sender_id
            ))
            logger.info(f"New user created: {user.user_name}")

        # Initialize or get conversation state
        if sender_id not in conversation_history:
            conversation_history[sender_id] = ConversationState(
                messages=[],
                #user_id=uuid4(),
                user_id=user.id, # Use actual user ID from database
                thread_id=persistent_thread_id,
                last_activity=datetime.now()
            )
        
        conversation = conversation_history[sender_id]
        
        # Add user message to history
        conversation.messages.append({
            "role": "user",
            "content": message_text
        })

        # Limit conversation history
        if len(conversation.messages) > 10:
            conversation.messages = conversation.messages[-10:]

        # Format messages for chatbot
        formatted_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation.messages
        ]

        # Generate chatbot response
        response_text = gen_answer_for_messenger(
            user_id=conversation.user_id,
            thread_id=conversation.thread_id,
            messages=formatted_messages
        )

        # Add bot response to history
        conversation.messages.append({
            "role": "assistant",
            "content": response_text
        })

        # Queue message for sending
        await queue_message(sender_id, response_text)

    except Exception as e:
        error_message = f"Error processing message: {str(e)}"
        logger.error(error_message)
        await queue_message(sender_id, "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.")

async def queue_message(recipient_id: str, message_text: str):
    message_queue.append((recipient_id, message_text))
    await process_message_queue()

async def process_message_queue():
    if not message_queue:
        return

    recipient_id, message_text = message_queue.popleft()
    await send_message(recipient_id, message_text)

async def send_message(recipient_id: str, message_text: str):
    # Initialize lock if not exists
    if recipient_id not in message_locks:
        message_locks[recipient_id] = asyncio.Lock()

    async with message_locks[recipient_id]:
        # Basic rate limiting
        await asyncio.sleep(1)

        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Message sent successfully to {recipient_id}")
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e.response.text if e.response else str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

async def get_conversation_id(sender_id: str) -> str:
    """Lấy conversation ID từ Facebook Graph API"""
    try:
        url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/conversations"
        params = {
            "user_id": sender_id,
            "access_token": PAGE_ACCESS_TOKEN,
            "fields": "id"  # Chỉ lấy ID của conversation
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Lấy conversation ID từ kết quả trả về
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]["id"]
            
            # Nếu không tìm thấy conversation, tạo fallback ID
            return f"{sender_id}_{int(time.time())}"
            
    except Exception as e:
        logger.error(f"Error getting conversation ID: {str(e)}")
        # Fallback: Tạo ID từ sender_id và timestamp
        return f"{sender_id}_{int(time.time())}"

def update_user_memory_with_context(user_memory: UserMemoryModel, context: dict):
    user_memory.context = context
    return update_user_memory(user_memory)

def cleanup_old_conversations():
    current_time = datetime.now()
    for sender_id in list(conversation_history.keys()):
        if (current_time - conversation_history[sender_id].last_activity).hours > 24:
            del conversation_history[sender_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "messenger:app", 
        host="0.0.0.0", 
        port=8000, 
        log_config=None, 
        reload=True
    )