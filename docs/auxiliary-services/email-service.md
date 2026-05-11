# Auxiliary Service: Ticket Confirmation Email Service

## Idea

The auxiliary service sends confirmation emails after ticket purchases. The main Ticketing API creates the order and then sends an HTTP notification to the email service. The email service formats and sends the email through SMTP.

In development, SMTP is handled by MailHog, a fake SMTP server with a browser inbox.

## Why This Should Be Separate

Sending email directly from the main API would be problematic because SMTP delivery is slow and can fail independently from ticket purchasing. A temporary email provider failure should not prevent an order from being created. Email credentials and provider-specific delivery logic also do not belong in the core ticketing API.

This service isolates email delivery from the order workflow while still showing real service-to-service communication.

## Overview

```text
Client
  -> Ticketing API
      -> PostgreSQL stores the order
      -> Email Service receives order notification
          -> MailHog receives the email through SMTP
```

## Communication Diagram

```text
+----------+      HTTP       +--------------+      HTTP       +---------------+
| Frontend | --------------> | Ticketing API | -------------> | Email Service |
+----------+                 +--------------+                 +---------------+
                                   |                                  |
                                   | SQL                              | SMTP
                                   v                                  v
                            +-------------+                    +-------------+
                            | PostgreSQL  |                    | MailHog     |
                            +-------------+                    +-------------+
```

## Service API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Confirms the service is running and shows SMTP configuration |
| POST | `/notify/order` | Receives order data and sends a confirmation email |

## Order Notification Payload

```json
{
  "user_email": "alice@example.com",
  "user_name": "Alice Wonderland",
  "event_title": "Summer Concert",
  "ticket_name": "VIP",
  "order_id": 1
}
```

## Demo Steps

1. Start the full system:

```bash
docker-compose up --build
```

2. Open the frontend:

```text
http://localhost:8080
```

3. Log in with a seeded user:

```text
alice@example.com
password123
```

4. Buy a ticket.

5. Open MailHog:

```text
http://localhost:8025
```

6. Confirm that the ticket purchase email appears in the inbox.

## Runtime Configuration

The backend uses:

```text
EMAIL_SERVICE_URL=http://email-service:5001
```

The email service uses:

```text
SMTP_ENABLED=true
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM=noreply@ticketing.com
```
