import smtplib
import imaplib
import email
from email.message import EmailMessage
import json
from pathlib import Path
import traceback

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def get_credentials():
    config_path = get_base_dir() / 'config' / 'api_keys.json'
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return data.get('email_address'), data.get('email_app_password')
    except Exception as e:
        print(f"Error reading credentials: {e}")
        return None, None

def email_compose(parameters: dict, player=None) -> str:
    """
    Sends or replies to an email.
    """
    try:
        if player:
            player.write_log(f"Executing email_compose with {parameters}")
            player.set_state("working")

        action = parameters.get('action', 'send')
        to_address = parameters.get('to')
        subject = parameters.get('subject', '')
        body = parameters.get('body', '')

        email_address, app_password = get_credentials()
        
        if not email_address or not app_password:
            return "Sir, I could not find your email credentials in the config file."

        if action == 'send':
            if not to_address:
                return "Please specify a recipient to send the email."
            
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = email_address
            msg['To'] = to_address
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(email_address, app_password)
                server.send_message(msg)
            
            return f"Email successfully sent to {to_address}."
            
        elif action == 'reply':
            # Basic IMAP reply logic (reads latest email from sender and replies)
            if not to_address:
                return "Please specify the sender you want to reply to."
                
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(email_address, app_password)
            mail.select('inbox')
            
            # Search for emails from the specified address
            status, messages = mail.search(None, f'(FROM "{to_address}")')
            if status != 'OK' or not messages[0]:
                return f"I couldn't find any recent emails from {to_address}."
                
            latest_email_id = messages[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    original_msg = email.message_from_bytes(response_part[1])
                    original_subject = original_msg['Subject']
                    
            msg = EmailMessage()
            msg['Subject'] = f"Re: {original_subject}" if original_subject else "Reply"
            msg['From'] = email_address
            msg['To'] = to_address
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(email_address, app_password)
                server.send_message(msg)
                
            mail.logout()
            
            return f"Reply successfully sent to {to_address}."
        else:
            return "Unknown email action specified."
            
    except Exception as e:
        error_msg = f"An error occurred while handling the email: {str(e)}"
        if player:
            player.write_log(traceback.format_exc())
        return error_msg
