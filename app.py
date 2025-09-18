# app.py (Updated Version)
import os
import uuid
import json
import threading
import csv
import logging
from flask import Flask, render_template, request, Response, send_from_directory
from werkzeug.utils import secure_filename
from src.email_sender import load_sender_accounts, load_recipients_from_csv, send_emails_with_progress

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER

logging.basicConfig(level=logging.INFO)

# --- In-memory job store for simplicity ---
job_streams = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_email_task(job_id, subject, body, recipients_path, senders_path):
    """The background task for sending emails."""
    job_streams[job_id] = []
    
    sender_accounts = load_sender_accounts(senders_path)
    recipients = load_recipients_from_csv(recipients_path)

    if not sender_accounts or not recipients:
        error_data = json.dumps({'error': 'Failed to load sender or recipient file. Please check files and try again.'})
        job_streams[job_id].append(f"event: error\ndata: {error_data}\n\n")
        return

    for update in send_emails_with_progress(recipients, sender_accounts, subject, body):
        if 'report' in update:
            report_data = update['report']
            if not os.path.exists(app.config['REPORTS_FOLDER']):
                os.makedirs(app.config['REPORTS_FOLDER'])
            
            report_filename = f"report_{job_id}.csv"
            report_filepath = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
            
            if report_data:
                try:
                    headers = report_data[0].keys()
                    with open(report_filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(report_data)
                except Exception as e:
                    logging.error(f"Error writing report file: {e}")

            job_streams[job_id].append(f"event: complete\ndata: {report_filename}\n\n")
            
            # Clean up uploaded files
            try:
                os.remove(recipients_path)
                os.remove(senders_path)
            except OSError as e:
                logging.error(f"Error removing uploaded files: {e}")

        else:
            job_streams[job_id].append(f"event: progress\ndata: {json.dumps(update)}\n\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-sending', methods=['POST'])
def start_sending():
    subject = request.form.get('subject')
    body = request.form.get('body')
    recipients_file = request.files.get('recipients_file')
    senders_file = request.files.get('senders_file') # <-- Get the new senders file

    # --- Validation for both files ---
    if not recipients_file or not allowed_file(recipients_file.filename):
        return {"error": "Invalid or missing recipients CSV file."}, 400
    if not senders_file or not allowed_file(senders_file.filename):
        return {"error": "Invalid or missing senders CSV file."}, 400

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    job_id = str(uuid.uuid4())

    # --- Save both files with unique names ---
    recipients_filename = f"recipients_{job_id}.csv"
    senders_filename = f"senders_{job_id}.csv"
    recipients_path = os.path.join(app.config['UPLOAD_FOLDER'], recipients_filename)
    senders_path = os.path.join(app.config['UPLOAD_FOLDER'], senders_filename)
    
    recipients_file.save(recipients_path)
    senders_file.save(senders_path)

    # --- Start background thread with both file paths ---
    thread = threading.Thread(target=run_email_task, args=(job_id, subject, body, recipients_path, senders_path))
    thread.start()

    return {"job_id": job_id}

@app.route('/progress/<job_id>')
def progress(job_id):
    def generate():
        sent_indices = 0
        while True:
            if job_id in job_streams:
                while sent_indices < len(job_streams[job_id]):
                    data = job_streams[job_id][sent_indices]
                    sent_indices += 1
                    yield data
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['REPORTS_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)