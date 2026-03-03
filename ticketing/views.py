def entry():
    return {
        "api_name": "ticketing",
        "api_version": "1.0",
        "collections": {
            "users": "/api/users/",
            "events": "/api/events/",
            "orders": "/api/orders/",
        },
    }