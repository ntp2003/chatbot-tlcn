import os
import json
import uuid
import logging
import requests
import traceback
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel, Field
import hmac
import hashlib
from service.store_chatbot_v2 import gen_answer_for_messenger
from models.user_memory import UserMemoryModel, CreateUserMemoryModel
from repositories.user_memory import get_by_messenger_id, create as create_user_memory
from repositories.thread import get as get_thread, create as create_thread, CreateThreadModel
from openai.types.chat import ChatCompletionMessageParam
from repositories.message import get_all, create as create_message
from models.message import MessageType, CreateMessageModel
from repositories.user import get_user_by_fb_id, create as create_user
from env import env

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("messenger_bot.log"),
    ]
)
logger = logging.getLogger("messenger_bot")

VERIFY_TOKEN = env.FB_VERIFY_TOKEN  
PAGE_ACCESS_TOKEN = env.FB_PAGE_ACCESS_TOKEN
APP_SECRET = env.FB_APP_SECRET
FB_PAGE_ID = env.FB_PAGE_ID

# Initialize FastAPI app
app = FastAPI(title="FPTShop Messenger Chatbot")



# FB Messenger API URL
FB_API_URL = "https://graph.facebook.com/v18.0/me/messages"

class WebhookRequestMessage(BaseModel):
    """Model for incoming webhook message"""
    mid: str
    text: str

class WebhookRequestSender(BaseModel):
    """Model for message sender"""
    id: str

class WebhookRequestRecipient(BaseModel):
    """Model for message recipient"""
    id: str

class WebhookRequestMessaging(BaseModel):
    """Model for messaging event"""
    sender: WebhookRequestSender
    recipient: WebhookRequestRecipient
    timestamp: int
    message: Optional[WebhookRequestMessage] = None

class WebhookRequestEntry(BaseModel):
    """Model for webhook entry"""
    id: str
    time: int
    messaging: List[WebhookRequestMessaging]

class WebhookRequest(BaseModel):
    """Model for Facebook webhook request"""
    object: str
    entry: List[WebhookRequestEntry]

def send_message(recipient_id: str, text: str):
    """Send message to Facebook user"""
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': text},
        'messaging_type': 'RESPONSE'
    }
    headers = {'content-type': 'application/json'}
    
    params = {'access_token': PAGE_ACCESS_TOKEN}
    
    try:
        response = requests.post(
            FB_API_URL,
            params=params,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Message sent to {recipient_id}: {text[:50]}...")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message: {e}")
        return None

