import streamlit as st
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
import gspread

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

# Google Sheets scopes
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ---------------- TEMPLATES ---------------- #

AGENT_PAPER_TEMPLATE = """
<p>I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions (link: <a href="https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1">https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1</a>) and have built end-to-end ML systems including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.</p>
"""

ML_SYSTEMS_TEMPLATE = """
<p>My Relevant experience includes:</p>
<p><b>• Applied ML and Finetuning LLM:</b> Built an Agentic vision-language model for medical image classification, achieving ~0.90 ROC-AUC across multi-site data, with ownership across dataset design, modeling, and validation.</p>
<p><b>• End-to-End ML Delivery:</b> Developed and deployed large-scale risk prediction models on 1.5M+ records using XGBoost/LightGBM, including feature engineering, explainability, evaluation, and production workflows.</p>
<p><b>• ML Systems & Collaboration:</b> Experience with reproducible pipelines, model tracking, scalable inference, and close collaboration with cross-functional stakeholders.</p>
"""

SOFTWARE_TEMPLATE = """
<p>My Relevant experience includes:</p>
<p><b>• Backend Development & Data Pipelines:</b> Engineered scalable data workflows using Apache Spark and Hive SQL, processing 1.5M+ records with optimized ETL pipelines and database integrations.</p>
<p><b>• System Architecture & Performance:</b> Implemented distributed systems with performance optimization, achieving ~2× throughput improvements through efficient resource management and parallel processing.</p>
<p><b>• Full-Stack Development & Deployment:</b> Built and deployed production applications with end-to-end ownership, including API development, cloud infrastructure (AWS), CI/CD pipelines, and monitoring.</p>
"""

SIGNATURE = """
<p>Thank you,<br>
Pavithra<br>
<a href="https://pavi2803.github.io/pavithrasenthilkumar.github.io/">Website</a> | 
<a href="https://www.linkedin.com/in/pavithra-senthilkumar-2803/">LinkedIn</a> | 
<a href="https://github.com/pavi2803">GitHub</a></p>
"""

# ---------------- AUTH ---------------- #

