"""
Gmail Token Generator
Run this script LOCALLY on your computer to generate an OAuth token.
You only need to do this once!
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def main():
    print("=" * 60)
    print("Gmail Token Generator")
    print("=" * 60)
    print("\nThis will open a browser window for authentication.")
    print("Make sure credentials.json is in the same folder!")
    print("\n" + "=" * 60 + "\n")
    
    try:
        # Create OAuth flow from credentials.json
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )
        
        # Run local server to get credentials
        print("Opening browser for authentication...")
        creds = flow.run_local_server(port=0)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Authentication complete!")
        print("=" * 60)
        print("\n📋 COPY THIS ENTIRE TOKEN:\n")
        print("-" * 60)
        print(creds.to_json())
        print("-" * 60)
        
        print("\n✨ Next steps:")
        print("1. Copy the token above (everything between the dashes)")
        print("2. Go to your Streamlit app")
        print("3. Paste it in the sidebar")
        print("4. Click 'Save Token'")
        print("5. Start scheduling emails!")
        print("\n" + "=" * 60)
        
        # Also save to file for convenience
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
        print("\n💾 Token also saved to token.json")
        
    except FileNotFoundError:
        print("\n❌ ERROR: credentials.json not found!")
        print("Make sure credentials.json is in the same folder as this script.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure you:")
        print("- Have credentials.json in the same folder")
        print("- Added ps12049@usc.edu as a test user in Google Cloud")
        print("- Enabled Gmail API in your project")

if __name__ == '__main__':
    main()