def send_typing_indicator(recipient_id: str, typing_on: bool = True):
    """Send typing indicator to user"""
    action = "typing_on" if typing_on else "typing_off"
    payload = {
        'recipient': {'id': recipient_id},
        'sender_action': action
    }
    headers = {'content-type': 'application/json'}
    params = {'access_token': PAGE_ACCESS_TOKEN}
    
    try:
        response = requests.post(
            FB_API_URL,
            params=params,
            json=payload,
            headers=headers
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")
        return None

def store_message(thread_id: uuid.UUID, is_user: bool, content: str):
    """
    Store message in database
    """
    try:
        # Create message
        message_data = CreateMessageModel(
            thread_id=thread_id,
            type=MessageType.user if is_user else MessageType.bot,
            content=content,
        )
        
        # Store in database
        new_message = create_message(message_data)
        logger.info(f"Message stored: thread_id={thread_id}, is_user={is_user}, content_length={len(content)}")
        return new_message
    except Exception as e:
        logger.error(f"Error storing message: {e}")
        traceback.print_exc()
        return None

async def process_message(sender_id: str, message_text: str):
    """Process user message and generate response"""
    try:
        logger.info(f"Processing message from {sender_id}: {message_text[:50]}...")
        
        # Show typing indicator
        send_typing_indicator(sender_id, True)
        
        # Get or create user memory
        user_memory = get_by_messenger_id(sender_id)
        
        # Create new user and thread if not exists
        if not user_memory:
            logger.info(f"Creating new user memory for sender {sender_id}")
            user_id = uuid.uuid4()
            thread_id = uuid.uuid4()
            
            # Create thread first
            thread = create_thread(
                CreateThreadModel(
                    id=thread_id,
                    user_id=user_id,
                    name=f"FB_THREAD_{sender_id}",
                )
            )
            
            # Create user memory
            user_memory = create_user_memory(
                CreateUserMemoryModel(
                    user_id=user_id,
                    thread_id=thread_id,
                    messenger_id=sender_id
                )
            )
            logger.info(f"Created user_memory with thread_id={thread_id}")
        
        # Format message for LLM processing
        formatted_message: ChatCompletionMessageParam = {
            "role": "user",
            "content": message_text
        }
        
        # Store user message in database
        store_message(user_memory.thread_id, is_user=True, content=message_text)
        
        # Get conversation history
        history = get_conversation_history(user_memory.thread_id)
        history.append(formatted_message)
        
        # Generate response
        logger.info(f"Generating response for user_id={user_memory.user_id}, thread_id={user_memory.thread_id}")
        response_text = gen_answer_for_messenger(
            user_id=user_memory.user_id,
            thread_id=user_memory.thread_id,
            messages=history
        )
        
        # Store bot response in database
        store_message(user_memory.thread_id, is_user=False, content=response_text)
        
        # Turn off typing indicator
        send_typing_indicator(sender_id, False)
        
        # Send response
        send_message(sender_id, response_text)
        logger.info(f"Response sent to {sender_id}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        traceback.print_exc()
        # Send error message to user
        send_message(sender_id, "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.")

def get_conversation_history(thread_id: uuid.UUID, limit: int = 10) -> List[ChatCompletionMessageParam]:
    """
    Get conversation history for thread from database
    """
    try:
        # Get messages from database
        messages = get_all(thread_id=thread_id, limit=limit)
        
        # Convert to OpenAI format
        conversation_history: List[ChatCompletionMessageParam] = []
        
        for message in messages:
            role = "user" if message.type == MessageType.user else "assistant"
            conversation_history.append({
                "role": role,
                "content": message.content
            })
        
        return conversation_history
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        traceback.print_exc()
        return []
    
def verify_facebook_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_header, expected_signature)

# Webhook verification endpoint
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handle webhook verification from Facebook
    """
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    challenge = query_params.get("hub.challenge")
    fb_verify_token = query_params.get("hub.verify_token")

    logger.info(f"Verifying webhook - mode={mode} , Token received: {fb_verify_token}")
        
    if mode and fb_verify_token:
        if mode == "subscribe" and fb_verify_token == VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
        else:
            logger.warning("Verification failed - Invalid token")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    logger.warning("Verification failed - Missing parameters")
    return Response(status_code=400)


@app.post("/webhook")
async def process_webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Process incoming messages from Facebook Messenger
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    body = json.loads(body_str)
    logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

    # Verify Facebook signature
    if APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_facebook_signature(body_bytes, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
    # Check if this is a page subscription
    if request.object != "page":
        logger.warning(f"Received non-page object: {request.object}")
        return {"status": "not page"}
    
    try:
        # Iterate over each entry (there may be multiple entries if batched)
        for entry in request.entry:
            # Iterate over each messaging event
            for messaging_event in entry.messaging:
                # Extract sender and message info
                sender_id = messaging_event.sender.id
                
                # Check if this is a message with text
                if messaging_event.message and messaging_event.message.text:
                    message_text = messaging_event.message.text
                    logger.info(f"Received message from {sender_id}: {message_text[:50]}...")
                    
                    # Process the message in the background
                    background_tasks.add_task(process_message, sender_id, message_text)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        traceback.print_exc()
    
    # Return a 200 OK response to acknowledge receipt
    # This should happen quickly regardless of message processing
    return {"status": "processed"}



if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Messenger webhook server")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
    '''
    uvicorn.run(
        "messenger:app", 
        host="0.0.0.0", 
        port=8000, 
        log_config=None, 
        reload=True
    )
    '''