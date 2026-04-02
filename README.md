# PWP SPRING 2026 - Ticket Sale API
# Group information
* Student 1. Niklas Raesalmi, nraesalm22@student.oulu.fi
* Student 2. Huan Vo, hvo22@student.oulu.fi
* Student 3. Niranjan Sreegith, nsreegit22@student.oulu.fi
* Student 4. MD. Nur-E Ferdaus, mferdaus25@student.oulu.fi

## Tech stack 

- Python 
- Flask
- Flask-RESTful
- Flask-SQLAlchemy
- SQLAlchemy
- jsonschema
- PyJWT (Authentication)
- Redis (Caching)

Testing:
- pytest
- pytest-cov
- pylint
- SQLAlchemy
- Werkzeug

All Python dependencies are encoded in:
- `pyproject.toml`

## Database

Database used: SQLite
Database is auto-created and seeded on server start.

## Features

### Authentication
- JWT-based authentication
- User registration returns auth token automatically
- Login endpoint: `/api/auth/login/`
- Logout endpoint: `/api/auth/logout/` (revokes token)
- Token expiration: 24 hours

### Caching
- Redis-based caching for GET endpoints
- Cache TTL: 5 min (users), 5 min (events list), 2 min (events/tickets)
- Automatic cache invalidation on data changes

### Security
- Protected endpoints require JWT token in Authorization header
- Users can only view/modify their own orders
- Password hashing using Werkzeug security

## Instructions

### Installing deps:
```bash
pip install -r requirements.txt
```

Or install from pyproject.toml:
```bash
pip install pyjwt redis
```

### Running the API:
```bash
flask --app=ticketing --debug run
```

The server will:
1. Auto-create the database on first run
2. Seed it with sample data (2 users, 2 events, 4 tickets)
3. Start on http://127.0.0.1:5000

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/users/` | No | Register user (returns token) |
| GET | `/api/users/` | No | List all users |
| GET | `/api/users/<id>/` | No | Get user details |
| PUT | `/api/users/<id>/` | Yes | Update user |
| DELETE | `/api/users/<id>/` | Yes | Delete user |
| POST | `/api/auth/login/` | No | Login (returns token) |
| POST | `/api/auth/logout/` | Yes | Logout (revoke token) |
| GET | `/api/events/` | No | List all events |
| POST | `/api/events/` | Yes | Create event |
| GET | `/api/events/<id>/` | No | Get event details |
| PUT | `/api/events/<id>/` | Yes | Update event |
| DELETE | `/api/events/<id>/` | Yes | Delete event |
| GET | `/api/events/<id>/tickets/` | No | List tickets for event |
| POST | `/api/events/<id>/tickets/` | Yes | Create ticket |
| GET | `/api/events/<id>/tickets/<id>/` | No | Get ticket details |
| DELETE | `/api/events/<id>/tickets/<id>/` | Yes | Delete ticket |
| GET | `/api/orders/` | Yes | List current user's orders |
| POST | `/api/orders/` | Yes | Create order (buy ticket) |
| GET | `/api/orders/<id>/` | Yes | Get order details (own only) |
| DELETE | `/api/orders/<id>/` | Yes | Delete order (own only) |
| GET | `/api/users/<id>/orders/` | Yes | Get user's orders (own only) |

### Example Usage

```bash
# Register new user (returns token automatically)
curl -X POST http://localhost:5000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "password": "password123"}'

# Login to get token
curl -X POST http://localhost:5000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'

# List events (public)
curl http://localhost:5000/api/events/

# Create event (requires auth)
curl -X POST http://localhost:5000/api/events/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Concert", "venue": "Arena", "city": "Helsinki", "starts_at": "2026-06-01T18:00:00"}'

# Create ticket (requires auth)
curl -X POST http://localhost:5000/api/events/1/tickets/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "VIP", "price": 100.00, "capacity": 50}'

# Buy ticket (requires auth) - only provide ticket_id
curl -X POST http://localhost:5000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"ticket_id": 1}'

# View own orders (requires auth)
curl http://localhost:5000/api/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Logout (requires auth)
curl -X POST http://localhost:5000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### How to run tests

Run tests and coverage:
```bash
pytest --cov=ticketing --cov-report=term-missing --cov-report=html
```

Coverage HTML report will be generated in 'htmlcov/'.

Also linting the code can be done using this command:
```bash
pylint ticketing --disable=no-member,import-outside-toplevel,no-self-use
```

### Redis (Optional)

For caching, Redis is used. If Redis is not available, caching is gracefully disabled.

Default Redis config:
- Host: localhost
- Port: 6379
- DB: 0

To configure Redis, modify the Flask app config:
```python
app.config["REDIS_HOST"] = "your-redis-host"
app.config["REDIS_PORT"] = 6379
app.config["REDIS_DB"] = 0
```

## Frontend (Branch: Frontend)

### Changes Made

| Date | Change | Description |
|------|--------|-------------|
| 2026-04-02 | Login/Logout with JWT | Implemented login form that calls `/api/auth/login/` and stores JWT token in localStorage. Logout calls `/api/auth/logout/` to blacklist the token server-side. |
| 2026-04-02 | JWT Token Storage | JWT token, user_id, and user_name are stored in localStorage using helper functions: `setAuth()`, `getToken()`, `clearAuth()` |
| 2026-04-02 | Using JWT Token | All authenticated requests use `getAuthHeaders()` which includes `Authorization: Bearer {token}` header |
| 2026-04-02 | View My Orders | Users can view their purchased tickets via "My Tickets" navigation which calls `/api/users/{user_id}/orders/` |
| 2026-04-02 | Token Uniqueness Fix | Added timestamp (`iat`) to JWT payload in backend to ensure each login generates a unique token. This fixes the bug where re-login after logout would fail because the same token was being blacklisted and reissued. |

### Frontend Files

- `frontend/index.html` - Main HTML with login form, events list, and my tickets view
- `frontend/app.js` - JavaScript handling API calls, authentication, and UI updates

### Frontend Features

- Login/Logout with JWT authentication
- View all available events
- Purchase tickets (requires login)
- View purchased tickets ("My Tickets")
- Token is automatically included in all authenticated API calls
- Logout blacklists token on server-side
