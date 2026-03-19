from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

def send_email(to, subject, body):
    # Load credentials
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Auto-refresh if expired
    if creds.expired and creds.refresh_token:
        print("Token expired, refreshing...")
        creds.refresh(Request())
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
        print("Token refreshed!")
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    
    # Create message
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Send
    service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()
    
    print(f"✅ Email sent to {to}")

# Test it!
send_email(
    to='pavi2468kuk@gmail.com',  # Change this to your email
    subject='Test Email',
    body='This is a test. The token will auto-refresh!'
)