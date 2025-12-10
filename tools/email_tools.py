import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from agno.tools import Toolkit
from agno.utils.log import logger

class EmailTools(Toolkit):
    def __init__(self, email_address: str, app_password: str, imap_server="imap.gmail.com", smtp_server="smtp.gmail.com"):
        super().__init__(name="email_tools")
        self.email_address = email_address
        self.password = app_password
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.register_ops([self.send_message, self.search_messages])

    def send_message(self, to_email: str, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.email_address, self.password)
                server.send_message(msg)
            return f"Email sent to {to_email}"
        except Exception as e:
            return f"Error sending email: {e}"

    def search_messages(self, query: str = "UNSEEN", limit: int = 5):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            mail.select("inbox")
            status, messages = mail.search(None, query)
            if status != "OK": return "No messages."
            
            results = []
            for e_id in messages[0].split()[-limit:]:
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes): subject = subject.decode()
                        results.append(f"Subject: {subject}")
            return results
        except Exception as e:
            return f"Error fetching emails: {e}"
