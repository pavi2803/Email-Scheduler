import streamlit as st
import base64
from email.mime.text import MIMEText
from datetime import datetime
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
          'https://www.googleapis.com/auth/gmail.compose']

# Template body
TEMPLATE_BODY = """My Relevant experience includes:

 • Advanced Modeling: Built MAVeRiC-AD, a vision-language ensemble for Alzheimer's MRI classification (0.90 ROC-AUC across multi-site data). Responsible for dataset design, modeling, and multi-center validation.

 • End-to-End Delivery: Developed and deployed HIPAA-compliant risk prediction systems on 1.5M+ patient records using XGBoost/LightGBM with SHAP explainability—covering data engineering, modeling, evaluation, and operationalization.

 • System-Level Work: Experienced with reproducible pipelines, model tracking, scalable inference, and cross-functional collaboration with clinical and product teams.

I'm exploring opportunities where I can contribute to both high-level ML strategy and hands-on development within healthcare AI. If your group is hiring, or if there's someone you'd recommend I connect with, I'd appreciate the guidance.

Thank you,
Pavithra
Website: https://pavi2803.notion.site/Pavithra-Senthilkumar-36e0d62aea2f4c8086fd279363c59b34
LinkedIn: https://www.linkedin.com/in/pavithra-senthilkumar-2803/
GitHub: https://github.com/pavi2803"""

def get_credentials_from_secrets():
    """Get credentials from Streamlit secrets or manual input"""
    try:
        if "google_credentials" in st.secrets:
            return dict(st.secrets["google_credentials"])
    except:
        pass
    
    # Check session state for manual token
    if 'manual_credentials' in st.session_state:
        return st.session_state.manual_credentials
    
    return None

