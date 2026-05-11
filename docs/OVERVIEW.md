# Ticketing System Client - Overview

## 1. Client Description

### Overview

The **Ticketing System Client** is a web-based frontend application that allows users to interact with the Ticketing REST API. It provides an intuitive graphical interface for browsing events, purchasing tickets, and managing bought tickets.

### Why This Client?

Users benefit from this client because:

- **No technical knowledge required**: Unlike curl commands or Postman, users can simply log in and click to buy tickets
- **Visual feedback**: Users see events, ticket availability, and prices in a clear layout
- **Real-time updates**: Ticket availability updates immediately after purchase
- **Accessible**: Works in any modern web browser without installation

### Target Users

- Event attendees who want to purchase tickets for concerts, events, or shows
- Users who prefer visual interfaces over command-line tools

---

## 2. API Resources and Methods

The client uses the following API endpoints:

| Resource | Method | Endpoint | Auth | Description |
|----------|--------|---------|------|-------------|
| **Auth** | POST | `/api/auth/login/` | No | User login, returns JWT token |
| **Auth** | POST | `/api/auth/logout/` | Yes | User logout, revokes token |
| **Events** | GET | `/api/events/` | No | List all available events with tickets |
| **Events** | GET | `/api/events/<id>/` | No | Get event details |
| **Orders** | POST | `/api/orders/` | Yes | Purchase a ticket |
| **Orders** | GET | `/api/users/<id>/orders/` | Yes | Get current user's orders |

---

## 3. Use Case Diagram

```
┌─────────────────┐     ┌─────────────────┐
│    User Actor   │     │  System Actor   │
└────────┬────────┘     └────────┬────────┘
         │                      │
         │  ┌──────────────────┴──────────────────┐
         │  │                                        │
         ▼  ▼                                        ▼
┌─────────────────────┐                 ┌─────────────────────┐
│   UC1: Login        │                 │  UC2: Logout        │
│ - Log in with       │                 │  - Clear session    │
│   email/password   │                 │  - Return to      │
└─────────────────────┘                 │    login screen   │
                                     └─────────────────────┘
         │
         │  ┌──────────────────┐    ┌──────────────────┐
         │  │ UC3: Browse       │    │ UC4: View       │
         │  │   Events         │    │   My Tickets    │
         │  │ - List events    │    │ - View bought   │
         │  │ - View tickets  │    │   tickets       │
         │  │ - See prices   │    │ - View order    │
         │  │   and avail    │    │   status       │
         │  └──────────────────┘    └──────────────────┘
         │
         │  ┌──────────────────────────────────────┐
         │  │ UC5: Purchase Ticket               │
         │  │ - Select ticket to buy             │
         │  │ - Create order via API            │
         │  │ - Update ticket availability    │
         │  └──────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│ UC6: Error Handling│
│ - Show API errors │
│ - Validate input │
│ - Inform user   │
└─────────────────────┘
```

---

## 4. GUI Layout

### Screen 1: Login Screen (Default)

```
┌──────────────────────────────────────────────────────────┐
│  [Logo]              Ticketing System                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                    LOGIN                                 │
│              ┌─────────────────┐                         │
│              │ Email:          │ [____________]                  │
│              │ Password:      │ [____________]                  │
│              │                │                         │
│              │    [Login]    │                         │
│              └─────────────────┘                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Screen 2: Main Screen (After Login)

```
┌──────────────────────────────────────────────────────────┐
│  [Logo]    Ticketing System      [Events] [My Tickets]  │
│                                          User: john@mail  │
│                                          [Logout]        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  AVAILABLE EVENTS                                  │ │
│  ├────────────────────────────────────────────────────┤ │
│  │                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ Concert A   │  │ Concert B   │                │ │
│  │  │ Date: ...   │  │ Date: ...   │                │ │
│  │  │ Venue: ...  │  │ Venue: ...  │                │ │
│  │  │             │  │             │                │ │
│  │  │ [Ticket 1] │  │ [Ticket 1] │                │ │
│  │  │ VIP €100   │  │ Standard €50│                │ │
│  │  │ [Buy]      │  │ [Buy]      │                │ │
│  │  └──────────────┘  └──────────────┘                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Screen Workflow

```
┌─────────────┐
│  START     │
│  (Login)   │
└─────┬──────┘
      │
      ▼
┌─────────────┐
│ Login Form  │◄─────────────────────────────────┐
│ (email,     │                                  │
│ password)  │                                   │
└─────┬──────┘                                   │
      │ (valid)                                  │
      ▼                                          │
┌─────────────┐      ┌──────────────────────┐   │
│ Main Screen │─────▶│ [Events] Tab Selected │   │
│ (tab:       │      └──────────────────────┘   │
│  Events)   │               │                    │
└─────┬──────┘               ▼                    │
      │              ┌──────────────────────┐   │
      │              │ [My Tickets] Tab      │   │
      │              │ Selected             │   │
      │              └──────────────────────┘   │
      │                      │                    │
      │                      ▼                    │
      │              ┌──────────────────────┐   │
      │              │ View My Tickets      │   │
      │              │ Screen             │   │
      │              └──────────────────┬───┘   │
      │                                 │       │
      │ (click Buy)                      │       │
      │                                 │       │
      │                                 ▼       │
      │              ┌──────────────────────┐   │
      │              │ Purchase Flow         │   │
      │              │ 1. POST /orders/     │──┼──┘
      │              │ 2. Show success      │   │
      │              │ 3. Reload tickets   │   │
      │              └──────────────────────┘   │
      │                      │                    │
      │                      ▼ (Logout)         │
      │              ┌──────────────────────┐   │
      └────────────▶│ Clear Session       │───┘
                  │ Return to Login    │
                  └──────────────────────┘
```

---

## 6. Client Features Summary

| Feature | Description | API Endpoint |
|--------|-------------|--------------|
| User Login | Authenticate with email/password | POST /api/auth/login/ |
| User Logout | End session | POST /api/auth/logout/ |
| Browse Events | View all events with available tickets | GET /api/events/ |
| Purchase Ticket | Buy a ticket for an event | POST /api/orders/ |
| View My Tickets | See all purchased tickets | GET /api/users/{id}/orders/ |

---

## 7. Error Handling

The client handles errors in the following ways:

- **Invalid login**: Shows "Invalid email or password" message
- **Network error**: Shows "Error loading events" with technical details
- **Purchase failed**: Shows API error message (e.g., "Ticket sold out")
- **Session expired**: Clears auth and shows login form

---

## 8. Dependencies

The client has no external dependencies for the browser. It uses:

- Vanilla JavaScript (ES6+)
- HTML5 and CSS3
- No framework required

For development:

- ESLint for code linting (optional)