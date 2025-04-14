import os
import smtplib
import logging
import subprocess
from dotenv import load_dotenv
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ---------------- Logging Setup ---------------- #
logging.basicConfig(
    filename='smtp_mail.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
)

line_break = "---"

# ---------------- Config ---------------- #
SMTP_SERVER = os.get_env("SMTP_SERVER")
SMTP_PORT = os.get_env("SMTP_PORT")
USERNAME =  os.get_env("USERNAME")
PASSWORD =  os.get_env("PASSWORD")
FROM_ADDRESS = "kimbal-alerts@apdclintelli.in"
TO_ADDRESS = [
    "naman.kumar@kimbal.io",
    "sanchit.rathee@kimbal.io",
    "amit.sharma@kimbal.io",
    "jagdeep@kimbal.io",
    "harojyoti.borah@kimbal.io",
    "shahadul.haque@intellismartinfra.in",
    "ronit.bhararia@intellismartinfra.in",
    "abhishek.soni@intellismartinfra.in",
    "chandan.s@fluentgrid.com",
    "prakash.g@fluentgrid.com"
]
SUBJECT = "Daily Queue Push Data Count Report || APDCL Pkg 7"
BODY = (
    "Hi Team,\n\n"
    "Please find attached the automated CSV report containing today's queue push data count.\n\n"
    "*This is a system-generated email.*\n\n"
    "Regards,\n"
    "Kimbal Alerts"
)
# ---------------- Run PowerShell Script ---------------- #
def run_powershell_script(script_path):
    try:
        logging.info(f"Running PowerShell script: {script_path}")
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logging.error(f"PowerShell script failed:\n{result.stderr}")
            print("❌ PowerShell script failed:", result.stderr)
        else:
            logging.info("PowerShell script executed successfully.")
            print("✅ PowerShell script executed.")
    except Exception as e:
        logging.exception("Error running PowerShell script")
        print("❌ Failed to run PowerShell script:", str(e))

# ---------------- Get Today's Expected CSV File ---------------- #
def get_expected_csv_file(directory, base_filename=""):
    date_string = datetime.now().strftime("%Y-%m-%d")
    expected_file = os.path.join(directory, f"{base_filename}_{date_string}.csv")
    if os.path.exists(expected_file):
        logging.info(f"Found expected CSV file: {expected_file}")
        return expected_file
    else:
        logging.warning(f"Expected CSV file not found: {expected_file}")
        return None

# ---------------- Construct and Send Email ---------------- #
def send_email_with_attachment(attachment_path):
    msg = MIMEMultipart()
    msg['From'] = FROM_ADDRESS
    msg['To'] = ', '.join(TO_ADDRESS)
    msg['Subject'] = SUBJECT
    msg.attach(MIMEText(BODY, 'plain'))

    if attachment_path:
        try:
            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
            logging.info(f"Attached file: {attachment_path}")
        except Exception as e:
            logging.exception("Error attaching CSV file")
            print("⚠️ Could not attach CSV file:", str(e))

    try:
        logging.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            logging.debug("TLS started successfully")
            server.login(USERNAME, PASSWORD)
            logging.debug(f"Logged in as {USERNAME}")
            server.sendmail(FROM_ADDRESS, TO_ADDRESS, msg.as_string())
            logging.info(f"Email sent successfully to {TO_ADDRESS}\n{50 * line_break}")
            print("✅ Email sent successfully!")

    except smtplib.SMTPAuthenticationError as e:
        error_msg = e.smtp_error.decode() if hasattr(e.smtp_error, 'decode') else str(e)
        logging.error(f"❌ SMTP Authentication failed: {error_msg}\n{50 * line_break}")
        print("❌ Authentication failed:", error_msg)

    except Exception as e:
        logging.exception(f"❌ Failed to send email\n{50 * line_break}")
        print("❌ Failed to send email:", str(e))

# ---------------- Main ---------------- #
if __name__ == "__main__":
    powershell_script_path = "generate_sql_report.ps1"  # <-- your script path
    csv_directory = "D:\\dist"  # must match what's used in your .ps1
    base_csv_name = "QueuePushAudit"  # e.g., "QueuePushAudit" if that's the originalFileName

    run_powershell_script(powershell_script_path)
    csv_file = get_expected_csv_file(csv_directory, base_csv_name)
    send_email_with_attachment(csv_file)
