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

load_dotenv(".env")

# get env variable
VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')
APP_SECRET = os.getenv('FB_APP_SECRET')
print("verify_token:", VERIFY_TOKEN)

# init FastAPI app
app = FastAPI()

# conversation history for each user
conversation_history = {}

# xác thực webhook 
# endpoint 
#@app.get('/messaging-webhook')

#@app.get('/messaging-webhook')
@app.get('/webhook')
async def verify_webhook(request: Request):
    # Facebook gửi verify token dưới dạng hub.verify_token  
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    challenge = query_params.get("hub.challenge")
    fb_verify_token = request.query_params.get("hub.verify_token")

    print(f"[DEBUG] Expected Token: {VERIFY_TOKEN} \n Received Token: {fb_verify_token}")
    #check if a token and mode is in the query string of the requets
    if (mode and fb_verify_token):
        # check the mode and token sent is correct
        if (mode == "subscribe" and fb_verify_token == VERIFY_TOKEN):
            print("WEBHOOK_VERIFIED")
            # Trả về hub.challenge để xác thực webhook
            return Response(content=challenge, status_code=200)
    return Response(content="Token không hợp lệ", status_code=403)

# handle facebook message
# endpoint to receive webhook notification from Facebook Messenger
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
                '''
                # handle text message
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    message_text = messaging_event["message"]["text"]
                    
                    # Xử lý tin nhắn trong background để không chặn response
                    background_tasks.add_task(
                        process_message, sender_id, message_text
                    )
                '''
                if "message" in messaging_event:
                    message = messaging_event["message"]
                    if message.get("is_echo"):
                        continue  # bỏ qua tin nhắn echo
                    if "text" in message:
                        message_text = message["text"]
                        background_tasks.add_task(process_message, sender_id, message_text)
    
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
'''
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
'''

async def process_message(sender_id: str, message_text: str):
    # Khởi tạo hoặc lấy thông tin cuộc trò chuyện
    if sender_id not in conversation_history:
        conversation_history[sender_id] = {
            'messages': [],
            'user_id': uuid4(),
            'thread_id': uuid4()
        }
    user_info = conversation_history[sender_id]
    messages_history = user_info['messages']
    
    # Thêm tin nhắn người dùng và giới hạn lịch sử
    messages_history.append({"role": "user", "content": message_text})
    if len(messages_history) > 10:
        user_info['messages'] = messages_history[-10:]
    
    formatted_messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in user_info['messages']
    ]
    
    try:
        # Tạo câu trả lời
        '''
        response_text = gen_answer_for_messenger(
            user_id=user_info['user_id'],
            thread_id=user_info['thread_id'],
            messages=formatted_messages,
        )
        '''''
        response_text = "xin chào"
        # Thêm và giới hạn lịch sử
        user_info['messages'].append({"role": "assistant", "content": response_text})
        if len(user_info['messages']) > 10:
            user_info['messages'] = user_info['messages'][-10:]
        
        await send_message(sender_id, response_text)
    except Exception as e:
        await send_message(sender_id, f"Lỗi: {str(e)}")

# gửi tin nhắn đến người dùng qua Facebook Messenger API
async def send_message(recipient_id: str, message_text: str):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

# run app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("messenger:app", host="0.0.0.0", port=8000, log_config=None, reload=True)
