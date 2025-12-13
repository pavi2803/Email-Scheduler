"""
Simple SMTP Email Scheduler - Single File Version
Perfect for testing and quick scheduling!

USAGE:
1. Edit the configuration section below
2. Add your scheduled emails
3. Run: python simple_scheduler.py
4. Keep the script running - it will send emails at scheduled times
"""

import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ═══════════════════════════════════════════════════════════
# CONFIGURATION - EDIT THIS SECTION
# ═══════════════════════════════════════════════════════════

# Your Gmail credentials
FROM_EMAIL = 'pavi2468kuk@gmail.com'  # Change this to your email
APP_PASSWORD = 'your_16_char_app_password'  # Get from https://myaccount.google.com/apppasswords

# ═══════════════════════════════════════════════════════════
# SCHEDULED EMAILS - ADD YOUR EMAILS HERE
# ═══════════════════════════════════════════════════════════

SCHEDULED_EMAILS = [
    {
        'to': 'john.doe@optum.com',
        'subject': 'Interested in ML Roles at Optum - USC Grad',
        'recipient_name': 'John',
        'company_intro': "I've been following your team's work in AI-driven utilization review using ML to prioritize cases, improve patient-status decisions, and reduce denial risk; and my background aligns closely with the problems your group focuses on at Optum.",
        'scheduled_time': '2024-12-15 14:30:00',  # YYYY-MM-DD HH:MM:SS format
        'sent': False
    },
    {
        'to': 'jane.smith@company.com',
        'subject': 'Interested in ML Roles at TechCorp - USC Grad',
        'recipient_name': 'Jane',
        'company_intro': "I've been impressed by your team's innovative work in healthcare AI and predictive analytics; my experience in building production ML systems aligns well with your group's focus.",
        'scheduled_time': '2024-12-15 15:00:00',
        'sent': False
    },
    # Add more emails here...
    # Just copy the format above and change the details!
]

# ═══════════════════════════════════════════════════════════
# EMAIL TEMPLATE - YOUR STANDARD CONTENT
# ═══════════════════════════════════════════════════════════

STANDARD_BODY = """My Relevant experience includes:
 • Advanced Modeling: Built MAVeRiC-AD, a vision-language ensemble for Alzheimer's MRI classification (0.90 ROC-AUC across multi-site data). Responsible for dataset design, modeling, and multi-center validation.
 • End-to-End Delivery: Developed and deployed HIPAA-compliant risk prediction systems on 1.5M+ patient records using XGBoost/LightGBM with SHAP explainability—covering data engineering, modeling, evaluation, and operationalization.
 • System-Level Work: Experienced with reproducible pipelines, model tracking, scalable inference, and cross-functional collaboration with clinical and product teams.

I'm exploring opportunities where I can contribute to both high-level ML strategy and hands-on development within healthcare AI. If your group is hiring, or if there's someone you'd recommend I connect with, I'd appreciate the guidance.

Thank you,
Pavithra
Website: https://pavi2803.notion.site/Pavithra-Senthilkumar-36e0d62aea2f4c8086fd279363c59b34
LinkedIn: https://www.linkedin.com/in/pavithra-senthilkumar-2803/
GitHub: https://github.com/pavi2803"""

# ═══════════════════════════════════════════════════════════
# EMAIL SENDING FUNCTIONS - DON'T EDIT BELOW THIS LINE
# ═══════════════════════════════════════════════════════════

def send_email(to_email, subject, body):
    """Send an email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def check_and_send():
    """Check for emails that need to be sent"""
    current_time = datetime.now()
    sent_count = 0
    
    for email in SCHEDULED_EMAILS:
        if email['sent']:
            continue
            
        scheduled_time = datetime.strptime(email['scheduled_time'], '%Y-%m-%d %H:%M:%S')
        
        if scheduled_time <= current_time:
            print(f"\n⏰ Sending email to {email['to']}...")
            
            # Create full email body with your format
            full_body = f"Hi {email['recipient_name']},\n\n{email['company_intro']}\n\n{STANDARD_BODY}"
            
            success, message = send_email(email['to'], email['subject'], full_body)
            
            if success:
                print(f"✅ {message}")
                email['sent'] = True
                sent_count += 1
            else:
                print(f"❌ Failed: {message}")
    
    return sent_count

def display_schedule():
    """Display the current schedule"""
    print("\n" + "="*70)
    print("📋 SCHEDULED EMAILS")
    print("="*70)
    
    pending_count = sum(1 for e in SCHEDULED_EMAILS if not e['sent'])
    sent_count = sum(1 for e in SCHEDULED_EMAILS if e['sent'])
    
    print(f"\nTotal: {len(SCHEDULED_EMAILS)} emails | ⏳ Pending: {pending_count} | ✅ Sent: {sent_count}\n")
    
    for i, email in enumerate(SCHEDULED_EMAILS, 1):
        status = "✅ SENT" if email['sent'] else "⏳ PENDING"
        print(f"{i}. {status} | {email['scheduled_time']} | {email['to']}")
    
    print("\n" + "="*70)

def main():
    """Main scheduler loop"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            Simple SMTP Email Scheduler v1.0                  ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
📧 From: {FROM_EMAIL}
🔄 Check interval: 60 seconds

""".format(FROM_EMAIL=FROM_EMAIL))
    
    # Validate configuration
    if APP_PASSWORD == 'your_16_char_app_password':
        print("❌ ERROR: Please configure your App Password first!")
        print("\n🔑 How to get App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Sign in with ps12049@usc.edu")
        print("3. Click 'Create' and select 'Mail' and 'Other'")
        print("4. Copy the 16-character password")
        print("5. Edit this script and paste it in APP_PASSWORD")
        print("\n💡 Example: APP_PASSWORD = 'abcd efgh ijkl mnop'")
        return
    
    if not SCHEDULED_EMAILS:
        print("❌ ERROR: No emails scheduled!")
        print("Add emails to the SCHEDULED_EMAILS list in the script.")
        return
    
    display_schedule()
    
    print("\n🚀 Scheduler is running. Press Ctrl+C to stop.\n")
    print("💡 Tip: Keep this window open and the script will send emails automatically!")
    
    try:
        check_count = 0
        while True:
            check_count += 1
            
            # Check for emails to send
            sent = check_and_send()
            
            if sent > 0:
                print(f"\n📊 Sent {sent} email(s)!")
                display_schedule()
            
            # Check if all emails are sent
            if all(email['sent'] for email in SCHEDULED_EMAILS):
                print("\n🎉 All scheduled emails have been sent!")
                print("You can close this window now.")
                break
            
            # Show periodic status
            if check_count % 10 == 0:  # Every 10 minutes
                pending = sum(1 for e in SCHEDULED_EMAILS if not e['sent'])
                print(f"⏰ {datetime.now().strftime('%I:%M %p')} - Still running... {pending} emails pending")
            
            time.sleep(60)  # Check every 60 seconds
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Scheduler stopped by user")
        print(f"📊 Status: {sum(1 for e in SCHEDULED_EMAILS if e['sent'])} sent, {sum(1 for e in SCHEDULED_EMAILS if not e['sent'])} pending")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == '__main__':
    main()