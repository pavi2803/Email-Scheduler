from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')  # <--- key changes

# Save token for future runs
with open('token.json', 'w') as f:
    f.write(creds.to_json())

print("Token saved to token.json. You can now use it in your deployed app.")