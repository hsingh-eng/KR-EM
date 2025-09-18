# main.py

import time
import argparse
import logging
from src.email_verifier import EmailVerifier
# --- MODIFIED: Import the new CSV loading function ---
from src.utils import load_emails_from_file, load_emails_from_csv, save_results_to_csv, analyze_results

def setup_logging():
    """Configures logging to print to console and save to a file."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("verification_results.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Advanced Email Verification Tool.")
    parser.add_argument(
        "-i", "--input-file",
        # --- MODIFIED: Changed default to EmailTest.csv ---
        default="./EmailTest.csv",
        help="Path to the input file with emails (supports .txt and .csv)."
    )
    parser.add_argument(
        "-o", "--output-file",
        default="./results.csv",
        help="Path to save the CSV results file."
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=10,
        help="Number of concurrent threads to use for verification."
    )
    args = parser.parse_args()

    # --- MODIFIED: Load emails based on file type ---
    logging.info(f"Loading emails from {args.input_file}...")
    emails_to_verify = []
    if args.input_file.lower().endswith('.csv'):
        emails_to_verify = load_emails_from_csv(args.input_file)
    elif args.input_file.lower().endswith('.txt'):
        emails_to_verify = load_emails_from_file(args.input_file)
    else:
        logging.error(f"Unsupported file type: {args.input_file}. Please provide a .csv or .txt file.")
        return

    if not emails_to_verify:
        logging.warning("No emails to verify. Exiting.")
        return
    logging.info(f"Found {len(emails_to_verify)} emails to process.")

    # --- Verification (This section remains unchanged) ---
    verifier = EmailVerifier()
    
    logging.info(f"Starting verification with {args.workers} workers...")
    start_time = time.time()
    
    results = verifier.bulk_verify(emails_to_verify, workers=args.workers)
    
    end_time = time.time()
    
    # --- Save and Analyze (This section remains unchanged) ---
    if results:
        save_results_to_csv(args.output_file, results)
        summary = analyze_results(results)

        logging.info("="*40)
        logging.info("Verification Complete!")
        logging.info(f"Total time taken: {end_time - start_time:.2f} seconds")
        logging.info("--- Results Summary ---")
        
        summary_report = (
            f"\n{'Total Emails Verified:':<25} {summary['total']}"
            f"\n{'-' * 25}"
            f"\n{'Valid:':<25} {summary['valid']}"
            f"\n{'Invalid:':<25} {summary['invalid']}"
            f"\n{'Catch-All (Risky):':<25} {summary['catch-all']}"
            f"\n{'Unknown/Error:':<25} {summary['unknown']}"
            f"\n{'-' * 25}"
            f"\n{'Disposable Emails Found:':<25} {summary['disposable']}"
            f"\n{'Role Accounts Found:':<25} {summary['role_accounts']}"
        )
        logging.info(summary_report)
        print(f"\nDetailed results saved in {args.output_file}")
        print(f"Detailed logs saved in verification_results.log")

if __name__ == '__main__':
    main()