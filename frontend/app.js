/**
 * Ticketing System Client Application
 * 
 * A web-based frontend for the Ticketing REST API that allows users to:
 * - Login/logout with email and password
 * - Browse available events and tickets
 * - Purchase tickets for events
 * - View their purchased tickets
 * 
 * @module ticketing-client
 * @version 1.0.0
 */

/**
 * API base URL for backend requests.
 * @constant {string}
 */
const API_BASE = "/api";

/**
 * Local storage key for authentication token.
 * @constant {string}
 */
const AUTH_TOKEN_KEY = "auth_token";

/**
 * Local storage key for user ID.
 * @constant {string}
 */
const USER_ID_KEY = "user_id";

/**
 * Local storage key for user name (email).
 * @constant {string}
 */
const USER_NAME_KEY = "user_name";

/**
 * Set of event IDs that have been viewed by the user.
 * Used to track view activity for analytics.
 * @type {Set<number>}
 */
const viewedThisSet = new Set();

/**
 * All events loaded from API (cached for search).
 * @type {Array}
 */
let allEvents = [];

/**
 * Filters events by search term.
 * 
 * @param {string} searchTerm - Text to filter by
 * @returns {Array} Filtered events
 */
function filterEvents(searchTerm) {
    if (!searchTerm) return allEvents;
    
    const term = searchTerm.toLowerCase();
    return allEvents.filter(event => {
        return event.title.toLowerCase().includes(term) ||
               event.venue.toLowerCase().includes(term) ||
               event.city.toLowerCase().includes(term);
    });
}

/**
 * Renders events to the DOM.
 * 
 * @param {Array} events - Events to render
 */
function renderEvents(events) {
    const container = document.getElementById("events");
    container.innerHTML = "";

    if (!Array.isArray(events) || events.length === 0) {
        container.innerHTML = "<p>No events found.</p>";
        return;
    }

    events.forEach(event => {
        const div = document.createElement("div");
        div.className = "event";

        let ticketBoxes = "";

        if (event.tickets && event.tickets.length > 0) {
            event.tickets.forEach(ticket => {
                const isSoldOut = ticket.remaining <= 0;
                ticketBoxes += `
                    <div class="ticket-box">
                        <strong>${ticket.name}</strong><br>
                        Price: €${ticket.price}<br>
                        Remaining: ${ticket.remaining}<br>
                        <button class="buy-btn" 
                                data-ticket-id="${ticket.id}"
                                ${isSoldOut ? "disabled" : ""}>
                            ${isSoldOut ? "Sold Out" : "Buy"}
                        </button>
                    </div>
                `;
            });
        } else {
            ticketBoxes = "<div>No tickets available</div>";
        }

        div.innerHTML = `
            <div class="event-title">${event.title}</div>
            <div class="event-info">
                Date: ${new Date(event.starts_at).toLocaleString()}<br>
                Venue: ${event.venue}, ${event.city}
            </div>
            <a class="event-map-btn" href="https://www.openstreetmap.org/search?query=${encodeURIComponent(event.venue + ' ' + event.city)}" target="_blank">
                Show on Map
            </a>
            <div class="ticket-container">
                ${ticketBoxes}
            </div>
        `;

        const titleEl = div.querySelector(".event-title");
        if (titleEl) {
            titleEl.style.cursor = "pointer";
            titleEl.title = "Click to log view";
            titleEl.addEventListener("click", async () => {
                const userId = getUserId();
                if (!userId || viewedThisSet.has(event.id)) return;
                viewedThisSet.add(event.id);
                await logActivity(userId, event.id, "view", { source: "ui_event_title_click" });
            });
        }

        container.appendChild(div);
    });

    attachPurchaseHandlers();
}

/**
 * Retrieves the authentication token from local storage.
 * 
 * @returns {string|null} The JWT token if stored, null otherwise
 */
function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Retrieves the user ID from local storage.
 * 
 * @returns {string|null} The user ID if stored, null otherwise
 */
function getUserId() {
    return localStorage.getItem(USER_ID_KEY);
}

