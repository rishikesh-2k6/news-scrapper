/**
 * AI Intelligence Hub — Dashboard Controller
 * Handles status polling, agent start/stop, and news data rendering
 * with XSS-safe DOM manipulation.
 */

// ── State ──────────────────────────────────────────────────────────────
let statusInterval = null;
let dataInterval = null;

// ── Helpers ────────────────────────────────────────────────────────────

/** Escape HTML entities to prevent XSS when rendering user/LLM text. */
function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

// ── Initialise ─────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    fetchStatus();
    fetchNews();

    // Poll status every 3 seconds (reduced from 2 to ease server load)
    statusInterval = setInterval(fetchStatus, 3000);
    // Poll data every 15 seconds
    dataInterval = setInterval(fetchNews, 15000);
});

// ── Status ─────────────────────────────────────────────────────────────

async function fetchStatus() {
    const statusDot = document.getElementById("statusDot");
    const statusValue = document.getElementById("statusValue");
    const batteryValue = document.getElementById("batteryValue");
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");

    try {
        const response = await fetch("/api/status");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        const agentStatus = data.status || "Unknown";
        const isPlugged = data.battery_plugged;

        statusValue.textContent = agentStatus;
        batteryValue.textContent = isPlugged ? "Plugged In (AC)" : "On Battery";
        batteryValue.style.color = isPlugged ? "#10b981" : "#f59e0b";

        // Update status indicator dot
        statusDot.className = "status-dot";
        if (
            agentStatus.includes("Running") ||
            agentStatus.includes("Starting") ||
            agentStatus.includes("Sleeping")
        ) {
            statusDot.classList.add("running");
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else if (agentStatus.includes("Paused")) {
            statusDot.classList.add("paused");
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusDot.classList.add("stopped");
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    } catch (error) {
        console.error("Error fetching status:", error);
        statusValue.textContent = "Server Offline";
        statusDot.className = "status-dot stopped";
    }
}

// ── Agent Controls ─────────────────────────────────────────────────────

async function startAgent() {
    const startBtn = document.getElementById("startBtn");
    startBtn.disabled = true;
    try {
        const res = await fetch("/api/start", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        fetchStatus();
    } catch (error) {
        console.error("Error starting agent:", error);
        startBtn.disabled = false;
    }
}

async function stopAgent() {
    const stopBtn = document.getElementById("stopBtn");
    stopBtn.disabled = true;
    try {
        const res = await fetch("/api/stop", { method: "POST" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        fetchStatus();
    } catch (error) {
        console.error("Error stopping agent:", error);
        stopBtn.disabled = false;
    }
}

// ── News Table ─────────────────────────────────────────────────────────

async function fetchNews() {
    const tableBody = document.getElementById("newsTableBody");
    try {
        const response = await fetch("/api/news");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        const data = result.data || [];

        if (data.length === 0) {
            tableBody.innerHTML =
                '<tr><td colspan="5" class="loading">No intelligence data yet. Start the agent!</td></tr>';
            return;
        }

        // Show newest first
        const reversedData = [...data].reverse();

        // Build rows safely (no innerHTML with unsanitised data)
        tableBody.innerHTML = "";
        reversedData.forEach((item) => {
            const tr = document.createElement("tr");

            const tdCompany = document.createElement("td");
            const strong = document.createElement("strong");
            strong.textContent = item.Company || "N/A";
            tdCompany.appendChild(strong);

            const tdModel = document.createElement("td");
            tdModel.textContent = item.Model || "N/A";

            const tdMetrics = document.createElement("td");
            const small = document.createElement("small");
            small.textContent = item.Metrics || "N/A";
            tdMetrics.appendChild(small);

            const tdSummary = document.createElement("td");
            tdSummary.textContent = item.InnovationSummary || "N/A";

            const tdSource = document.createElement("td");
            if (item.SourceURL) {
                const a = document.createElement("a");
                a.href = item.SourceURL;
                a.target = "_blank";
                a.rel = "noopener noreferrer";
                a.textContent = "View Article";
                tdSource.appendChild(a);
            } else {
                tdSource.textContent = "N/A";
            }

            tr.appendChild(tdCompany);
            tr.appendChild(tdModel);
            tr.appendChild(tdMetrics);
            tr.appendChild(tdSummary);
            tr.appendChild(tdSource);
            tableBody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}
