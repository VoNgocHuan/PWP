"""Email service for sending ticket purchase confirmations.

This module provides email sending functionality for the email auxiliary service.
It handles formatting and delivery of confirmation emails when tickets are purchased.
"""
from email.message import EmailMessage
import logging
import smtplib
import sys
from datetime import datetime

try:
    from .config import config
except ImportError:
    from config import config

logger = logging.getLogger("email-service")


def send_confirmation_email(recipient_email, recipient_name, event_title, ticket_name, order_id):
    """Send a ticket purchase confirmation email.

    Args:
        recipient_email: Email address of the buyer
        recipient_name: Name of the buyer
        event_title: Title of the event
        ticket_name: Name of the ticket type (e.g., VIP, Standard)
        order_id: ID of the order

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    cfg = config["default"]
    email_body = format_email_body(recipient_name, event_title, ticket_name, order_id)
    subject = "Order Confirmation - %s" % event_title

    logger.info("Sending confirmation email to %s for order #%s", recipient_email, order_id)

    if cfg.PRINT_TO_CONSOLE:
        print_email(recipient_email, subject, email_body)

    if cfg.SMTP_ENABLED:
        try:
            send_smtp_email(cfg, recipient_email, subject, email_body)
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("SMTP delivery failed for order #%s: %s", order_id, exc)
            return False

    logger.info("Email sent successfully to %s for order #%s", recipient_email, order_id)
    return True


def send_smtp_email(cfg, recipient_email, subject, body):
    """Send an email using the configured SMTP server.

    Args:
        cfg: Active service configuration object
        recipient_email: Recipient email address
        subject: Message subject
        body: Plain-text message body
    """
    message = EmailMessage()
    message["From"] = cfg.SMTP_FROM
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=10) as smtp:
        if cfg.SMTP_USE_TLS:
            smtp.starttls()
        if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
            smtp.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
        smtp.send_message(message)


def print_email(recipient_email, subject, body):
    """Print a copy of the email to stdout for local demonstrations."""
    print("=" * 60, file=sys.stdout)
    print("EMAIL SERVICE - CONFIRMATION EMAIL", file=sys.stdout)
    print("=" * 60, file=sys.stdout)
    print("To: %s" % recipient_email, file=sys.stdout)
    print("Subject: %s" % subject, file=sys.stdout)
    print("-" * 60, file=sys.stdout)
    print(body, file=sys.stdout)
    print("=" * 60, file=sys.stdout)
    print(file=sys.stdout)


def format_email_body(recipient_name, event_title, ticket_name, order_id):
    """Format the email body for the confirmation email.

    Args:
        recipient_name: Name of the buyer
        event_title: Title of the event
        ticket_name: Name of the ticket type
        order_id: ID of the order

    Returns:
        str: Formatted email body
    """
    body = """Dear %s,

Thank you for your purchase!

Order Details:
- Order ID: %s
- Event: %s
- Ticket Type: %s
- Purchase Date: %s

Your ticket is confirmed. Please present this email confirmation
at the event venue.

Best regards,
The Ticketing Team
""" % (recipient_name, order_id, event_title, ticket_name,
      datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return body


def validate_order_data(data):
    """Validate incoming order data from the API.

    Args:
        data: Dictionary containing order information

    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ["user_email", "user_name", "event_title", "ticket_name", "order_id"]

    for field in required_fields:
        if field not in data or not data[field]:
            return False, "Missing required field: %s" % field

    if "@" not in data["user_email"]:
        return False, "Invalid email address"

    try:
        int(data["order_id"])
    except (ValueError, TypeError):
        return False, "Invalid order_id - must be an integer"

    return True, None
