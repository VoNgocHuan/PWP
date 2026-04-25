# Ticketing System - Frontend Client

A web-based frontend client for the Ticketing REST API. Allows users to browse events, purchase tickets, and view their purchased tickets.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Client](#running-the-client)
- [Configuration](#configuration)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [API Endpoints Used](#api-endpoints-used)

## Overview

The Ticketing Client is a static HTML/JavaScript web application that:
- Provides a visual interface for browsing events
- Allows users to purchase tickets
- Shows user's purchased tickets
- Handles authentication via JWT tokens

## Features

| Feature | Description |
|--------|-------------|
| User Login | Authenticate with email and password |
| Browse Events | View all available events with ticket options |
| Purchase Tickets | Buy tickets for events |
| View My Tickets | See all purchased tickets |
| Error Handling | Clear error messages for failed operations |

## Prerequisites

- Modern web browser (Chrome, Firefox, Edge, Safari)
- Backend API running (see main README for backend setup)
- nginx for serving static files (via Docker)

## Installation

### Option 1: Using Docker (Recommended)

```bash
# From project root
docker-compose up -d
```

The frontend will be available at http://localhost:8080

### Option 2: Manual Setup

1. **Serve with any HTTP server:**

   Using Python:
   ```bash
   cd frontend
   python -m http.server 8080
   ```

   Using nginx:
   ```bash
   nginx -g 'daemon off;' -c /path/to/nginx.conf
   ```

   Using npx (Node.js):
   ```bash
   npx serve -p 8080
   ```

2. **Access the client:**
   Open http://localhost:8080 in your browser

## Running the Client

### With Docker

```bash
docker-compose up -d
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8080/api/

### Without Docker

1. Start the backend (see backend/README.md)
2. Start the frontend HTTP server
3. Open browser at http://localhost:8080

### Demo Credentials

The system is seeded with test users:

| Email | Password |
|-------|----------|
| alice@example.com | password123 |
| bob@example.com | password123 |

## Configuration

The client connects to the API at `/api/` (proxied via nginx to backend).

To change the API base URL, edit `app.js`:

```javascript
const API_BASE = "/api";  // Change this if needed
```

### Local Storage Keys

The client uses these localStorage keys:

| Key | Description |
|-----|-------------|
| `auth_token` | JWT authentication token |
| `user_id` | Current user ID |
| `user_name` | Current user email |

## Testing

### Manual Testing Checklist

- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Browse events list
- [ ] Purchase a ticket
- [ ] View my tickets
- [ ] Logout
- [ ] Handle sold-out tickets
- [ ] Handle network errors

### API Testing

```bash
# Test login
curl -X POST http://localhost:5000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'

# Test events
curl http://localhost:5000/api/events/
```

## Code Quality

### JavaScript Linting

The project uses ESLint for JavaScript code quality.

```bash
# Install ESLint
npm install -g eslint

# Run linting
cd frontend
eslint app.js
```

Configuration is in `.eslintrc.json`


## API Endpoints Used

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login/` | No | Login, get JWT token |
| POST | `/api/auth/logout/` | Yes | Logout, revoke token |
| GET | `/api/events/` | No | List all events with tickets |
| POST | `/api/orders/` | Yes | Purchase a ticket |
| GET | `/api/users/<id>/orders/` | Yes | Get user's orders |
