from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

# Clean slate
if os.path.exists('token.json'):
    os.remove('token.json')
    print("Deleted old token")

print("\n🔴 IMPORTANT: Revoke old access first!")
print("Go to: https://myaccount.google.com/permissions")
print("Find your app → Remove access")
input("Press Enter when done...\n")

# Generate fresh token with refresh token
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(
    port=0,
    access_type='offline',  # Gets refresh token
    prompt='consent'         # Forces new refresh token
)

# Save it
with open('token.json', 'w') as f:
    f.write(creds.to_json())

# Verify
token_data = json.loads(creds.to_json())
if token_data.get('refresh_token'):
    print("\n✅ SUCCESS! Refresh token saved.")
    print("✅ This token will last indefinitely (as long as you use it occasionally)")
else:
    print("\n❌ ERROR: No refresh token. Try revoking access and running again.")