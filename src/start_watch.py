import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/pubsub"
]

GCP_PROJECT_ID = "customeragent-465705"
PUB_SUB_TOPIC_ID = "gmail-new-noti" 

def get_local_gmail_service():
    """
    Performs the browser-based OAuth 2.0 flow to get credentials
    for running a local administrative script.
    """
    creds = None
    token_file = 'admin_token.json'
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def main():
    """
    Tells Gmail to start sending push notifications for the authenticated
    user's inbox to the specified Pub/Sub topic.
    """
    print("Attempting to get local Gmail service credentials.")
    service = get_local_gmail_service()
    if not service:
        print("Could not get Gmail service. Aborting.")
        return

    topic_name = f"projects/{GCP_PROJECT_ID}/topics/{PUB_SUB_TOPIC_ID}"

    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }

    try:
        # This is the command that starts the watch.
        response = service.users().watch(userId='me', body=request).execute()
        print("\n--- SUCCESS! ---")
        print(f"Gmail is now watching your inbox. Notifications will be sent to {topic_name}.")
        print(f"This watch is active for 7 days. You may need to run this script again after that.")
        print(f"History ID: {response['historyId']}")
    except HttpError as e:
        print(f"\n❌ An error occurred: {e}")
        print("This may be due to incorrect permissions. Ensure the Pub/Sub topic exists and that 'gmail-api-push@system.gserviceaccount.com' has the 'Pub/Sub Publisher' role on it.")

if __name__ == "__main__":
    main()
