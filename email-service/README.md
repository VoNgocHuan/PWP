# Email Auxiliary Service

This is an independent Flask microservice for ticket purchase confirmation emails.
The main Ticketing API calls this service after an order has been created.

## Why This Service Exists

Email delivery is a separate operational concern from selling tickets. SMTP calls can be slow, fail because of network or provider issues, and require credentials or provider configuration. If the main API sent email directly inside the order endpoint, a mail problem could slow down or break ticket purchasing.

Keeping email delivery in a separate service gives the system:

- Failure isolation: ticket purchase can succeed even if email delivery fails.
- Separation of concerns: the main API owns orders, the email service owns notifications.
- Easier provider replacement: MailHog can be used in development and a real SMTP server later.
- Independent demonstration and monitoring through service logs and the fake inbox.

## Architecture

```text
Frontend
  -> POST /api/orders/
      -> Ticketing API
          -> POST /notify/order
              -> Email Service
                  -> SMTP
                      -> MailHog fake inbox
```

## Communication

The main API sends an HTTP request to the email service after creating an order.

```text
POST /notify/order
Content-Type: application/json
```

Example body:

```json
{
  "user_email": "buyer@example.com",
  "user_name": "John Doe",
  "event_title": "Rock Concert",
  "ticket_name": "VIP",
  "order_id": 42
}
```

Success response:

```json
{
  "message": "Email sent successfully",
  "order_id": 42
}
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check and SMTP configuration status |
| POST | `/notify/order` | Send a ticket purchase confirmation email |

## Running With Docker

From the repository root:

```bash
docker-compose up --build
```

Services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Main API | http://localhost:5000/api/ |
| Email service | http://localhost:5001 |
| MailHog inbox | http://localhost:8025 |

The Docker setup configures the email service to send through MailHog:

```text
SMTP_ENABLED=true
SMTP_HOST=mailhog
SMTP_PORT=1025
```

## Manual Development Run

Install dependencies:

```bash
cd email-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run the service:

```bash
python app.py
```

By default, manual mode prints emails to the console. To send through a local fake SMTP server:

```bash
set SMTP_ENABLED=true
set SMTP_HOST=localhost
set SMTP_PORT=1025
python app.py
```

## Manual Test

```bash
curl -X POST http://localhost:5001/notify/order ^
  -H "Content-Type: application/json" ^
  -d "{\"user_email\":\"test@example.com\",\"user_name\":\"Test User\",\"event_title\":\"Test Event\",\"ticket_name\":\"VIP\",\"order_id\":1}"
```

When running with Docker, open MailHog to inspect the delivered email:

```text
http://localhost:8025
```

## Linting

```bash
pylint app.py config.py service.py
```

## Project Structure

```text
email-service/
  app.py            Flask endpoints
  config.py         Environment-based configuration
  service.py        Email formatting and SMTP delivery
  Dockerfile        Container image
  requirements.txt  Python dependencies
  README.md         Service documentation
  .pylintrc         Linting configuration
```
