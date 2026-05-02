================================================================================
                     SCREEN WORKFLOW DIAGRAM
                    Ticketing Client Application
================================================================================

This diagram shows the transitions between different screens in the client
application.

================================================================================
                         APPLICATION FLOW
================================================================================

 START
   │
   ▼
┌─────────────────────────────┐
│     LOAD PAGE           │
│  (index.html loads)     │
│                      │
│  ┌─────────────────┐ │
│  │ Check local      │ │
│  │ Storage for      │ │
│  │ auth token      │ │
│  └────────┬────────┘ │
└───────────┼───────────┘
            │
            ├──[token exists]──▶ Show Main Screen
            │                       │
            │                       ▼
            │              ┌─────────────────────────────┐
            │              │      MAIN SCREEN             │
            │              │  ┌─────────────────────────┐  │
            │              │  │  Active Tab: Events  │  │
            │              │  │  or My Tickets     │  │
            │              │  └─────────────────────────┘  │
            │              │            │                    │
            │              │   ┌────────┴────────┐          │
            │              │   │                 │          │
            │              │   ▼                 ▼          │
            │              │Events Tab     MyTickets Tab    │
            │              │   │                 │          │
            │              │   ▼                 │          │
            │              │Load events         Load orders   │
            │              │  │                 │          │
            │              │  ▼                 │          │
            │              │ ├─ [Buy clicked]  │          │
            │              │ │       ▼         │          │
            │              │ │ POST /orders/  │          │
            │              │ │       │         │          │
            │              │ │  [Success]     │          │
            │              │ │       │         │          │
            │              │ │       ▼         │          │
            │              │ │ Reload events ──┘          │
            │              │ │       │                  │
            │              │ │       ▼                  │
            │              │ │ Show message             │
            │              │ │ (success/error)          │
            │              │ │       │                  │
            ▼                 ▼                  ▼
         [no token]                                     │
            │                                           │
            ▼                                           │
┌─────────────────────────────┐                         │
│     LOGIN SCREEN            │◄────────────────────────┘
│                             │      (Logout clicked)
│  ┌───────────────────────┐ │
│  │ Email Input           │ │
│  │ Password Input        │ │
│  │ Login Button         │ │
│  └───────────────────────┘ │
│            │                                        
│            ▼ (Login clicked)                      
│            │                                       
│  ┌─────────────────────────┐                       
│  │ POST /api/auth/login/  │                       
│  │                       │                       
│  │ {email, password}     │                       
│  └──────────┬────────────┘                       
│             │                                     
│    ┌────────┴─────────┐                          
│    │                  │                          
│  [Success]          [Error]                     
│    │                  │                          
│    ▼                  ▼                          
│ Store token      Show error message              
│ Store user_id   Return to login form            
│ Store user_name                            
│    │                                      
│    ▼                                      
└──────────────────────────────────────────────────┘
             │
             ▼
    [Return to Login]
             │
             ▼
         START (loop)
         

================================================================================
                    INTER-SCREEN TRANSITIONS
================================================================================

Login Screen
    │
    ├─[Login success]──▶ Main Screen (Events tab)
    │                           │
    │                           ├─[Click Events]───▶ Main Screen (Events tab)
    │                           │
    │                           ├─[Click My Tickets]──▶ Main Screen (My Tickets tab)
    │                           │
    │                           ├─[Click Buy]───▶ Purchase flow
    │                           │                     │
    │                           │                     ▼
    │                           │              ┌──────────────┐
    │                           │              │ POST order  │
    │                           │              │            │
    │                           │              └──────┬───────┘
    │                           │                     │
    │                           │          ┌────────┴────────┐
    │                           │          │                 │
    │                           │    [Success]      [Error]
    │                           │          │                 │
    │                           │          ▼                 ▼
    │                           │    Reload events   Show error
    │                           │          │                 │
    │                           └──────────┴─────────────────┘
    │                                        │
    │                                        ▼
    │                              Main Screen (refreshed)
    ��                                        │
    └─[Click Logout]─────────────────────────┘
                         │
                         ▼
                   Login Screen


================================================================================
                      NAVIGATION SUMMARY
================================================================================

┌─────────────────────────────────────┐
│         NAVIGATION FLOW              │
├─────────────────────────────────────┤
│                                     │
│  [Events Tab] ───────┐               │
│       ▲             │               │
│       │             │               │
│       │         [Events Tab]        │
│       │             │               │
│       │             ▼               │
│       │    [My Tickets Tab]        │
│       │             │               │
│       │             ▼               │
│       │    [My Tickets Tab]        │
│       │             │               │
│       │             │               │
│       └─────────────┘               │
│                                     │
│  [My Tickets Tab] ──┐               │
│       ▲            │               │
│       │            │               │
│       │        [My Tickets Tab]    │
│       │            │               │
│       │            ▼               │
│       │    [Events Tab]           │
│       │            │               │
│       │            ▼               │
│       │    [Events Tab]           │
│       │            │               │
│       │            │               │
│       └────────────┘                │
│                                     │
│  [Logout] ────────▶ [Login Screen]  │
│                                     │
└─────────────────────────────────────┘


================================================================================
                         ERROR FLOW
================================================================================

Any Screen
        │
        ▼
┌──────────────────┐
│  API Call fails  │
│  (fetch error)   │
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│  Show error msg   │ (Error message on screen)
│  (5 second wait)  │
└────────┬──────────┘
         │
         ▼
┌──────────────────┐
│  Clear message   │
│  Return to state │
└──────────────────┘