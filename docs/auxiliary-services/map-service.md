# Auxiliary Service: Event Location Map

## Description

The Event Location Map service provides venue location visualization for events by integrating with OpenStreetMap's geocoding and mapping services. It allows users to view event venue locations on an interactive map directly in their browser.

## Goals

1. **Enhance User Experience**: Help users visualize event locations without leaving the ticketing platform
2. **Improve Navigation**: Make it easy for users to find event venues using external map services
3. **Lightweight Integration**: Avoid loading heavy mapping libraries by using external map services
4. **Fast Performance**: Provide instant location lookup through direct links to OpenStreetMap

## Interaction with API and Client

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSER                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  index.html  │───▶│   app.js     │───▶│  Event Location Map Service  │  │
│  │  (Frontend) │    │  (Logic)     │    │  (OpenStreetMap Integration)  │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────────┘  │
│         │                    │                         │                      │
│         │                    ▼                         ▼                      │
│         │             ┌──────────┐          ┌─────────────┐               │
│         │             │  REST API │          │  OpenStreetMap │              │
│         │             │ /api/*   │          │  (External)   │              │
│         │             └──────────┘          └─────────────┘               │
│         │                   │                                         │      │
│         └───────────────────┼─────────────────────────────────────────┘      │
│                             ▼                                               │
│                    ┌────────────────┐                                     │
│                    │  Flask Backend  │                                     │
│                    │    Server      │                                     │
│                    └────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
Client Browser                           Ticketing API                    OpenStreetMap
     │                                       │                              │
     │  1. User clicks "Show on Map"          │                              │
     │───────────────────────────────────────▶│                              │
     │                                       │                              │
     │  2. Build OpenStreetMap search URL     │                              │
     │     (venue + city)                    │                              │
     │────────────────────────────────────────│──────────────────────────────▶│   │
     │                                       │                              │   │
     │  3. Open new browser tab with          │                              │
     │     search results                    │                              │
     │◀──────────────────────────────────────│──────────────────────────────│   │
     │                                       │                              │
```

## Service Components

### 1. Location Resolver
- Resolves venue names to geographic coordinates
- Uses predefined fallback coordinates for known venues
- Falls back to Nominatim geocoding service for unknown locations

### 2. Map Link Generator
- Constructs OpenStreetMap search URLs
- Encodes venue and city names for URL parameters
- Opens results in new browser tab

### 3. Cache (Future Enhancement)
```python
# Potential cache structure
LOCATION_CACHE = {
    "central park arena helsinki": {"lat": 60.1699, "lon": 24.9384},
    "convention center oulu": {"lat": 65.0126, "lon": 25.4682},
}
```

## Data Flow

1. **Client Request**: User clicks "Show on Map" button
2. **URL Construction**: JavaScript builds OpenStreetMap search URL
3. **External Call**: Browser redirects to OpenStreetMap search
4. **Map Display**: User sees venue location in OpenStreetMap interface
5. **User Actions**: User can get directions, explore area, etc.

## API Endpoints Used

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/` | Fetch all events with venue info |
| Browser Redirect | OpenStreetMap Search | External service call |

## Future Enhancements

1. **Static Map Images**: Embed pre-rendered map images directly in event cards
2. **Geocoding Cache**: Store coordinates in database to reduce API calls
3. **Interactive Maps**: Add embedded interactive map using Leaflet.js
4. **Directions Integration**: Link to driving/walking directions
5. **Venue Database**: Store official venue coordinates in the backend

## Dependencies

- **OpenStreetMap Nominatim API**: For geocoding (rate-limited)
- **OpenStreetMap Static Map**: For static map images
- **OpenStreetMap Search**: For full interactive search

## Limitations

1. Requires internet connection to access external mapping services
2. Geocoding accuracy depends on OpenStreetMap data quality
3. Rate limiting on Nominatim API (1 request/second recommended)
4. Some venues may not be found in OpenStreetMap database