/**
 * Retrieves the user name (email) from local storage.
 * 
 * @returns {string|null} The user name if stored, null otherwise
 */
function getUserName() {
    return localStorage.getItem(USER_NAME_KEY);
}

/**
 * Stores authentication data in local storage.
 * 
 * @param {string} token - JWT authentication token
 * @param {string} userId - User's unique identifier
 * @param {string} userName - User's email address
 */
function setAuth(token, userId, userName) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(USER_ID_KEY, userId);
    localStorage.setItem(USER_NAME_KEY, userName);
}

/**
 * Clears all authentication data from local storage.
 * Called on logout or when session is invalidated.
 */
function clearAuth() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem(USER_NAME_KEY);
}

/**
 * Checks if user is currently logged in.
 * 
 * @returns {boolean} True if authenticated, false otherwise
 */
function isLoggedIn() {
    return !!getToken();
}

/**
 * Generates authentication headers for API requests.
 * 
 * @returns {Object} Headers object with Authorization token and Content-Type
 */
function getAuthHeaders() {
    const token = getToken();
    if (!token) return {};
    return {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };
}

/**
 * Validates an email address format.
 * 
 * @param {string} email - Email address to validate
 * @returns {boolean} True if valid, false otherwise
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validates password meets minimum requirements.
 * 
 * @param {string} password - Password to validate
 * @returns {boolean} True if valid (non-empty), false otherwise
 */
function isValidPassword(password) {
    return password && password.length > 0;
}

/**
 * Logs user activity to the backend for analytics tracking.
 * 
 * @param {string} userId - User's unique identifier
 * @param {number|string} eventId - Event ID that was viewed
 * @param {string} action - Type of action (e.g., "view")
 * @param {Object} [meta=null] - Additional metadata about the action
 * @returns {Promise<void>}
 */
async function logActivity(userId, eventId, action, meta = null) {
    try {
        await fetch(`${API_BASE}/activity`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                event_id: eventId,
                action: action,
                meta: meta
            })
        });
    } catch (e) {
        console.warn("Activity logging failed:", e);
    }
}

/**
 * Shows the loading spinner for events section.
 */
function showEventsLoading() {
    document.getElementById("loading-events").classList.add("active");
    document.getElementById("events").innerHTML = "";
}

/**
 * Hides the loading spinner for events section.
 */
function hideEventsLoading() {
    document.getElementById("loading-events").classList.remove("active");
}

/**
 * Shows the loading spinner for tickets section.
 */
function showTicketsLoading() {
    document.getElementById("loading-tickets").classList.add("active");
    document.getElementById("my-tickets").innerHTML = "";
}

/**
 * Hides the loading spinner for tickets section.
 */
function hideTicketsLoading() {
    document.getElementById("loading-tickets").classList.remove("active");
}

/**
 * Loads all events from the API and renders them on the page.
 * Handles both successful loading and error states.
 * 
 * @returns {Promise<void>}
 */