def get_gmail_service():
    """Get Gmail service using stored token"""
    if 'token_data' not in st.session_state:
        return None
    
    try:
        creds = Credentials.from_authorized_user_info(st.session_state.token_data, SCOPES)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state.token_data = json.loads(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        st.error(f"Failed to create Gmail service: {e}")
        return None

def create_message(to, subject, body):
    """Create email message"""
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def schedule_email(service, to, subject, body, scheduled_time):
    """Schedule email to be sent at specific time"""
    try:
        message = create_message(to, subject, body)
        
        # Convert scheduled time to milliseconds since epoch
        scheduled_datetime = datetime.fromisoformat(scheduled_time)
        scheduled_send_time = int(scheduled_datetime.timestamp() * 1000)
        
        # Add scheduledSendDateTime to message
        message['scheduledSendDateTime'] = scheduled_send_time
        
        # Send the message
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return True, f"Email scheduled successfully! Message ID: {sent_message['id']}"
    except HttpError as error:
        return False, f"Gmail API error: {error}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="Gmail Email Scheduler", page_icon="📧", layout="wide")

st.title("📧 Gmail Email Scheduler")
st.markdown("Schedule personalized cold emails through Gmail API")

# Check if credentials are configured
credentials_configured = get_credentials_from_secrets() is not None

# Sidebar for authentication
with st.sidebar:
    st.header("🔐 Authentication")
    
    # Method 1: Manual Token Entry (Simplest for Streamlit Cloud)
    if 'token_data' not in st.session_state:
        st.warning("⚠️ Not authenticated")
        
        st.markdown("### Option 1: Manual Token (Recommended)")
        st.info("""
        **One-time setup:**
        1. Run the authentication script locally
        2. Copy the generated token
        3. Paste it here
        """)
        
        with st.expander("📋 How to get your token"):
            st.markdown("""
            **Run this Python script on your local computer:**
            
            ```python
            from google_auth_oauthlib.flow import InstalledAppFlow
            import json
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                      'https://www.googleapis.com/auth/gmail.compose']
            
            # Load your credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Print token
            print("\\nCopy this token:")
            print(creds.to_json())
            ```
            
            **Then:**
            - Copy the entire JSON output
            - Paste it in the text area below
            - Click "Save Token"
            """)
        
        token_input = st.text_area(
            "Paste your token JSON here:",
            height=150,
            placeholder='{"token": "ya29...", "refresh_token": "...", ...}'
        )
        
        if st.button("💾 Save Token", type="primary"):
            try:
                token_data = json.loads(token_input)
                st.session_state.token_data = token_data
                st.success("✅ Token saved! You're authenticated!")
                st.rerun()
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON. Please check your token format.")
        
        st.markdown("---")
        
        # Method 2: OAuth URL (Alternative)
        st.markdown("### Option 2: OAuth Link")
        
        if credentials_configured:
            credentials = get_credentials_from_secrets()
            if credentials and 'installed' in credentials:
                client_id = credentials['installed']['client_id']
                
                oauth_url = f"""https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri=http://localhost&response_type=code&scope=https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.compose&access_type=offline"""
                
                st.markdown(f"[🔗 Click here to authorize]({oauth_url})")
                st.caption("After authorizing, you'll get a code. Paste it below:")
                
                auth_code = st.text_input("Authorization code:")
                if st.button("Submit Code"):
                    st.warning("This method requires additional setup. Use Option 1 instead.")
        else:
            st.info("Configure credentials in secrets first")
    else:
        st.success("✅ Authenticated with Gmail!")
        st.info("Token stored in session")
        
        if st.button("🔄 Clear Token"):
            if 'token_data' in st.session_state:
                del st.session_state.token_data
            st.rerun()

# Main form
if 'token_data' in st.session_state:
    st.markdown("---")
    
    # Email details
    col1, col2 = st.columns(2)
    
    with col1:
        recipient_email = st.text_input(
            "📧 Recipient Email Address",
            placeholder="john.doe@optum.com"
        )
    
    with col2:
        subject_line = st.text_input(
            "📝 Subject Line",
            value="Interested in ML Roles at [Company] - USC Grad"
        )
    
    # Company intro
    st.markdown("### ✍️ Custom Company Introduction")
    company_intro = st.text_area(
        "This will appear after 'Hi [First Name],' - customize it per company",
        placeholder="I've been following your team's work in AI-driven utilization review using ML to prioritize cases, improve patient-status decisions, and reduce denial risk; and my background aligns closely with the problems your group focuses on.",
        height=150
    )
    
    # Schedule date and time
    st.markdown("### 📅 Schedule")
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_date = st.date_input(
            "Date",
            min_value=datetime.now().date(),
            value=datetime.now().date()
        )
    
    with col2:
        schedule_time = st.time_input(
            "Time",
            value=datetime.now().time()
        )
    
    # Combine date and time
    scheduled_datetime = datetime.combine(schedule_date, schedule_time)
    

    with col1:
        recipient_first_name = st.text_input(
            "First Name",
            placeholder="John",
            help="Will replace [First Name] in email"
        )


    # Preview
    st.markdown("---")
    with st.expander("👁️ Preview Email"):
        full_body = f"Hi {recipient_first_name},\n\n{company_intro}\n\n{TEMPLATE_BODY}" if company_intro else f"Hi {recipient_first_name},\n\n{TEMPLATE_BODY}"
        
        st.markdown(f"**To:** {recipient_email or '[Recipient Email]'}")
        st.markdown(f"**Subject:** {subject_line}")
        st.markdown(f"**Scheduled for:** {scheduled_datetime.strftime('%B %d, %Y at %I:%M %p')}")
        st.markdown("---")
        st.text(full_body)
    
    # Template reference
    with st.expander("📄 Standard Template Body (Reference)"):
        st.text(TEMPLATE_BODY)
        st.info("This template is automatically included in every email. Only customize the company intro above.")
    
    # Schedule button
    st.markdown("---")
    if st.button("📤 Schedule Email", type="primary", use_container_width=True):
        if not recipient_email:
            st.error("❌ Please enter recipient email address")
        elif not company_intro:
            st.error("❌ Please enter custom company introduction")
        else:
            # Create full email body
            full_body = f"Hi {recipient_first_name},\n\n{company_intro}\n\n{TEMPLATE_BODY}"
            
            # Get Gmail service
            service = get_gmail_service()
            
            if service:
                with st.spinner("Scheduling email..."):
                    success, message = schedule_email(
                        service,
                        recipient_email,
                        subject_line,
                        full_body,
                        scheduled_datetime.isoformat()
                    )
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Failed to connect to Gmail. Check your token.")
else:
    st.info("👈 Please authenticate in the sidebar to start scheduling emails.")
    
    with st.expander("ℹ️ Quick Start Guide"):
        st.markdown("""
        ### 🚀 How to get started:
        
        **Step 1: Get your token (one-time setup)**
        
        1. Download this Python script and save as `get_token.py`:
        
        ```python
        from google_auth_oauthlib.flow import InstalledAppFlow
        import json
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                  'https://www.googleapis.com/auth/gmail.compose']
        
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        print("\\nCopy this entire token:")
        print("="*50)
        print(creds.to_json())
        print("="*50)
        ```
        
        2. Put your `credentials.json` in the same folder
        3. Run: `python get_token.py`
        4. Browser will open → Sign in with ps12049@usc.edu
        5. Copy the token JSON from terminal
        
        **Step 2: Paste token in sidebar**
        
        1. Go to sidebar → paste token → Save
        2. You're authenticated!
        
        **Step 3: Schedule emails**
        
        - Enter recipient, subject, intro
        - Pick date/time
        - Hit "Schedule Email"
        - Done!
        
        ---
        
        **Note:** Token stays valid for a while, but may need refresh eventually.
        """)

# Footer
st.markdown("---")
st.caption("🎓 Graduating Dec 17, 2024 | Built for cold email outreach")