
    
# app.py
import os
import logging
from flask import Flask, render_template, request, jsonify
from src.email_sender import send_single_email 
from src.email_verifier import EmailVerifier    
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

verifier = EmailVerifier() 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-one-email', methods=['POST'])
def send_one():
    """
    Receives data, verifies the email address, and ONLY sends if it's valid.
    """
    if not request.json:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    data = request.json
    recipient = data.get('recipient')
    sender = data.get('sender')
    subject = data.get('subject')
    body = data.get('body')

    if not all([recipient, sender, subject, body]):
        return jsonify({"status": "error", "message": "Missing data"}), 400

    recipient_email = recipient.get('email')
    
    # --- Gatekeeper Logic ---
    verification_result = verifier.verify_email(recipient_email)
    
    # Check if the email is something we should send to ('valid' or 'catch-all')
    if verification_result['status'] in ['valid', 'catch-all']:
        is_catch_all = verification_result['status'] == 'catch-all'
        
        # If it's valid, proceed to send the email
        result = send_single_email(recipient, sender, subject, body, is_catch_all)
        
        if result['status'] == 'Success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    else:
        # If verification fails, DO NOT SEND. Immediately return a failed result.
        failed_result = {
            'recipient_email': recipient_email,
            'sender_email': sender.get('email'),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'catch_all': False, # It's not a catch-all if it's invalid
            'status': 'Failed',
            'reason': f"Invalid Email: {verification_result['reason']}"
        }
        # Use status 400 for a client error (bad email provided)
        return jsonify(failed_result), 400

# The if __name__ == '__main__': block has been removed, as Vercel
# will run the app using a production server like Gunicorn.    