async function loadEvents() {
    showEventsLoading();
    
    let events;
    try {
        const response = await fetch(`${API_BASE}/events/`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        events = data.items || [];
    } catch (e) {
        console.error("Failed to load events:", e);
        hideEventsLoading();
        document.getElementById("events").innerHTML = `<p class="error-message">Error loading events: ${e.message}</p>`;
        return;
    }

    hideEventsLoading();
    
    // Store all events for search
    allEvents = events;
    
    // Apply current search filter if any
    const searchTerm = document.getElementById("event-search")?.value || "";
    const filteredEvents = filterEvents(searchTerm);
    
    const container = document.getElementById("events");
    container.innerHTML = "";

    if (!Array.isArray(filteredEvents) || filteredEvents.length === 0) {
        container.innerHTML = "<p>No events found.</p>";
        return;
    }

    filteredEvents.forEach(event => {
        const div = document.createElement("div");
        div.className = "event";
        
        let ticketBoxes = "";

        if (event.tickets && event.tickets.length > 0) {
            event.tickets.forEach(ticket => {
                const isSoldOut = ticket.remaining <= 0;
                ticketBoxes += `
                    <div class="ticket-box">
                        <strong>${ticket.name}</strong><br>
                        Price: €${ticket.price}<br>
                        Remaining: ${ticket.remaining}<br>
                        <button class="buy-btn" 
                                data-ticket-id="${ticket.id}"
                                ${isSoldOut ? "disabled" : ""}>
                            ${isSoldOut ? "Sold Out" : "Buy"}
                        </button>
                    </div>
                `;
            });
        } else {
            ticketBoxes = "<div>No tickets available</div>";
        }

        div.innerHTML = `
            <div class="event-title">${event.title}</div>
            <div class="event-info">
                Date: ${new Date(event.starts_at).toLocaleString()}<br>
                Venue: ${event.venue}, ${event.city}
            </div>
            <a class="event-map-btn" href="https://www.openstreetmap.org/search?query=${encodeURIComponent(event.venue + ' ' + event.city)}" target="_blank">
                Show on Map
            </a>
            <div class="ticket-container">
                ${ticketBoxes}
            </div>
        `;

        const titleEl = div.querySelector(".event-title");
        if (titleEl) {
            titleEl.style.cursor = "pointer";
            titleEl.title = "Click to log view";
            titleEl.addEventListener("click", async () => {
                const userId = getUserId();
                if (!userId || viewedThisSet.has(event.id)) return;
                viewedThisSet.add(event.id);
                await logActivity(userId, event.id, "view", { source: "ui_event_title_click" });
            });
        }

        container.appendChild(div);
    });

    attachPurchaseHandlers();
}

/**
 * Attaches click handlers to all "Buy" buttons on the page.
 * Called after events are rendered.
 */
function attachPurchaseHandlers() {
    document.querySelectorAll("button.buy-btn").forEach(button => {
        button.addEventListener("click", () => {
            const ticketId = button.getAttribute("data-ticket-id");
            purchaseTicket(ticketId);
        });
    });
}

/**
 * Attaches click handlers to cancel order buttons.
 * Called after tickets are rendered.
 */
function attachCancelHandlers() {
    document.querySelectorAll("button.cancel-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const orderId = button.getAttribute("data-order-id");
            if (confirm("Are you sure you want to cancel this order?")) {
                await cancelOrder(orderId);
            }
        });
    });
}

function showInlineMap(eventId, venue, city, title) {
    const container = document.getElementById(`event-map-${eventId}`);
    if (!container || container.dataset.loaded) return;
    container.dataset.loaded = "true";
    
    const FALLBACK_COORDS = {
        "central park arena helsinki": [60.1699, 24.9384],
        "convention center oulu": [65.0126, 25.4682],
        "helsinki": [60.1699, 24.9384],
        "oulu": [65.0126, 25.4682]
    };
    
    let lat = 60.1699, lon = 24.9384;
    const searchKey = `${venue} ${city}`.toLowerCase();
    if (FALLBACK_COORDS[searchKey]) {
        [lat, lon] = FALLBACK_COORDS[searchKey];
    } else if (FALLBACK_COORDS[venue.toLowerCase()]) {
        [lat, lon] = FALLBACK_COORDS[venue.toLowerCase()];
    }
    
    const zoom = 15;
    const mapUrl = `https://staticmap.openstreetmap.de/staticmap.php?center=${lat},${lon}&zoom=${zoom}&size=400x200&markers=${lat},${lon},lightblue`;
    
    container.innerHTML = `
        <div style="text-align:center;">
            <img src="${mapUrl}" alt="Map" style="width:100%;max-width:400px;border-radius:6px;border:1px solid #ccc;">
            <p style="margin:8px 0 0;font-size:0.85rem;color:#555;">${venue}, ${city}</p>
            <a href="https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}&zoom=${zoom}" target="_blank" style="font-size:0.8rem;color:#007bff;">Open in OSM</a>
        </div>
    `;
}

/**
 * Cancels an order (deletes it).
 * 
 * @param {number|string} orderId - ID of the order to cancel
 * @returns {Promise<void>}
 */
