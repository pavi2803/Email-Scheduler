import streamlit as st
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

# ---------------- TEMPLATES ---------------- #

RECRUITER_TEMPLATE = """
I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions, (link: https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1) and have built end-to-end ML systems including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.
"""

HIRING_MANAGER_TEMPLATE = """
I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions, (link: https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1) and have built end-to-end ML systems including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.
"""

SOFTWARE_RECRUITER = """
My Relevant experience includes:

• Backend Development & Data Pipelines: Engineered scalable data workflows using Apache Spark and Hive SQL, processing 1.5M+ records with optimized ETL pipelines and database integrations.

• System Architecture & Performance: Implemented distributed systems with performance optimization, achieving ~2× throughput improvements through efficient resource management and parallel processing.

• Full-Stack Development & Deployment: Built and deployed production applications with end-to-end ownership, including API development, cloud infrastructure (AWS), CI/CD pipelines, and monitoring.
"""

SIGNATURE = """
Thank you,
Pavithra
Website: https://pavi2803.github.io/pavithrasenthilkumar.github.io/
LinkedIn: https://www.linkedin.com/in/pavithra-senthilkumar-2803/
GitHub: https://github.com/pavi2803"""

# ---------------- AUTH ---------------- #

def get_gmail_service():
    if 'token_data' not in st.session_state:
        return None

    creds = Credentials.from_authorized_user_info(
        st.session_state.token_data, SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.token_data = json.loads(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

# ---------------- GMAIL HELPERS ---------------- #

def create_message_with_attachment(to, subject, body_text, attachment_data=None, attachment_filename=None):
    """Create a plain text email message with optional attachment"""
    message = MIMEMultipart("mixed")
    message['to'] = to
    message['subject'] = subject

    # Use plain text
    text_part = MIMEText(body_text, "plain")
    message.attach(text_part)

    # Add attachment if provided
    if attachment_data and attachment_filename:
        attachment = MIMEApplication(attachment_data, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
        message.attach(attachment)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_draft(service, to, subject, body, attachment_data=None, attachment_filename=None):
    """Create a draft in Gmail"""
    message = create_message_with_attachment(to, subject, body, attachment_data, attachment_filename)
    draft = service.users().drafts().create(
        userId='me',
        body={'message': message}
    ).execute()
    return draft['id']

def schedule_send(service, to, subject, body, send_datetime, attachment_data=None, attachment_filename=None):
    """Schedule an email to be sent at a specific time"""
    try:
        message = create_message_with_attachment(to, subject, body, attachment_data, attachment_filename)
        
        # Convert to milliseconds timestamp
        timestamp_ms = int(send_datetime.timestamp() * 1000)
        message['scheduledSendTime'] = timestamp_ms
        
        # Send with schedule
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return True, f"Email scheduled! Message ID: {result['id']}"
    except HttpError as e:
        # If scheduling fails, create a draft instead
        return False, f"Scheduling not supported. Creating draft instead..."
    except Exception as e:
        return False, f"Error: {str(e)}"

# ---------------- UI ---------------- #

st.set_page_config(page_title="Gmail Scheduler", layout="wide", page_icon="📧")
st.title("📧 Gmail Draft + Scheduler")
st.caption("Create drafts or schedule emails directly through Gmail API")

# ---------- SIDEBAR AUTH & RESUME UPLOAD ---------- #

with st.sidebar:
    st.header("🔐 Authentication")

    if 'token_data' not in st.session_state:
        st.warning("⚠️ Not authenticated")
        
        with st.expander("📋 How to get your token"):
            st.markdown("""
            **Run this locally:**
            
            ```python
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.send'
            ]
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            print(creds.to_json())
            ```
            
            Copy the JSON output and paste below.
            """)
        
        token_input = st.text_area(
            "Paste Gmail token JSON",
            height=200,
            placeholder='{"token": "...", "refresh_token": "..."}'
        )

        if st.button("💾 Save Token", type="primary"):
            try:
                st.session_state.token_data = json.loads(token_input)
                st.success("✅ Authenticated!")
                st.rerun()
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON")
    else:
        st.success("✅ Authenticated with Gmail!")
        if st.button("🔄 Clear Token"):
            del st.session_state.token_data
            st.rerun()

    st.markdown("---")
    st.header("📄 Resume Upload")
    
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
    
    # Store resumes in session state
    if ml_resume:
        st.session_state.ml_resume_data = ml_resume.read()
        st.session_state.ml_resume_name = ml_resume.name
        st.success(f"✓ {ml_resume.name}")
    
    if swe_resume:
        st.session_state.swe_resume_data = swe_resume.read()
        st.session_state.swe_resume_name = swe_resume.name
        st.success(f"✓ {swe_resume.name}")

# ---------- MAIN FORM ---------- #

if 'token_data' in st.session_state:
    st.markdown("---")
    
    # Recipient info
    st.markdown("### 👤 Recipient Information")
    col1, col2 = st.columns(2)

    with col1:
        recipient_name = st.text_input(
            "First Name",
            placeholder="John"
        )

    with col2:
        recipient_email = st.text_input(
            "Email Address",
            placeholder="john.doe@company.com"
        )

    subject_line = st.text_input(
        "📝 Subject Line",
        value="Applied ML in Healthcare – Quick Intro"
    )

    # Recipient type
    st.markdown("### 🎯 Recipient Type")
    recipient_type = st.radio(
        "Select template:",
        ["Recruiter", "Hiring Manager / Technical Contact", "Software Hiring Manager"],
        horizontal=True
    )

    # Select template
    if recipient_type == "Recruiter":
        experience_template = RECRUITER_TEMPLATE
    elif recipient_type == "Hiring Manager / Technical Contact":
        experience_template = HIRING_MANAGER_TEMPLATE
    else:
        experience_template = SOFTWARE_RECRUITER

    # Custom intro
    st.markdown("### ✍️ Custom Company Introduction")
    company_intro = st.text_area(
        f"This will appear after 'Hi {recipient_name or '[First Name]'},'",
        height=150,
        placeholder="I've been following your team's work in AI-driven techniques..."
    )

    # Optional sections
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
    
    # Resume attachment
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
                resume_text = "\n\nI have attached my resume for your reference."
                st.success(f"✓ Will attach: {resume_filename}")
            else:
                st.warning("⚠️ Upload ML resume in sidebar")
        else:
            if 'swe_resume_data' in st.session_state:
                resume_data = st.session_state.swe_resume_data
                resume_filename = st.session_state.swe_resume_name
                resume_text = "\n\nI have attached my resume for your reference."
                st.success(f"✓ Will attach: {resume_filename}")
            else:
                st.warning("⚠️ Upload SWE resume in sidebar")

    # Send options
    st.markdown("---")
    st.markdown("### 📅 Send Options")
    
    send_option = st.radio(
        "When to send:",
        ["Create Draft (Manual Schedule)", "Schedule Send (Automatic)"],
        horizontal=True
    )
    
    send_datetime = None
    if send_option == "Schedule Send (Automatic)":
        send_datetime = st.datetime_input(
            "Pick Send Date & Time",
            min_value=datetime.now(),
            value=datetime.now()
        )
        st.info(f"⏰ Email will be sent at: {send_datetime.strftime('%B %d, %Y at %I:%M %p')}")

    # Build email body
    body_text = f"Hi {recipient_name or '[First Name]'},\n\n{company_intro}\n\n{experience_template}"
    
    if outro_text:
        body_text += f"\n\n{outro_text}"
    
    if resume_text:
        body_text += resume_text
    
    body_text += f"\n\n{SIGNATURE}"

    # Preview
    st.markdown("---")
    with st.expander("👁️ Preview Email", expanded=False):
        st.markdown(f"**To:** {recipient_email or '[Recipient Email]'}")
        st.markdown(f"**Subject:** {subject_line}")
        if send_datetime:
            st.markdown(f"**Scheduled for:** {send_datetime.strftime('%B %d, %Y at %I:%M %p')}")
        st.markdown("---")
        st.text(body_text)
        
        if resume_data:
            st.info(f"📎 Attachment: {resume_filename}")
        
        if not recipient_name:
            st.warning("⚠️ Don't forget first name!")

    # Action button
    st.markdown("---")
    button_text = "📝 Create Draft in Gmail" if send_option == "Create Draft (Manual Schedule)" else f"⏰ Schedule Send for {send_datetime.strftime('%I:%M %p') if send_datetime else 'Later'}"
    
    if st.button(button_text, type="primary", use_container_width=True):
        if not recipient_email:
            st.error("❌ Enter recipient email")
        elif not recipient_name:
            st.error("❌ Enter recipient's first name")
        elif not company_intro:
            st.error("❌ Enter company introduction")
        elif include_resume and not resume_data:
            st.error("❌ Upload selected resume type")
        else:
            service = get_gmail_service()
            
            if service:
                try:
                    if send_option == "Create Draft (Manual Schedule)":
                        # Create draft
                        with st.spinner("Creating draft..."):
                            draft_id = create_draft(
                                service,
                                recipient_email,
                                subject_line,
                                body_text,
                                resume_data,
                                resume_filename
                            )
                        st.success("✅ Draft created in Gmail!")
                        st.info("📧 Open Gmail → Drafts → Click on draft → Schedule send")
                        st.balloons()
                    else:
                        # Schedule send
                        with st.spinner(f"Scheduling email for {send_datetime.strftime('%I:%M %p')}..."):
                            success, message = schedule_send(
                                service,
                                recipient_email,
                                subject_line,
                                body_text,
                                send_datetime,
                                resume_data,
                                resume_filename
                            )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.warning(message)
                            # Fallback to draft
                            draft_id = create_draft(
                                service,
                                recipient_email,
                                subject_line,
                                body_text,
                                resume_data,
                                resume_filename
                            )
                            st.info("✅ Draft created instead. Schedule manually from Gmail.")
                            
                except HttpError as e:
                    st.error(f"❌ Gmail API error: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Not authenticated")

else:
    st.info("👈 Please authenticate with Gmail in the sidebar")
    
    st.markdown("---")
    st.markdown("### ✨ Features:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📝 Create Drafts**")
        st.markdown("Save to Gmail Drafts folder")
    
    with col2:
        st.markdown("**⏰ Schedule Sends**")
        st.markdown("Auto-send at specific time")
    
    with col3:
        st.markdown("**📎 Add Resumes**")
        st.markdown("Attach ML or SWE resume")

# Footer
st.markdown("---")
st.caption("🎓 Graduating Dec 17, 2024 | Built for cold email outreach")
st.caption("💡 Use your personal Gmail account for full functionality!")