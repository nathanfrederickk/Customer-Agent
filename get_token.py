import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

# file downloaded from Google Cloud Console
CLIENT_SECRETS_FILE = "credentials.json"
# file to save the new token to
NEW_TOKEN_FILE = "token.json"

def generate_new_token():
    """Runs the authentication flow to generate a new token.json."""
    creds = None
    
    # check if the master credentials file exists
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Error: '{CLIENT_SECRETS_FILE}' not found. Please download it from Google Cloud Console.")
        return

    print("🚀 Starting authentication flow...")
    # create the flow instance from the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    
    # 1. Starts a temporary local web server.
    # 2. Opens your web browser to the Google consent screen.
    # 3. After you grant permission, it captures the authorization code.
    # 4. Exchanges the code for an access token and a refresh token.
    creds = flow.run_local_server(port=0)

    # Save the new credentials to the token.json file
    with open(NEW_TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())
    
    print(f"\n✅ Success! New credentials saved to '{NEW_TOKEN_FILE}'.")
    print("➡️ Next step: Copy the contents of this file into AWS Secrets Manager.")

if __name__ == "__main__":
    generate_new_token()