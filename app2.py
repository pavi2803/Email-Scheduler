import streamlit as st
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email.mime.application import MIMEApplication
import json
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
I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions, (link: [https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1]) and have built end-to-end ML systems including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.
"""

HIRING_MANAGER_TEMPLATE = """
<p>I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions, (link: [https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1]) and have built end-to-end ML systems including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.</p>
"""

SOFTWARE_RECRUITER = """
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
        st.session_state.token_data, SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.token_data = json.loads(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


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


# ---------------- UI ---------------- #

st.set_page_config(page_title="Gmail Draft Generator", layout="wide")
st.title("📝 Draft Generator")
st.caption("Creates Gmail drafts. Schedule send inside Gmail.")

# ---------- SIDEBAR AUTH & RESUME UPLOAD ---------- #

with st.sidebar:
    st.header("🔐 Authentication")

    if 'token_data' not in st.session_state:
        token_input = st.text_area(
            "Paste Gmail token JSON",
            height=200,
            placeholder='{"token": "...", "refresh_token": "..."}'
        )

        if st.button("Save Token"):
            try:
                st.session_state.token_data = json.loads(token_input)
                st.success("Authenticated")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON")

    else:
        st.success("Authenticated")
        if st.button("Clear Token"):
            del st.session_state.token_data
            st.rerun()

    st.markdown("---")
    st.header("📄 Resume Files")
    st.caption("Upload your resumes once - they'll be saved for this session")
    
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
        st.success(f"✓ ML Resume: {ml_resume.name}")
    
    if swe_resume:
        st.session_state.swe_resume_data = swe_resume.read()
        st.session_state.swe_resume_name = swe_resume.name
        st.success(f"✓ SWE Resume: {swe_resume.name}")


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

    # Updated: Three recipient type options
    recipient_type = st.radio(
        "Recipient Type",
        options=["Recruiter", "Hiring Manager / Technical Contact", "Software Hiring Manager"],
        horizontal=True
    )

    company_intro = st.text_area(
        "Custom Company Intro",
        height=150,
        value="I've been following your team's work in AI-driven techniques to prioritize cases, improve patient-status decisions, and reduce denial risk; and my background aligns closely with the problems your group focuses on at Optum."
    )

    # Select template based on recipient type
    if recipient_type == "Recruiter":
        experience_template = RECRUITER_TEMPLATE
    elif recipient_type == "Hiring Manager / Technical Contact":
        experience_template = HIRING_MANAGER_TEMPLATE
    else:  # Software Hiring Manager
        experience_template = SOFTWARE_RECRUITER

    # ---------- OPTIONAL SECTIONS ---------- #
    
    st.markdown("---")
    st.subheader("Optional Sections")
    
    # Optional outro
    include_outro = st.checkbox("Include closing paragraph")
    outro_text = ""
    if include_outro:
        outro_text = st.text_area(
            "Closing Paragraph",
            height=100,
            value="Would love to briefly discuss how my background could support your team.",
            placeholder="Add a custom closing paragraph..."
        )
    
    # Optional resume attachment
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
                st.warning("⚠️ Please upload your ML/Data Science resume in the sidebar")
        else:
            if 'swe_resume_data' in st.session_state:
                resume_data = st.session_state.swe_resume_data
                resume_filename = st.session_state.swe_resume_name
                resume_text = "<p>I have attached my resume for your reference.</p>"
                st.success(f"✓ Will attach: {resume_filename}")
            else:
                st.warning("⚠️ Please upload your Software Engineering resume in the sidebar")

    # ---------- PREVIEW ---------- #

    st.markdown("---")
    with st.expander("Preview Email"):
        # Build email body
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


    # ---------- CREATE DRAFT ---------- #

    st.markdown("---")
    if st.button("📝 Create Gmail Draft", type="primary", use_container_width=True):
        if not recipient_email or not company_intro:
            st.error("Recipient and company intro required")
        elif include_resume and not resume_data:
            st.error("Please upload the selected resume type in the sidebar")
        else:
            service = get_gmail_service()

            try:
                draft_id = create_draft(
                    service,
                    recipient_email,
                    subject_line,
                    body_html,
                    resume_data,
                    resume_filename
                )
                st.success("✅ Draft created successfully with attachment!" if resume_data else "✅ Draft created successfully!")
                st.info("Open Gmail → Drafts → Schedule Send")
            except HttpError as e:
                st.error(f"Gmail API error: {e}")


else:
    st.info("Authenticate to start creating drafts")