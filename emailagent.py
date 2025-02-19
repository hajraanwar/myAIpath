import smtplib
from email.message import EmailMessage
import re
from fpdf import FPDF

GMAIL_ADDRESS="learning@atomcamp.com"
GMAIL_PASSWORD="nspg fsar hhsl oyuq"
SMTP="smtp.gmail.com"
PORT=587

def email_sender(subject, body, name, receiver_email_add):
    """Send an email with the specified subject, body, and receiver address."""

    try:
        # Ensure necessary constants are defined
        assert 'GMAIL_ADDRESS' in globals(), "Sender email address not defined."
        assert 'GMAIL_PASSWORD' in globals(), "Sender email password not defined."
        assert 'SMTP' in globals(), "SMTP server address not defined."
        assert 'PORT' in globals(), "SMTP server port not defined."

        sender_email = GMAIL_ADDRESS
        sender_password = GMAIL_PASSWORD

        # Clean the email body
        body = re.sub(r'[*#]', '', body).strip()

        # Create a PDF file with the body content
        pdf_filename = "Your Personalized Roadmap.pdf"

        pdf = FPDF()
        pdf.add_page()
        # Use built-in Helvetica font
        pdf.set_font('Helvetica', '', 12)

        # Convert body text to plain text, removing any HTML/markdown
        plain_text = re.sub(r'[^\x00-\x7F]+', ' ', body)
        pdf.multi_cell(0, 10, plain_text)
        pdf.output(pdf_filename)


        # Format the body for email display
        formatted_body = f"""
        Hello {name},

        {body}

        Best regards,
        MyAIpath @atomcamp
        """

        # Create the email message
        msg = EmailMessage()
        msg.set_content(formatted_body, charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email_add

        # Attach the PDF file
        with open(pdf_filename, "rb") as pdf_file:
            msg.add_attachment(pdf_file.read(), maintype="application", subtype="pdf", filename=pdf_filename)

        # Set up the SMTP session
        with smtplib.SMTP(SMTP, PORT) as session:
            session.starttls()  # Secure the connection
            session.login(sender_email, sender_password)  # Login to the SMTP server
            session.send_message(msg)  # Send the email

        print("Mail Sent!")
    except AssertionError as ae:
        print(f"Configuration Error: {ae}")
    except smtplib.SMTPException as smtp_err:
        print(f"SMTP Error: {smtp_err}")
    except Exception as e:
        print(f"Error sending email: {e}")
