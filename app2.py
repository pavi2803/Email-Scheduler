import streamlit as st
import base64
from email.mime.text import MIMEText
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
<p>My Relevant experience includes:</p>
<p><b>•</b> Built machine learning models for medical images with ~0.90 ROC-AUC across multi-site data, owning dataset design, modeling, and validation.</p>
<p><b>•</b> Developed and deployed large-scale risk prediction models on 1.5M+ records, including feature engineering, explainability, and production workflows.</p>
<p><b>•</b> Experienced with reproducible pipelines, model tracking, scalable inference, and collaborating with cross-functional teams.</p>
<p>I'm exploring opportunities to contribute to both hands-on ML development and broader ML strategy. If your team is hiring or if there's someone you'd recommend I connect with, I'd appreciate your guidance!</p>
"""

HIRING_MANAGER_TEMPLATE = """
<p>My Relevant experience includes:</p>
<p><b>• Applied ML and finetuning LLM:</b> Built an Agentic vision-language model for medical image classification, achieving ~0.90 ROC-AUC across multi-site data, with ownership across dataset design, modeling, and validation.</p>
<p><b>• End-to-End ML Delivery:</b> Developed and deployed large-scale risk prediction models on 1.5M+ records using XGBoost/LightGBM, including feature engineering, explainability, evaluation, and production workflows.</p>
<p><b>• ML Systems & Collaboration:</b> Experience with reproducible pipelines, model tracking, scalable inference, and close collaboration with cross-functional stakeholders.</p>
<p>I'm exploring opportunities where I can contribute to both hands-on ML development and broader ML strategy. If your team is hiring or if there's someone you'd recommend I connect with, I'd appreciate your guidance!</p>
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

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_message(to, subject, body_html):
    """Create an HTML email message"""
    message = MIMEMultipart("alternative")
    message['to'] = to
    message['subject'] = subject

    # HTML part
    html_part = MIMEText(body_html, "html")
    message.attach(html_part)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def create_draft(service, to, subject, body):
    message = create_message(to, subject, body)
    draft = service.users().drafts().create(
        userId='me',
        body={'message': message}
    ).execute()
    return draft['id']


# ---------------- UI ---------------- #

st.set_page_config(page_title="Gmail Draft Generator", layout="wide")
st.title("📝 Draft Generator")
st.caption("Creates Gmail drafts. Schedule send inside Gmail.")

# ---------- SIDEBAR AUTH ---------- #

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

    # NEW: Recipient type selector
    recipient_type = st.radio(
        "Recipient Type",
        options=["Recruiter", "Hiring Manager / Technical Contact"],
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
    else:
        experience_template = HIRING_MANAGER_TEMPLATE

    # ---------- PREVIEW ---------- #

    st.markdown("---")
    with st.expander("Preview Email"):
        body_html = f"""
        <p>Hi {recipient_name},</p>
        <p>{company_intro}</p>
        {experience_template}
        {SIGNATURE}
        """
        st.markdown(f"**To:** {recipient_email}<br>**Subject:** {subject_line}<br><br>", unsafe_allow_html=True)
        st.markdown(body_html, unsafe_allow_html=True)


    # ---------- CREATE DRAFT ---------- #

    st.markdown("---")
    if st.button("📝 Create Gmail Draft", type="primary", use_container_width=True):
        if not recipient_email or not company_intro:
            st.error("Recipient and company intro required")
        else:
            service = get_gmail_service()

            try:
                draft_id = create_draft(
                    service,
                    recipient_email,
                    subject_line,
                    body_html
                )
                st.success("Draft created successfully!")
                st.info("Open Gmail → Drafts → Schedule Send")
            except HttpError as e:
                st.error(f"Gmail API error: {e}")


else:
    st.info("Authenticate to start creating drafts")