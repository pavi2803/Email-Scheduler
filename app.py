import streamlit as st
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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
GitHub: [Your GitHub URL]"""

def get_credentials_from_secrets():
    """Get credentials from Streamlit secrets"""
    try:
        # Try to get from secrets first
        if "google_credentials" in st.secrets:
            return dict(st.secrets["google_credentials"])
        return None
    except:
        return None

def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    
    # Check if token exists in session state
    if 'token_data' in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state.token_data, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                st.session_state.token_data = json.loads(creds.to_json())
            except Exception as e:
                st.error(f"Token refresh failed: {e}")
                if 'token_data' in st.session_state:
                    del st.session_state.token_data
                return None
        else:
            # Get credentials from secrets or upload
            credentials_data = get_credentials_from_secrets()
            
            if not credentials_data:
                # Fall back to manual upload if secrets not configured
                if 'credentials_data' not in st.session_state:
                    return None
                credentials_data = st.session_state.credentials_data
            
            try:
                flow = InstalledAppFlow.from_client_config(
                    credentials_data,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save token to session
                st.session_state.token_data = json.loads(creds.to_json())
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                return None
    
    return build('gmail', 'v1', credentials=creds)

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
        
        # Convert scheduled time to RFC 3339 format
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
        return False, f"An error occurred: {error}"
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
    
    if not credentials_configured:
        st.warning("⚠️ Credentials not configured in secrets")
        
        with st.expander("📖 How to configure secrets"):
            st.markdown("""
            ### Setup Instructions:
            
            1. Go to your Streamlit Cloud dashboard
            2. Click on your app → Settings → Secrets
            3. Add this format:
            
            ```toml
            [google_credentials]
            type = "authorized_user"
            client_id = "your-client-id"
            client_secret = "your-client-secret"
            redirect_uris = ["http://localhost"]
            ```
            
            4. Copy values from your credentials.json file
            5. Save and restart the app
            """)
        
        # Fallback: manual upload
        st.info("Or upload manually (temporary):")
        uploaded_file = st.file_uploader("Upload credentials.json", type=['json'])
        
        if uploaded_file is not None:
            credentials_data = json.load(uploaded_file)
            st.session_state.credentials_data = credentials_data
            st.success("Credentials loaded temporarily!")
            st.rerun()
    else:
        st.success("✅ Credentials configured in secrets")
    
    # Authentication status
    if credentials_configured or 'credentials_data' in st.session_state:
        if 'token_data' not in st.session_state:
            if st.button("🔑 Authenticate with Gmail", type="primary"):
                with st.spinner("Opening browser for authentication..."):
                    service = get_gmail_service()
                    if service:
                        st.success("✅ Authenticated successfully!")
                        st.rerun()
        else:
            st.success("✅ Authenticated with Gmail!")
            st.info(f"Session active")
            
            if st.button("🔄 Re-authenticate"):
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
    
    # Preview
    st.markdown("---")
    with st.expander("👁️ Preview Email"):
        full_body = f"Hi [First Name],\n\n{company_intro}\n\n{TEMPLATE_BODY}" if company_intro else f"Hi [First Name],\n\n{TEMPLATE_BODY}"
        
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
            full_body = f"Hi [First Name],\n\n{company_intro}\n\n{TEMPLATE_BODY}"
            
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
                    
                    # Clear form
                    if st.button("Send another email"):
                        st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Failed to connect to Gmail. Please re-authenticate.")
else:
    st.info("👈 Please authenticate with Gmail in the sidebar to start scheduling emails.")
    
    with st.expander("ℹ️ How to use this app"):
        st.markdown("""
        ### Quick Start:
        
        1. **Configure credentials** (one-time setup):
           - Add your credentials.json to Streamlit secrets
           - Or upload it manually (temporary)
        
        2. **Authenticate with Gmail**:
           - Click "Authenticate with Gmail" in sidebar
           - Sign in with ps12049@usc.edu
           - Grant permissions
        
        3. **Start scheduling emails!**
           - Enter recipient email
           - Customize subject and intro
           - Pick date/time
           - Hit "Schedule Email"
        
        ### First-time authentication:
        - You'll see "Google hasn't verified this app"
        - Click "Continue" (it's your own app - totally safe!)
        - Grant permission to send emails
        - You only authenticate once per session!
        """)

# Footer
st.markdown("---")
st.caption("🎓 Graduating Dec 17, 2024 | Built for cold email outreach")