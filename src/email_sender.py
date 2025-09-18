# src/email_sender.py
import csv, smtplib, ssl, time, logging, random, uuid
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
TRACKING_SERVER_DOMAIN = "http://YOUR_SERVER_IP_OR_DOMAIN:5000"

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
    if not recipients or not sender_accounts:
        return

    num_senders = len(sender_accounts)
    context = ssl._create_unverified_context()
    total_recipients = len(recipients)
    success_count = 0
    
    report_data = []

    for i, person in enumerate(recipients):
        progress = int(((i + 1) / total_recipients) * 100)
        recipient_email = person['email']
        
        # Yield current status before sending
        yield {'progress': progress, 'current_email': recipient_email, 'success_count': success_count}

        current_sender = sender_accounts[i % num_senders]
        sender_email = current_sender['email']
        sender_password = current_sender['password']
        tracking_id = str(uuid.uuid4())
        
        status = 'Failed'
        reason = ''

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                msg = EmailMessage()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject_template.format(name=person['name'])
                html_content = body_template.format(name=person['name']).replace('\n', '<br>')
                html_body = f"""<html><body>{html_content}<br><br><img src="{TRACKING_SERVER_DOMAIN}/track?id={tracking_id}" width="1" height="1" alt=""></body></html>"""
                msg.set_content(body_template.format(name=person['name']))
                msg.add_alternative(html_body, subtype='html')
                server.send_message(msg)
                
                status = 'Success'
                success_count += 1

        except smtplib.SMTPAuthenticationError as e:
            reason = f"Authentication error with {sender_email}. Check App Password."
            logging.error(f"Failed to send to {recipient_email}: {reason}")
        except Exception as e:
            reason = str(e)
            logging.error(f"Failed to send to {recipient_email}: {reason}")
        
        report_data.append({
            'recipient_email': recipient_email,
            'sender_email': sender_email,
            'status': status,
            'reason': reason
        })
        
        if i < total_recipients - 1:
            time.sleep(random.randint(20, 30))

    # Yield the final report data
    yield {'report': report_data}