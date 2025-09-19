# app.py
import os
import logging
from flask import Flask, render_template, request, jsonify
from src.email_sender import send_single_email

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

# --- NEW ENDPOINT FOR SENDING ONE EMAIL ---
@app.route('/send-one-email', methods=['POST'])
def send_one():
    """
    Receives data for one email from the browser, sends it, and returns the result.
    This is a short-lived function that will not time out.
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

    # Call the new function to send just one email
    result = send_single_email(recipient, sender, subject, body)

    if result['status'] == 'Success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# --- OLD ROUTES ARE NO LONGER NEEDED ---
# The /start-sending, /progress, and /download routes are now handled
# entirely by the browser-side JavaScript.
