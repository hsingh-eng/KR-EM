# src/email_verifier.py

import dns.resolver
import socket
import smtplib
import re
import logging
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Commonly known disposable email providers
DISPOSABLE_DOMAINS = {
    "temp-mail.org", "mailinator.com", "10minutemail.com", 
}

# Common role-based account prefixes
ROLE_ACCOUNTS = {
    "info", "admin", "sales", "contact", "support",
}

class EmailVerifier:
    def __init__(self, from_email="verifier@example.com", timeout=10):
        """Initializes the verifier."""
        self.from_email = from_email
        self.timeout = timeout
        try:
            self.helo_name = socket.getfqdn()
        except Exception:
            self.helo_name = "google.com" 

    def _get_mx_records(self, domain):
        """Gets MX records for a domain. Returns None if no records are found or domain is invalid."""
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_records = sorted([(r.preference, r.exchange.to_text()) for r in records])
            return mx_records
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            # This is the key part: if the domain does not exist or has no MX records, return None.
            return None

    def _generate_random_email(self, domain):
        """Generates a highly unlikely random email address for catch-all detection."""
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        return f"{random_part}@{domain}"

    def verify_email(self, email):
        """
        Performs a comprehensive verification of a single email address.
        """
        # Default result structure
        result = {
            'email': email, 
            'status': 'unknown', 
            'reason': 'An unexpected error occurred',
            'is_disposable': False, 
            'is_role_account': False
        }

        # 1. Syntax Check
        if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
            result.update({'status': 'invalid', 'reason': 'Invalid email syntax'})
            return result

        username, domain = email.split('@')
        domain = domain.lower()
        
        result['is_disposable'] = domain in DISPOSABLE_DOMAINS
        result['is_role_account'] = username.lower() in ROLE_ACCOUNTS

        # 2. DNS (MX Record) Check
        mx_records = self._get_mx_records(domain)
        if not mx_records:
            result.update({'status': 'invalid', 'reason': 'No MX records found for domain'})
            return result

        # 3. SMTP Connection Check
        try:
            with smtplib.SMTP(mx_records[0][1], timeout=self.timeout) as server:
                server.set_debuglevel(0)
                server.ehlo(self.helo_name)
                server.mail(self.from_email)
                
                # Check the actual email address
                code, message = server.rcpt(email)

                if code == 250:
                    # Address is accepted, now check for catch-all
                    random_email = self._generate_random_email(domain)
                    catch_all_code, _ = server.rcpt(random_email)
                    if catch_all_code == 250:
                        result.update({'status': 'catch-all', 'reason': 'Domain accepts all emails'})
                    else:
                        result.update({'status': 'valid', 'reason': 'SMTP server confirmed address exists'})
                
                elif code in [550, 551, 553, 554]:
                    result.update({'status': 'invalid', 'reason': f"SMTP rejected address: {message.decode(errors='ignore')}"})
                
                else: # Handle temporary errors or other codes
                    result.update({'status': 'unknown', 'reason': f"SMTP Error (Code: {code}): {message.decode(errors='ignore')}"})

        except (socket.timeout, smtplib.SMTPServerDisconnected, ConnectionRefusedError, OSError) as e:
            result.update({'status': 'unknown', 'reason': f'SMTP connection failed: {e}'})
        
        except Exception as e:
            # Catch any other unexpected errors during verification
            result.update({'status': 'unknown', 'reason': f'A verification error occurred: {e}'})
            
        return result

    def bulk_verify(self, emails, workers=10):
        """Verifies a list of emails in bulk using threading."""
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_email = {executor.submit(self.verify_email, email.strip()): email for email in emails}
            for future in tqdm(as_completed(future_to_email), total=len(emails), desc="Verifying Emails"):
                email = future_to_email[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    logging.error(f'"{email}" generated an exception: {exc}')
        return results