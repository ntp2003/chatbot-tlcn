from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from env import env
import os

# Scopes required to send an email
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _authenticate_gmail():
    """Authenticate the user and return the Gmail API service."""
    creds = None
    # Load previously saved credentials
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If credentials are not valid or do not exist, initiate the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                env.GOOGLE_APPLICATION_CREDENTIALS, SCOPES
            )
            creds = flow.run_local_server(port=12345)
        # Save credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def create_message(
    sender: str, to: str, subject: str, message_text: str, content_type: str = "html"
) -> dict:
    """Create an email message."""
    message = MIMEText(message_text, _subtype=content_type)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_message(
    message: dict[str, str] | str, service=_authenticate_gmail(), user_id: str = "me"
):
    """Send an email using the Gmail API."""
    try:
        sent_message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print(f"Message sent successfully: {sent_message['id']}")
    except Exception as error:
        print(f"An error occurred: {error}")
