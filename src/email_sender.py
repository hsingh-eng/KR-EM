# src/email_sender.py
import csv, smtplib, ssl, time, logging, random, uuid
from email.message import EmailMessage
from datetime import datetime

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
TRACKING_SERVER_DOMAIN = "http://YOUR_SERVER_IP_OR_DOMAIN:5000"

# --- MODIFIED: Function now accepts 'is_catch_all' ---
def send_single_email(recipient, sender, subject_template, body_template, is_catch_all):
    """
    Sends a single email and returns a dictionary with the result,
    including whether the domain is a catch-all.
    """
    sender_email = sender['email']
    sender_password = sender['password']
    recipient_email = recipient['email']
    tracking_id = str(uuid.uuid4())
    
    status = 'Failed'
    reason = ''
    timestamp = ''

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            msg = EmailMessage()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject_template.format(name=recipient['name'])
            html_content = body_template.format(name=recipient['name']).replace('\n', '<br>')
            html_body = f"""<html><body>{html_content}<br><br><img src="{TRACKING_SERVER_DOMAIN}/track?id={tracking_id}" width="1" height="1" alt=""></body></html>"""
            msg.set_content(body_template.format(name=recipient['name']))
            msg.add_alternative(html_body, subtype='html')
            server.send_message(msg)
            
            status = 'Success'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"Successfully sent email to {recipient_email}")

    except smtplib.SMTPAuthenticationError:
        reason = f"Authentication error with {sender_email}. Check App Password."
        logging.error(f"Failed to send to {recipient_email}: {reason}")
    except Exception as e:
        reason = str(e)
        logging.error(f"Failed to send to {recipient_email}: {reason}")
    
    # --- MODIFIED: Added 'catch_all' to the returned dictionary ---
    return {
        'recipient_email': recipient_email,
        'sender_email': sender_email,
        'timestamp': timestamp,
        'catch_all': is_catch_all, # <-- New column
        'status': status,
        'reason': reason
    }

# --- UNUSED BUT KEPT FOR REFERENCE ---
def load_sender_accounts(filepath):
    accounts = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('email') and row.get('app_password'):
                    accounts.append({'email': row['email'].strip(), 'password': row['app_password'].strip()})
        return accounts
    except FileNotFoundError:
        return []

def load_recipients_from_csv(csv_filepath):
    recipients = []
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Name') and row.get('Email'):
                    recipients.append({'name': row['Name'].strip(), 'email': row['Email'].strip()})
        return recipients
    except FileNotFoundError:
        return []

def send_emails_with_progress(recipients, sender_accounts, subject_template, body_template):
    # This function is no longer used by the web app but is kept for potential CLI use.
    pass