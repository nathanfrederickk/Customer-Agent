# src/gmail_service.py

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """
    Authenticates with the Gmail API and returns a service object.
    Handles the OAuth 2.0 flow and token storage.
    """
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
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
    Fetches the content of the most recent unread email.
    In a real system, you would have more robust logic to find specific threads.
    """
    try:
        # Get the list of unread messages
        results = service.users().messages().list(userId=user_id, q="is:unread", maxResults=1).execute()
        messages = results.get("messages", [])

        if not messages:
            print("No new unread messages found.")
            return None

        # Get the full message details for the first unread message
        msg = service.users().messages().get(userId=user_id, id=messages[0]["id"], format="full").execute()
        
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "No Sender")

        # Extract the body content
        body = "No Body"
        if "parts" in payload:
            part = payload["parts"][0]
            if "body" in part and "data" in part["body"]:
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
        elif "body" in payload and "data" in payload["body"]:
            data = payload["body"]["data"]
            body = base64.urlsafe_b64decode(data).decode("utf-8")

        print(f"--- New Email Found ---")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        
        return body

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

if __name__ == "__main__":
    get_latest_email(get_gmail_service())