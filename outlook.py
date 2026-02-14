import streamlit as st
import base64
import json
import requests

# Microsoft Graph endpoint
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0/me"

# ---------------- TEMPLATES ---------------- #

RECRUITER_TEMPLATE = """
<p>I recently published work on Agentic MoE based architecture for diagnosis of dementia conditions, 
(link: <a href="https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1">https://www.biorxiv.org/content/10.1101/2025.09.05.674598v1</a>) and have built end-to-end ML systems 
including vision-language models for medical imaging (0.90 ROC-AUC) and risk prediction on 1.5M+ records.</p>
"""

HIRING_MANAGER_TEMPLATE = RECRUITER_TEMPLATE

SOFTWARE_RECRUITER = """
<p><b>• Backend Development & Data Pipelines:</b> Engineered scalable data workflows using Apache Spark and Hive SQL, processing 1.5M+ records.</p>
<p><b>• System Architecture & Performance:</b> Implemented distributed systems with ~2× throughput improvements.</p>
<p><b>• Full-Stack & Deployment:</b> Built production ML systems with APIs, AWS, CI/CD, and monitoring.</p>
"""

SIGNATURE = """
<p>Thank you,<br>
Pavithra<br>
<a href="https://pavi2803.github.io/pavithrasenthilkumar.github.io/">Website</a> | 
<a href="https://www.linkedin.com/in/pavithra-senthilkumar-2803/">LinkedIn</a> | 
<a href="https://github.com/pavi2803">GitHub</a></p>
"""

# ---------------- AUTH HELPER ---------------- #

def get_headers():
    if "access_token" not in st.session_state:
        return None
    return {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }

# ---------------- CREATE DRAFT ---------------- #

def create_outlook_draft(to, subject, body_html):
    """Create a draft email in Outlook"""
    headers = get_headers()
    if not headers:
        return False, "Not authenticated"

    message = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body_html
        },
        "toRecipients": [
            {"emailAddress": {"address": to}}
        ]
    }

    try:
        response = requests.post(
            f"{GRAPH_BASE_URL}/messages",
            headers=headers,
            data=json.dumps(message)
        )

        if response.status_code in [200, 201]:
            return True, "Draft created successfully!"
        else:
            return False, f"Error: {response.text}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ---------------- UI ---------------- #

st.set_page_config(page_title="Outlook Draft Creator", page_icon="📬", layout="wide")

st.title("📬 Outlook Draft Creator")
st.markdown("Create personalized email drafts in Outlook - Schedule them manually later!")

# ---------- SIDEBAR AUTH ---------- #
with st.sidebar:
    st.header("🔐 Outlook Authentication")
    
    if "access_token" not in st.session_state:
        st.warning("⚠️ Not authenticated")
        
        with st.expander("📋 How to get Access Token"):
            st.markdown("""
            ### Quick Setup:
            
            1. **Register an app in Azure:**
               - Go to [Azure Portal](https://portal.azure.com/)
               - Navigate to "Azure Active Directory" → "App registrations"
               - Click "New registration"
               - Name: "Outlook Draft Creator"
               - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
               - Click "Register"
            
            2. **Configure API permissions:**
               - In your app, go to "API permissions"
               - Click "Add a permission" → "Microsoft Graph" → "Delegated permissions"
               - Add: `Mail.ReadWrite` and `Mail.Send`
               - Click "Grant admin consent"
            
            3. **Get your token:**
               - Use Microsoft Graph Explorer: [https://developer.microsoft.com/en-us/graph/graph-explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
               - Sign in with your Outlook account
               - Run any query (e.g., GET /me)
               - Copy the "Access token" from the toolbar
               - Paste it below
            
            **Note:** Token expires after ~1 hour. You'll need to get a new one.
            """)
        
        token = st.text_area(
            "Paste Microsoft Graph Access Token:",
            height=100,
            placeholder="eyJ0eXAiOiJKV1QiLCJub..."
        )

        if st.button("💾 Save Token", type="primary"):
            st.session_state.access_token = token.strip()
            st.success("✅ Token saved!")
            st.rerun()
    else:
        st.success("✅ Authenticated with Outlook!")
        if st.button("🔄 Clear Token"):
            del st.session_state.access_token
            st.rerun()

# ---------- MAIN FORM ---------- #

if "access_token" in st.session_state:
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

    # Select template based on type
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
        placeholder="I've been following your team's work in AI-driven clinical decision support and am impressed by your recent deployment of real-time risk prediction models...",
        height=150
    )

    # Build full email
    body_html = f"""
    <p>Hi {recipient_name or '[First Name]'},</p>
    <p>{company_intro}</p>
    {experience_template}
    {SIGNATURE}
    """

    # Preview
    st.markdown("---")
    with st.expander("👁️ Preview Email", expanded=False):
        st.markdown(f"**To:** {recipient_email or '[Recipient Email]'}")
        st.markdown(f"**Subject:** {subject_line}")
        st.markdown("---")
        st.markdown(body_html, unsafe_allow_html=True)
        
        if not recipient_name:
            st.warning("⚠️ Don't forget to enter recipient's first name!")

    # Template reference
    with st.expander("📄 Templates (Reference)"):
        st.markdown("**Recruiter / Hiring Manager Template:**")
        st.markdown(RECRUITER_TEMPLATE, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**Software Hiring Manager Template:**")
        st.markdown(SOFTWARE_RECRUITER, unsafe_allow_html=True)

    # Create draft button
    st.markdown("---")
    if st.button("📬 Create Draft in Outlook", type="primary", use_container_width=True):
        if not recipient_email:
            st.error("❌ Please enter recipient email address")
        elif not recipient_name:
            st.error("❌ Please enter recipient's first name")
        elif not company_intro:
            st.error("❌ Please enter custom company introduction")
        else:
            with st.spinner("Creating draft in Outlook..."):
                success, message = create_outlook_draft(
                    recipient_email,
                    subject_line,
                    body_html
                )
            
            if success:
                st.success(f"✅ {message}")
                st.info("📧 Check your Outlook → Drafts folder. You can now schedule it manually!")
                st.balloons()
            else:
                st.error(f"❌ {message}")

else:
    st.info("👈 Please authenticate with Outlook in the sidebar to start creating drafts!")
    
    st.markdown("---")
    st.markdown("### ✨ How This Works:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**1️⃣ Authenticate**")
        st.markdown("Get your access token from Microsoft Graph Explorer")
    
    with col2:
        st.markdown("**2️⃣ Create Draft**")
        st.markdown("Fill in details and create draft in Outlook")
    
    with col3:
        st.markdown("**3️⃣ Schedule Manually**")
        st.markdown("Open Outlook and schedule the draft whenever you want!")

# Footer
st.markdown("---")
st.caption("🎓 Graduating Dec 17, 2024 | Built for cold email outreach")
st.caption("💡 Tip: Drafts are saved in your Outlook - schedule them at your convenience!")