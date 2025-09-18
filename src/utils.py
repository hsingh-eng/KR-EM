# src/utils.py

import csv
import logging

def load_emails_from_file(filepath):
    """Loads a list of emails from a text file, one per line."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"The file {filepath} was not found.")
        return []

# --- NEW FUNCTION ---
def load_emails_from_csv(filepath):
    """Loads a list of emails from a CSV file's 'Email' column."""
    emails = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check for 'Email' or 'email' to be flexible with column names
                email = row.get('Email') or row.get('email')
                if email:
                    emails.append(email.strip())
                else:
                    logging.warning(f"No 'Email' column found in row: {row}")
        return emails
    except FileNotFoundError:
        logging.error(f"The file {filepath} was not found.")
        return []
    except Exception as e:
        logging.error(f"An error occurred while reading the CSV file: {e}")
        return []

def save_results_to_csv(filepath, results):
    """Saves the verification results to a CSV file."""
    if not results:
        logging.warning("No results to save.")
        return

    headers = results[0].keys()
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Results successfully saved to {filepath}")
    except IOError as e:
        logging.error(f"Could not write to file {filepath}: {e}")

def analyze_results(results):
    """Provides a summary of the verification results."""
    summary = {
        'valid': 0, 'invalid': 0, 'catch-all': 0, 'unknown': 0,
        'disposable': 0, 'role_accounts': 0, 'total': len(results)
    }
    for res in results:
        summary[res['status']] += 1
        if res['is_disposable']:
            summary['disposable'] += 1
        if res['is_role_account']:
            summary['role_accounts'] += 1
    return summary