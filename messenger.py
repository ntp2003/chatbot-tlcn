from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import os
import json
import httpx
from uuid import uuid4
import hmac
import hashlib
from service.store_chatbot import gen_answer_for_messenger
from openai.types.chat import ChatCompletionMessageParam

# run FastAPI app
# uvicorn messenger:app --reload 

# use ngrok to create public URL
# ngrok http 8000

load_dotenv()

# get env variable
VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')
APP_SECRET = os.getenv('FB_APP_SECRET')

# init FastAPI app
app = FastAPI()

# conversation history for each user
conversation_history = {}

# xác thực webhook và xử lý tin nhắn từ Facebook
@app.get('/webhook')
async def verify_webhook(request: Request):
    # Facebook gửi verify token dưới dạng hub.verify_token
    fb_token = request.query_params.get("hub.verify_token")
    
    # Kiểm tra token
    if fb_token == VERIFY_TOKEN:
        # Trả về hub.challenge để xác thực webhook
        return Response(content=request.query_params["hub.challenge"])
    
    return 'Token xác thực không hợp lệ'

# handle facebook message
@app.post('/webhook')
async def process_webhook(request: Request, background_tasks: BackgroundTasks):
    # Lấy dữ liệu từ request
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    body = json.loads(body_str)
    
    # verify request từ Facebook
    if APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_facebook_signature(body_bytes, signature):
            raise HTTPException(status_code=403, detail="Chữ ký không hợp lệ")
    
    # check for message event
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                
                # handle text message
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    message_text = messaging_event["message"]["text"]
                    
                    # Xử lý tin nhắn trong background để không chặn response
                    background_tasks.add_task(
                        process_message, sender_id, message_text
                    )
    
    # Facebook yêu cầu phản hồi 200 OK
    return Response(content="EVENT_RECEIVED")

# xác thực chữ ký từ Facebook
def verify_facebook_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_header, expected_signature)

# xử lý tin nhắn và gửi phản hồi
async def process_message(sender_id: str, message_text: str):
    # tạo ID người dùng và ID cuộc trò chuyện nếu chưa có
    if sender_id not in conversation_history:
        conversation_history[sender_id] = []
    
    # thêm tin nhắn của người dùng vào lịch sử
    conversation_history[sender_id].append({"role": "user", "content": message_text})
    
    # giới hạn lịch sử trò chuyện để tránh quá dài
    if len(conversation_history[sender_id]) > 10:
        conversation_history[sender_id] = conversation_history[sender_id][-10:]
    
    # Tạo UUID cho user_id và thread_id
    user_id = uuid4()
    thread_id = uuid4()
    
    # Chuẩn bị tin nhắn cho chatbot
    formatted_messages = []
    for msg in conversation_history[sender_id]:
        formatted_message: ChatCompletionMessageParam = {
            "role": msg["role"],
            "content": msg["content"],
        }
        formatted_messages.append(formatted_message)
    
    try:
        response_text = gen_answer_for_messenger(
            user_id=user_id,
            thread_id=thread_id,
            messages=formatted_messages,
        )
        
        # thêm response vào conversation_history
        conversation_history[sender_id].append({"role": "assistant", "content": response_text})
        
        # send response to user qua Facebook Messenger
        await send_message(sender_id, response_text)
    except Exception as e:
        error_message = f"Đã xảy ra lỗi: {str(e)}"
        await send_message(sender_id, error_message)

# gửi tin nhắn đến người dùng qua Facebook Messenger API
async def send_message(recipient_id: str, message_text: str):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn: {e}")

# run app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("messenger:app", host="0.0.0.0", port=8000, log_config=None, reload=True)