async function cancelOrder(orderId) {
    if (!isLoggedIn()) {
        showMessage("Please log in to cancel orders.", true);
        return;
    }

    const cancelBtn = document.querySelector(`button[data-order-id="${orderId}"]`);
    if (cancelBtn) {
        cancelBtn.disabled = true;
        cancelBtn.textContent = "Cancelling...";
    }

    try {
        const response = await fetch(`${API_BASE}/orders/${orderId}/`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });

        if (response.ok) {
            showMessage("Order cancelled successfully!");
            showTicketsLoading();
            await loadMyTickets();
        } else {
            const text = await response.text();
            let result = null;
            try {
                result = JSON.parse(text);
            } catch (e) {
                result = { message: text };
            }
            showMessage(result?.error || result?.message || "Failed to cancel order.", true);
            loadMyTickets();
        }
    } catch (e) {
        showMessage("Network error. Please try again.", true);
        loadMyTickets();
    }
}

/**
 * Purchases a ticket for the authenticated user.
 * Validates login status and handles purchase response.
 * 
 * @param {number|string} ticketId - ID of the ticket to purchase
 * @returns {Promise<void>}
 */
async function purchaseTicket(ticketId) {
    if (!isLoggedIn()) {
        showMessage("Please log in to purchase tickets.", true);
        return;
    }

    const buyBtn = document.querySelector(`button[data-ticket-id="${ticketId}"]`);
    if (buyBtn) {
        buyBtn.disabled = true;
        buyBtn.textContent = "Processing...";
    }

    try {
        const response = await fetch(`${API_BASE}/orders/`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                ticket_id: parseInt(ticketId),
                quantity: 1
            })
        });

        let result = null;
        const text = await response.text();
        if (text) {
            try {
                result = JSON.parse(text);
            } catch (e) {
                result = { message: text };
            }
        }

        if (response.ok) {
            showMessage("Purchase successful!");
            document.getElementById("message").className = "message success";
            // Wait a moment before reloading to let message stay visible
            setTimeout(() => {
                showEventsLoading();
                loadEvents();
            }, 1000);
        } else {
            const errorMsg = result?.error || result?.message || "Purchase failed.";
            showMessage(errorMsg, true);
            loadEvents();
        }
    } catch (e) {
        showMessage("Network error. Please try again.", true);
        loadEvents();
    }
}

/**
 * Loads and displays the authenticated user's purchased tickets.
 * Fetches orders from API and shows event details.
 * 
 * @returns {Promise<void>}
 */
async function loadMyTickets() {
    if (!isLoggedIn()) {
        document.getElementById("my-tickets").innerHTML = "<p>Please log in to view your tickets.</p>";
        return;
    }

    showTicketsLoading();
    
    const userId = getUserId();
    const response = await fetch(`${API_BASE}/users/${userId}/orders/`, {
        headers: getAuthHeaders()
    });

    if (!response.ok) {
        hideTicketsLoading();
        document.getElementById("my-tickets").innerHTML = `<p>Could not load tickets. Status: ${response.status}</p>`;
        return;
    }

    const ordersData = await response.json();
    const orders = ordersData.items || [];
    
    hideTicketsLoading();
    
    const container = document.getElementById("my-tickets");
    container.innerHTML = "";

    if (orders.length === 0) {
        container.innerHTML = "<p>You have no purchased tickets.</p>";
        return;
    }

    try {
        const ticketResp = await fetch(`${API_BASE}/events/`);
        const eventsData = await ticketResp.json();
        const events = eventsData.items || [];
        
        const ticketEventMap = new Map();
        for (const event of events) {
            if (event.tickets) {
                for (const ticket of event.tickets) {
                    ticketEventMap.set(ticket.id, { ticketName: ticket.name, eventName: event.title });
                }
            }
        }

        for (const order of orders) {
            const ticketInfo = ticketEventMap.get(order.ticket_id) || { ticketName: "Unknown Ticket", eventName: "Unknown Event" };
            
            const statusDisplay = order.status === "not_used" ? "Unused" : 
                             order.status === "used" ? "Used" : 
                             order.status === "cancelled" ? "Cancelled" : 
                             order.status;
            
            const canCancel = order.status === "not_used";

            const div = document.createElement("div");
            div.className = "ticket-item";
            div.innerHTML = `
                <strong>${ticketInfo.eventName} - ${ticketInfo.ticketName}</strong><br>
                Order #${order.id} | Status: ${statusDisplay}<br>
                Purchased: ${new Date(order.created_at).toLocaleString()}
                ${canCancel ? `<br><button class="cancel-btn" data-order-id="${order.id}">Cancel Order</button>` : ""}
            `;
            container.appendChild(div);
        }
        
        // Attach cancel handlers
        attachCancelHandlers();
    } catch (e) {
        console.warn("Could not fetch ticket details:", e);
        container.innerHTML = "<p>Could not load ticket details.</p>";
    }
}

