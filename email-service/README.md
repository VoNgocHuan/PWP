# Email Auxiliary Service

An independent microservice that sends email confirmations when tickets are purchased through the main ticketing API.

## Overview

The Email Auxiliary Service is a separate microservice designed to handle email notifications for the ticketing system. It listens for order notifications from the main API and sends confirmation emails to buyers when they purchase tickets.

### Why This Service is Necessary

Sending emails directly from the main API would be problematic for several reasons:

1. **Blocking I/O**: SMTP operations are slow and unreliable - they require network connections to external mail servers and can take several seconds to complete. This would block API responses and degrade user experience.

2. **Failure Isolation**: If the email server (e.g., Gmail SMTP) is down or experiencing issues, it should not affect the main API's ability to process ticket purchases.

3. **Separation of Concerns**: Email credentials and delivery logic should be separate from the core ticketing business logic. The main API handles ordering; this service handles notifications.

4. **Reliability and Retry**: The email service can implement retry logic for failed deliveries independently, without requiring changes to the main API.

5. **Scalability**: Email delivery can be scaled independently from the main API based on traffic patterns.

## Architecture

```
┌─────────────────┐         HTTP POST          ┌─────────────────┐
│   Main API       │ ───────────────────────▶│  Email Service  │
│  (port 5000)    │    /notify/order       │ (port 5001)    │
└─────────────────┘                           └─────────────────┘
                                                      │
                                                      ▼
                                                ┌───────────┐
                                                │ Console   │
                                                │ Print    │
                                                └───────────┘
```

### Communication Protocol

The main API sends a POST request to the email service when an order is created:

- **Endpoint**: `http://localhost:5001/notify/order`
- **Method**: POST
- **Content-Type**: application/json

**Request Body**:
```json
{
    "user_email": "buyer@example.com",
    "user_name": "John Doe",
    "event_title": "Rock Concert",
    "ticket_name": "VIP",
    "order_id": 42
}
```

**Success Response** (200):
```json
{
    "message": "Email sent successfully",
    "order_id": 42
}
```

**Error Responses**:
- 400: Validation error (missing or invalid fields)
- 415: Unsupported media type (not JSON)
- 500: Internal server error

## Installation

### Prerequisites

- Python 3.8 or higher

### Steps

1. Navigate to the email-service directory:
   ```bash
   cd email-service
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The service can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_HOST` | `0.0.0.0` | Host to bind to |
| `SERVICE_PORT` | `5001` | Port to listen on |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SMTP_ENABLED` | `false` | Enable real SMTP sending |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server host |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | (empty) | SMTP username |
| `SMTP_PASSWORD` | (empty) | SMTP password |
| `SMTP_FROM` | `noreply@ticketing.com` | From email address |

## Running the Service

### Development Mode

```bash
python app.py
```

The service will start on `http://localhost:5001`.

### With Custom Port

```bash
set SERVICE_PORT=5002
python app.py
```

Or on Linux/Mac:
```bash
SERVICE_PORT=5002 python app.py
```

### Verify Service is Running

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{"status": "healthy", "service": "email-service"}
```

## Connecting to the Main API

To enable the main API to notify the email service when tickets are purchased:

1. Set the environment variable before running the main API:
   ```bash
   set EMAIL_SERVICE_URL=http://localhost:5001
   ```

2. Start the main API:
   ```bash
   cd backend
   flask --app=ticketing --debug run
   ```

The main API will now send a POST request to the email service whenever an order is created.

## Testing

### Manual Test

Send a test notification using curl:

```bash
curl -X POST http://localhost:5001/notify/order ^
  -H "Content-Type: application/json" ^
  -d "{\"user_email\": \"test@example.com\", \"user_name\": \"Test User\", \"event_title\": \"Test Event\", \"ticket_name\": \"VIP\", \"order_id\": 1}"
```

You should see the confirmation email printed to the console.

### Health Check

```bash
curl http://localhost:5001/health
```

## Linting

Run pylint to check code quality:

```bash
pylint service.py config.py app.py
```

Expected output should show no errors (score ~9.0+).

## Project Structure

```
email-service/
├── app.py          # Flask application and endpoints
├── config.py       # Service configuration
├── service.py     # Email sending logic
├── requirements.txt
├── README.md      # This file
└── .pylintrc    # Pylint configuration
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/notify/order` | POST | Handle order notification |

## Troubleshooting

### Connection Refused

If the main API cannot connect to the email service:
1. Check the email service is running (`curl http://localhost:5001/health`)
2. Verify `EMAIL_SERVICE_URL` is set correctly
3. Check firewall settings are not blocking the port

### Service Not Starting

1. Check port 5001 is not in use: `netstat -ano | findstr 5001`
2. Try a different port: `set SERVICE_PORT=5002`

## License

This project is part of the PWP Spring 2026 Ticketing System.