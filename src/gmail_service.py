import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Ensure you have the correct scopes for reading and sending
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_gmail_service():
    """Authenticates with the Gmail API and returns a service object."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def get_latest_email(service, user_id="me"):
    """
    Fetches the most recent unread email and returns its details as a dictionary.
    """
    try:
        results = service.users().messages().list(userId=user_id, q="from:nathanfrederick3@gmail.com", maxResults=1).execute()
        messages = results.get("messages", [])

        if not messages:
            # Return None if no new messages are found
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
            if part['body'] and 'data' in part['body']:
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode("utf-8")
        elif 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode("utf-8")
        
        email_data["body"] = body
        
        print(f"--- New Email Found ---")
        print(f"From: {email_data['sender']}")
        print(f"Subject: {email_data['subject']}")
        
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
