import os.path
import base64
import json
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.secret_manager import get_secret

# This is the version that uses the token.json from Secrets Manager
# It is the correct version for your AWS Lambda environment.

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_gmail_service():
    """
    Authenticates with the Gmail API using a token stored in an environment variable.
    """
    token_json_str = get_secret("prod/CustomerAgent/GmailTokenS")
    
    if not token_json_str:
        print("❌ GMAIL_TOKEN_JSON environment variable not set.")
        return None

    try:
        creds = Credentials.from_authorized_user_info(token_json_str, SCOPES)
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Error during Gmail authentication: {e}")
        return None

def get_latest_email(service, user_id="me"):
    """
    Fetches the most recent unread email ONLY from a specific sender.
    """
    try:
        # This query now filters for unread emails specifically from your address.
        query = "is:unread from:nathanfrederick3@gmail.com"
        print(f"Searching for emails with query: '{query}'")
        
        results = service.users().messages().list(userId=user_id, q=query, maxResults=1).execute()
        messages = results.get("messages", [])

        if not messages:
            return None

        msg_id = messages[0]["id"]
        msg = service.users().messages().get(userId=user_id, id=msg_id, format="full").execute()
        
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        
        email_data = {
            "id": msg_id,
            "thread_id": msg.get("threadId"),
            "subject": next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject"),
            "sender": next((h["value"] for h in headers if h["name"] == "From"), "No Sender"),
        }

        body = "No Body Content"
        if "parts" in payload and payload.get('parts'):
            part = payload['parts'][0]
            if part.get('body') and 'data' in part['body']:
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode("utf-8")
        elif 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode("utf-8")
        
        email_data["body"] = body
        
        print(f"--- New Email Found ---")
        print(f"From: {email_data['sender']}")
        
        return email_data

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def send_email(service, to, subject, message_text, thread_id):
    """Creates and sends an email message as a reply in a specific thread."""
    try:
        message = EmailMessage()
        message.set_content(message_text)
        message["To"] = to
        message["From"] = "me"
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message, "threadId": thread_id}

        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f'Message Id: {send_message["id"]}')
        return send_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
