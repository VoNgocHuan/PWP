const API_BASE = "/api";

const AUTH_TOKEN_KEY = "auth_token";
const USER_ID_KEY = "user_id";
const USER_NAME_KEY = "user_name";

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function getUserId() {
    return localStorage.getItem(USER_ID_KEY);
}

function getUserName() {
    return localStorage.getItem(USER_NAME_KEY);
}

function setAuth(token, userId, userName) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(USER_ID_KEY, userId);
    localStorage.setItem(USER_NAME_KEY, userName);
}

function clearAuth() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem(USER_NAME_KEY);
}

function isLoggedIn() {
    return !!getToken();
}

function getAuthHeaders() {
    const token = getToken();
    if (!token) return {};
    return {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };
}

const viewedThisSet = new Set();

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

async function loadEvents() {
    let events;
    try {
        const response = await fetch(`${API_BASE}/events/`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        events = await response.json();
    } catch (e) {
        console.error("Failed to load events:", e);
        document.getElementById("events").innerHTML = `<p>Error loading events: ${e.message}</p>`;
        return;
    }

    const container = document.getElementById("events");
    container.innerHTML = "";

    if (!Array.isArray(events) || events.length === 0) {
        container.innerHTML = "<p>No events available.</p>";
        return;
    }

    events.forEach(event => {
        const div = document.createElement("div");
        div.className = "event";

        let ticketBoxes = "";

        if (event.tickets && event.tickets.length > 0) {
            event.tickets.forEach(ticket => {
                ticketBoxes += `
                    <div class="ticket-box">
                        <strong>${ticket.name}</strong><br>
                        Price: €${ticket.price}<br>
                        Remaining: ${ticket.remaining}<br>
                        <button class="buy-btn" data-ticket-id="${ticket.id}">
                            Buy
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

function attachPurchaseHandlers() {
    document.querySelectorAll("button.buy-btn").forEach(button => {
        button.addEventListener("click", () => {
            const ticketId = button.getAttribute("data-ticket-id");
            purchaseTicket(ticketId);
        });
    });
}

async function purchaseTicket(ticketId) {
    if (!isLoggedIn()) {
        showMessage("Please log in to purchase tickets.", true);
        return;
    }

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
        loadEvents();
    } else {
        showMessage(result?.error || result?.message || "Purchase failed.", true);
    }
}

async function loadMyTickets() {
    if (!isLoggedIn()) {
        document.getElementById("my-tickets").innerHTML = "<p>Please log in to view your tickets.</p>";
        return;
    }

    const userId = getUserId();
    const response = await fetch(`${API_BASE}/users/${userId}/orders/`, {
        headers: getAuthHeaders()
    });

    if (!response.ok) {
        document.getElementById("my-tickets").innerHTML = `<p>Could not load tickets. Status: ${response.status}</p>`;
        return;
    }

    const orders = await response.json();
    const container = document.getElementById("my-tickets");
    container.innerHTML = "";

    if (orders.length === 0) {
        container.innerHTML = "<p>You have no purchased tickets.</p>";
        return;
    }

    for (const order of orders) {
        let ticketName = "Unknown Ticket";
        let eventName = "Unknown Event";

        try {
            const ticketResp = await fetch(`${API_BASE}/events/`);
            const events = await ticketResp.json();
            
            for (const event of events) {
                if (event.tickets) {
                    const ticket = event.tickets.find(t => t.id === order.ticket_id);
                    if (ticket) {
                        ticketName = ticket.name;
                        eventName = event.title;
                        break;
                    }
                }
            }
        } catch (e) {
            console.warn("Could not fetch ticket details:", e);
        }

        const statusDisplay = order.status === "not_used" ? "Unused" : 
                             order.status === "used" ? "Used" : 
                             order.status === "cancelled" ? "Cancelled" : 
                             order.status;

        const div = document.createElement("div");
        div.className = "ticket-item";
        div.innerHTML = `
            <strong>${eventName} - ${ticketName}</strong><br>
            Order #${order.id} | Status: ${statusDisplay}<br>
            Purchased: ${new Date(order.created_at).toLocaleString()}
        `;
        container.appendChild(div);
    }
}

async function login(email, password) {
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
}

async function logout() {
    const token = getToken();
    if (token) {
        try {
            await fetch(`${API_BASE}/auth/logout/`, {
                method: "POST",
                headers: getAuthHeaders()
            });
        } catch (e) {
            console.warn("Logout API call failed:", e);
        }
    }
    clearAuth();
    updateAuthUI();
    document.getElementById("events").innerHTML = "";
    document.getElementById("my-tickets").innerHTML = "";
    showMessage("Logged out.");
}

function showMessage(text, isError = false) {
    const msgDiv = document.getElementById("message");
    msgDiv.textContent = text;
    msgDiv.className = "message" + (isError ? " error" : "");
    setTimeout(() => {
        msgDiv.textContent = "";
    }, 5000);
}

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
}

document.addEventListener("DOMContentLoaded", () => {
    updateAuthUI();
    attachAuthHandlers();
    loadEvents();
});
