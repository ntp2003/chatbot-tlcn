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
from repositories.user import get_user_by_fb_id, create_user
from models.user import CreateUserModel

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
#@app.get('/messaging-webhook')
@app.get('/webhook') # endpoint to receive webhook notification from Facebook Messenger
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
    json.dump(body, open("messenger_body.json", "w"),indent=4, ensure_ascii=False)
    print(f"[DEBUG] Body: {body}")

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
                        # Xử lý tin nhắn trong background để không chặn response
                        background_tasks.add_task(process_message, sender_id, message_text)
    
    # Facebook yêu cầu phản hồi 200 OK
    return Response(content="EVENT_RECEIVED")

# xác thực facebook signature
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
    # Get user info from Facebook
    url = f"https://graph.facebook.com/{sender_id}?fields=name&access_token={PAGE_ACCESS_TOKEN}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url) # get response from Facebook
        fb_user_info = response.json() # convert response to json
        user_name = fb_user_info.get('name') # get user name
        print(f"[DEBUG] User Name: {user_name}")

    
    # Check if user exists in our database
    user = get_user_by_fb_id(sender_id)
    if not user:
        
        # Create new user if not exists
        user = create_user(CreateUserModel(
            user_name=user_name,
            fb_id=sender_id
        ))
    
    # Khởi tạo hoặc lấy thông tin cuộc trò chuyện
    if sender_id not in conversation_history:
        conversation_history[sender_id] = {
            'messages': [],
            #'user_id': user.id,  # Use actual user ID from database
            'user_id': uuid4(),  # Tạo ID người dùng giả
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
    print(f"User ID: {user_info['user_id']}")
    print(f"Thread ID: {user_info['thread_id']}")
    try:
        # Tạo câu trả lời
        response_text = "xin chào"
        '''
        response_text = gen_answer_for_messenger(
            user_id=user_info['user_id'],
            thread_id=user_info['thread_id'],
            messages=formatted_messages,
        
        )
        '''
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
        "recipient": {"id": recipient_id}, # người nhận
        "message": {"text": message_text} # nội dung tin nhắn
    }
    
        
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            print(f"Message sent successfully to {recipient_id}")
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error: {e.response.text if e.response else str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

# run app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("messenger:app", host="0.0.0.0", port=8000, log_config=None, reload=True)

'''
[DEBUG] Body: {'object': 'page', 'entry': [{'time': 1744021471078, 'id': '591093784088045', 'messaging': [{'sender': {'id': '9908280712517002'}, 'recipient': {'id': '591093784088045'}, 'timestamp': 1744021470391, 'message': {'mid': 'm_QHAiHG3WIWb4ThQ0twibOlFDTJJ6QGYUkRoqRWOwcwLxk-LEUPhEUfxfCplG-uFAlf2O4l5SFV8ykD8rx6CZLw', 'text': 'hellooo abc'}}]}]}
INFO:     2a03:2880:20ff:71:::0 - "POST /webhook HTTP/1.1" 200 OK
2025-04-07 10:24:31 - HTTP Request: GET https://graph.facebook.com/9908280712517002?fields=name&access_token=EAAI6l2XYrA0BOxVPZB9sVzC4BVdAELtm5nkMaYBbM7V0gY1ZCdxFteimPEkOqrqg0s8cDy3y2N0uTzyhgUfCKYPuLBmOBDdYnQA6G3yFDXx4iqznSOCZCduONNDyFjdrgWeEWF1BZAksrWuoBzRm7DLS10hQhj6KHHyIlqB24CfrUy6ZAwxZCbSVnQ1UJiCRzZCbgZDZD "HTTP/1.1 200 OK"
[DEBUG] User Name: Huynh Nguyen Tuan Kiet
User ID: 2ad74960-c832-4b0f-9e50-5849a8e62740
Thread ID: 3934358c-5653-4341-b7eb-1bffc705390e
2025-04-07 10:24:32 - HTTP Request: POST https://graph.facebook.com/v18.0/me/messages?access_token=EAAI6l2XYrA0BOxVPZB9sVzC4BVdAELtm5nkMaYBbM7V0gY1ZCdxFteimPEkOqrqg0s8cDy3y2N0uTzyhgUfCKYPuLBmOBDdYnQA6G3yFDXx4iqznSOCZCduONNDyFjdrgWeEWF1BZAksrWuoBzRm7DLS10hQhj6KHHyIlqB24CfrUy6ZAwxZCbSVnQ1UJiCRzZCbgZDZD "HTTP/1.1 200 OK"
[DEBUG] Body: {'object': 'page', 'entry': [{'time': 1744021472596, 'id': '591093784088045', 'messaging': [{'sender': {'id': '591093784088045'}, 'recipient': {'id': '9908280712517002'}, 'timestamp': 1744021472474, 'message': {'mid': 'm_dAR_N3zGbyCEbuTfiNRiTlFDTJJ6QGYUkRoqRWOwcwLhkgFNX9GMCWYfWzltlJYfGGxKlz5uaRjCKn0FVYxLOg', 'is_echo': True, 'text': 'xin chào', 'app_id': 627371876592653}}]}]}
INFO:     2a03:2880:20ff:45:::0 - "POST /webhook HTTP/1.1" 200 OK
[DEBUG] Body: {'object': 'page', 'entry': [{'time': 1744021472960, 'id': '591093784088045', 'messaging': [{'sender': {'id': '9908280712517002'}, 'recipient': {'id': '591093784088045'}, 'timestamp': 1744021472862, 'delivery': {'mids': ['m_dAR_N3zGbyCEbuTfiNRiTlFDTJJ6QGYUkRoqRWOwcwLhkgFNX9GMCWYfWzltlJYfGGxKlz5uaRjCKn0FVYxLOg'], 'watermark': 1744021472474}}]}]}
INFO:     2a03:2880:7ff:70:::0 - "POST /webhook HTTP/1.1" 200 OK
'''