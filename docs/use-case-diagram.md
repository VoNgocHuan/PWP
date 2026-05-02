# Use Case Diagram

## Mermaid Version (renders as diagram)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#007bff', 'edgeLabelBackground':'#ffffff'}}}%%
useCaseDiagram
    actor "User" as user
    
    usecase "UC1: Login" as login
    usecase "UC2: Browse Events" as browse
    usecase "UC3: View Tickets" as viewTickets
    usecase "UC4: Purchase Ticket" as purchase
    usecase "UC5: View My Tickets" as myTickets
    usecase "UC6: Logout" as logout
    
    user --> login
    user --> browse
    user --> viewTickets
    user --> purchase
    user --> myTickets
    user --> logout
    
    login ..> browse : extends
    
    browse ..> purchase : includes
    purchase ..> myTickets : includes
```

## Text-Based Version

```
                    ┌──────────────────┐
                    │      USER        │
                    │  (Actor)        │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│   Login         │ │   Browse       │ │   Logout       │
│ - Enter email  │ │   Events      │ │ - Clear token  │
│ - Enter pass   │ │ - View list   │ │ - Return to    │
│ - Get JWT      │ │ - See details │ │   login        │
└────────────────┘ └────────────────┘ └────────────────┘
         │                   │
         ▼                   ▼
┌────────────────┐ ┌────────────────┐
│   View Tickets  │ │   Purchase     │
│ - See ticket   │ │   Ticket       │
│   options      │ │ - Select      │
│ - See prices   │ │   ticket       │
│ - See avail   │ │ - Create order │
└────────────────┘ └────────────────┘
         │
         ▼
┌────────────────┐
│   View My       │
│   Tickets       │
│ - Order list   │
│ - Status       │
└────────────────┘
```

## Use Cases Summary

| Use Case | Description | API Endpoint |
|----------|-------------|---------------|
| UC1: Login | User authenticates with email and password | POST /api/auth/login/ |
| UC2: Browse Events | User views list of events with tickets | GET /api/events/ |
| UC3: View Tickets | User sees ticket types, prices, availability | GET /api/events/<id>/tickets/ |
| UC4: Purchase Ticket | User buys a ticket | POST /api/orders/ |
| UC5: View My Tickets | User views purchased tickets | GET /api/users/<id>/orders/ |
| UC6: Logout | User ends session | POST /api/auth/logout/ |

## Actor-System Interactions

```
User Login
    │
    ├─▶ POST /api/auth/login/
    │       │
    │       ▼
    │   JWT Token
    │       │
    │       ▼
    └─▶ Access Main Screen
            │
            │
    ┌───────┴───────┐
    ▼               ▼
Browse Events  My Tickets
    │               │
    ▼               ▼
GET /events/    GET /users/{id}/orders/
    ���               │
    ▼               ▼
Display list   Display orders
    │               │
    ▼               ▼
[Buy] button    View details
    │               │
    ▼               ▼
POST /orders/  -----
    │
    ▼
Success/Fail message
```