/**
 * Performs user login with email and password.
 * Validates input and handles authentication response.
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise<boolean>} True if login successful, false otherwise
 */
async function login(email, password) {
    if (!isValidEmail(email)) {
        showMessage("Please enter a valid email address.", true);
        return false;
    }
    
    if (!isValidPassword(password)) {
        showMessage("Please enter your password.", true);
        return false;
    }

    const submitBtn = document.querySelector("#login-form button[type='submit']");
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Logging in...";
    submitBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/auth/login/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (response.ok) {
            setAuth(result.token, result.user_id, email);
            updateAuthUI();
            loadEvents();
            loadMyTickets();
            showMessage("Logged in successfully!");
            return true;
        } else {
            showMessage(result.error || "Login failed.", true);
            return false;
        }
    } catch (e) {
        showMessage("Network error. Please try again.", true);
        return false;
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Performs user logout.
 * Updates UI and clears session data.
 * 
 * @returns {Promise<void>}
 */
async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout/`, {
            method: "POST",
            headers: getAuthHeaders()
        });
    } catch (e) {
        console.warn("Logout API call failed:", e);
    }
    
    clearAuth();
    updateAuthUI();
    document.getElementById("events").innerHTML = "";
    document.getElementById("my-tickets").innerHTML = "";
    showMessage("Logged out.");
}

/**
 * Displays a message to the user.
 * Shows success or error message with auto-clear after 5 seconds.
 * 
 * @param {string} text - Message text to display
 * @param {boolean} [isError=false] - Whether this is an error message
 */
function showMessage(text, isError = false) {
    const msgDiv = document.getElementById("message");
    msgDiv.textContent = text;
    msgDiv.className = "message" + (isError ? " error" : "");
    setTimeout(() => {
        msgDiv.textContent = "";
    }, 5000);
}

/**
 * Updates the UI based on authentication state.
 * Shows/hides login form vs. user greeting and navigation.
 */
function updateAuthUI() {
    const authSection = document.getElementById("auth-section");
    const userSection = document.getElementById("user-section");
    const navSection = document.getElementById("nav-section");

    if (isLoggedIn()) {
        authSection.style.display = "none";
        userSection.style.display = "flex";
        navSection.style.display = "flex";
        document.getElementById("user-greeting").textContent = getUserName();
    } else {
        authSection.style.display = "flex";
        userSection.style.display = "none";
        navSection.style.display = "none";
    }
}

/**
 * Attaches event handlers for authentication forms and navigation.
 * Called once on page load.
 */
function attachAuthHandlers() {
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        await login(email, password);
    });

    document.getElementById("logout-btn").addEventListener("click", logout);

    document.getElementById("nav-events").addEventListener("click", () => {
        document.getElementById("my-tickets-section").style.display = "none";
        document.getElementById("events-section").style.display = "block";
    });

    document.getElementById("nav-tickets").addEventListener("click", () => {
        document.getElementById("events-section").style.display = "none";
        document.getElementById("my-tickets-section").style.display = "block";
        loadMyTickets();
    });

    // Search functionality
    const searchInput = document.getElementById("event-search");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const filtered = filterEvents(e.target.value);
            renderEvents(filtered);
        });
    }
}

/**
 * Initializes the application on page load.
 * Sets up UI state and loads initial data.
 */
document.addEventListener("DOMContentLoaded", () => {
    updateAuthUI();
    attachAuthHandlers();
    loadEvents();
});