def get_gmail_service():
    if 'token_data' not in st.session_state:
        return None

    creds = Credentials.from_authorized_user_info(
        st.session_state.token_data, GMAIL_SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.token_data = json.loads(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_sheets_client():
    """Get Google Sheets client using service account"""
    if 'sheets_creds' not in st.session_state:
        return None
    
    creds = ServiceAccountCredentials.from_service_account_info(
        st.session_state.sheets_creds,
        scopes=SHEETS_SCOPES
    )
    return gspread.authorize(creds)

# ---------------- GMAIL HELPERS ---------------- #

def create_message_with_attachment(to, subject, body_html, attachment_data=None, attachment_filename=None):
    """Create an HTML email message with optional attachment"""
    message = MIMEMultipart("mixed")
    message['to'] = to
    message['subject'] = subject

    # Create the HTML part
    msg_alternative = MIMEMultipart("alternative")
    html_part = MIMEText(body_html, "html")
    msg_alternative.attach(html_part)
    message.attach(msg_alternative)

    # Add attachment if provided
    if attachment_data and attachment_filename:
        attachment = MIMEApplication(attachment_data, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
        message.attach(attachment)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_draft(service, to, subject, body, attachment_data=None, attachment_filename=None):
    message = create_message_with_attachment(to, subject, body, attachment_data, attachment_filename)
    draft = service.users().drafts().create(
        userId='me',
        body={'message': message}
    ).execute()
    return draft['id']

def add_to_schedule_sheet(draft_id, recipient_email, recipient_name, subject, send_time):
    """Add scheduled email to Google Sheet"""
    try:
        client = get_sheets_client()
        if not client:
            return False, "Sheets client not configured"
        
        sheet = client.open_by_key(st.session_state.sheet_id).sheet1
        
        row = [
            draft_id,
            recipient_email,
            recipient_name,
            subject,
            send_time.strftime('%Y-%m-%d %H:%M:%S'),
            'pending',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        sheet.append_row(row)
        return True, "Added to schedule"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ---------------- UI ---------------- #

st.set_page_config(page_title="Gmail Draft + Scheduler", layout="wide")
st.title("📝 Draft Generator + Scheduler")
st.caption("Creates Gmail drafts and schedules them for automatic sending")

# ---------- SIDEBAR AUTH & CONFIG ---------- #

with st.sidebar:
    st.header("🔐 Gmail Authentication")

    if 'token_data' not in st.session_state:
        token_input = st.text_area(
            "Paste Gmail token JSON",
            height=150,
            placeholder='{"token": "...", "refresh_token": "..."}'
        )

        if st.button("Save Gmail Token"):
            try:
                st.session_state.token_data = json.loads(token_input)
                st.success("Gmail Authenticated")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON")
    else:
        st.success("✅ Gmail Authenticated")
        if st.button("Clear Gmail Token"):
            del st.session_state.token_data
            st.rerun()

    st.markdown("---")
    st.header("📊 Google Sheets Config")
    
    if 'sheets_creds' not in st.session_state:
        sheets_creds_input = st.text_area(
            "Paste Service Account JSON",
            height=150,
            placeholder='{"type": "service_account", ...}'
        )
        
        sheet_id_input = st.text_input(
            "Google Sheet ID",
            placeholder="1ABC...XYZ"
        )
        
        if st.button("Save Sheets Config"):
            try:
                st.session_state.sheets_creds = json.loads(sheets_creds_input)
                st.session_state.sheet_id = sheet_id_input
                st.success("Sheets Configured")
                st.rerun()
            except:
                st.error("Invalid configuration")
    else:
        st.success("✅ Sheets Configured")
        if st.button("Clear Sheets Config"):
            del st.session_state.sheets_creds
            del st.session_state.sheet_id
            st.rerun()

    st.markdown("---")
    st.header("📄 Resume Files")
    
    ml_resume = st.file_uploader(
        "ML/Data Science Resume (PDF)",
        type=['pdf'],
        key="ml_resume"
    )
    
    swe_resume = st.file_uploader(
        "Software Engineering Resume (PDF)",
        type=['pdf'],
        key="swe_resume"
    )
    
    if ml_resume:
        st.session_state.ml_resume_data = ml_resume.read()
        st.session_state.ml_resume_name = ml_resume.name
        st.success(f"✓ ML Resume")
    
    if swe_resume:
        st.session_state.swe_resume_data = swe_resume.read()
        st.session_state.swe_resume_name = swe_resume.name
        st.success(f"✓ SWE Resume")

# ---------- MAIN FORM ---------- #

if 'token_data' in st.session_state:

    col1, col2 = st.columns(2)

    with col1:
        recipient_email = st.text_input(
            "Recipient Email",
            placeholder="john.doe@company.com"
        )

    with col2:
        subject_line = st.text_input(
            "Subject",
            value="Applied ML in Healthcare – Quick Intro"
        )

    recipient_name = st.text_input(
        "Recipient First Name",
        placeholder="John"
    )

    recipient_type = st.radio(
        "Recipient Type",
        options=["Agent Paper", "ML Systems", "Software Content"],
        horizontal=True
    )

    company_intro = st.text_area(
        "Custom Company Intro",
        height=150,
        placeholder="I've been following your team's work..."
    )

    # Select template
    if recipient_type == "Agent Paper":
        experience_template = AGENT_PAPER_TEMPLATE
    elif recipient_type == "ML Systems":
        experience_template = ML_SYSTEMS_TEMPLATE
    else:
        experience_template = SOFTWARE_TEMPLATE

    # ---------- OPTIONAL SECTIONS ---------- #
    
    st.markdown("---")
    st.subheader("Optional Sections")
    
    include_outro = st.checkbox("Include closing paragraph")
    outro_text = ""
    if include_outro:
        outro_text = st.text_area(
            "Closing Paragraph",
            height=100,
            value="Would love to briefly discuss how my background could support your team."
        )
    
    include_resume = st.checkbox("Attach resume")
    resume_data = None
    resume_filename = None
    resume_text = ""
    
    if include_resume:
        resume_type = st.radio(
            "Resume Type",
            options=["ML/Data Science Resume", "Software Engineering Resume"],
            horizontal=True
        )
        
        if resume_type == "ML/Data Science Resume":
            if 'ml_resume_data' in st.session_state:
                resume_data = st.session_state.ml_resume_data
                resume_filename = st.session_state.ml_resume_name
                resume_text = "<p>I have attached my resume for your reference.</p>"
                st.success(f"✓ Will attach: {resume_filename}")
            else:
                st.warning("⚠️ Upload ML resume in sidebar")
        else:
            if 'swe_resume_data' in st.session_state:
                resume_data = st.session_state.swe_resume_data
                resume_filename = st.session_state.swe_resume_name
                resume_text = "<p>I have attached my resume for your reference.</p>"
                st.success(f"✓ Will attach: {resume_filename}")
            else:
                st.warning("⚠️ Upload SWE resume in sidebar")

    # ---------- SEND OPTIONS ---------- #
    
    st.markdown("---")
    st.subheader("📅 Send Options")
    
    send_mode = st.radio(
        "When to send:",
        ["Create Draft Only", "Schedule for Later"],
        horizontal=True
    )
    
    send_datetime = None
    if send_mode == "Schedule for Later":
        if 'sheets_creds' not in st.session_state:
            st.warning("⚠️ Configure Google Sheets in sidebar to enable scheduling")
        else:
            send_datetime = st.datetime_input(
                "Send Date & Time",
                value=datetime.now(),
                min_value=datetime.now()
            )
            st.info(f"⏰ Will send at: {send_datetime.strftime('%B %d, %Y at %I:%M %p')}")

    # ---------- PREVIEW ---------- #

    st.markdown("---")
    with st.expander("Preview Email"):
        body_html = f"<p>Hi {recipient_name},</p>\n<p>{company_intro}</p>\n{experience_template}"
        
        if outro_text:
            body_html += f"\n<p>{outro_text}</p>"
        
        if resume_text:
            body_html += f"\n{resume_text}"
        
        body_html += f"\n{SIGNATURE}"
        
        st.markdown(f"**To:** {recipient_email}<br>**Subject:** {subject_line}<br><br>", unsafe_allow_html=True)
        st.markdown(body_html, unsafe_allow_html=True)
        
        if resume_data:
            st.info(f"📎 Attachment: {resume_filename}")

    # ---------- ACTION BUTTON ---------- #

    st.markdown("---")
    
    button_text = "📝 Create Draft" if send_mode == "Create Draft Only" else f"⏰ Schedule for {send_datetime.strftime('%I:%M %p') if send_datetime else 'Later'}"
    
    if st.button(button_text, type="primary", use_container_width=True):
        if not recipient_email or not recipient_name or not company_intro:
            st.error("❌ Fill in all required fields")
        elif include_resume and not resume_data:
            st.error("❌ Upload selected resume type")
        elif send_mode == "Schedule for Later" and 'sheets_creds' not in st.session_state:
            st.error("❌ Configure Google Sheets for scheduling")
        else:
            service = get_gmail_service()

            try:
                # Create draft
                draft_id = create_draft(
                    service,
                    recipient_email,
                    subject_line,
                    body_html,
                    resume_data,
                    resume_filename
                )
                
                if send_mode == "Create Draft Only":
                    st.success("✅ Draft created in Gmail!")
                    st.info("📧 Open Gmail → Drafts → Schedule Send")
                else:
                    # Add to schedule
                    success, message = add_to_schedule_sheet(
                        draft_id,
                        recipient_email,
                        recipient_name,
                        subject_line,
                        send_datetime
                    )
                    
                    if success:
                        st.success(f"✅ Draft created and scheduled for {send_datetime.strftime('%B %d, %I:%M %p')}!")
                        st.info("🤖 GitHub Actions will send it automatically")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
                        
            except HttpError as e:
                st.error(f"❌ Gmail API error: {e}")

else:
    st.info("👈 Authenticate with Gmail to start")