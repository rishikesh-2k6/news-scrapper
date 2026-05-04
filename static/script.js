/**
 * AI Intelligence Hub — Dashboard Controller
 * Handles status polling, agent start/stop, and news card rendering
 * with XSS-safe DOM manipulation.
 */

// ── State ──────────────────────────────────────────────────────────────
let statusInterval = null;
let dataInterval = null;

// ── Helpers ────────────────────────────────────────────────────────────

/** Create a DOM element with optional classes and text content. */
function el(tag, classes, text) {
    const node = document.createElement(tag);
    if (classes) node.className = classes;
    if (text) node.textContent = text;
    return node;
}

/** Return a colour class based on impact score. */
function impactColor(score) {
    const s = parseInt(score, 10) || 0;
    if (s >= 9) return "impact-critical";
    if (s >= 7) return "impact-high";
    if (s >= 5) return "impact-medium";
    return "impact-low";
}

/** Map category strings to readable badge labels. */
function categoryLabel(cat) {
    const map = {
        NEW_MODEL: "New Model",
        FEATURE_UPDATE: "Feature Update",
        TOOL_RELEASE: "Tool Release",
        RESEARCH: "Research",
        INDUSTRY: "Industry",
    };
    return map[(cat || "").toUpperCase()] || cat || "Unknown";
}

// ── Initialise ─────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    fetchStatus();
    fetchNews();
    statusInterval = setInterval(fetchStatus, 3000);
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
        batteryValue.textContent = isPlugged ? "⚡ Plugged In (AC)" : "🔋 On Battery";
        batteryValue.style.color = isPlugged ? "#10b981" : "#f59e0b";

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

// ── News Cards ─────────────────────────────────────────────────────────

function updateStats(data) {
    const totalEl = document.getElementById("totalCount");
    const highEl = document.getElementById("highImpactCount");
    const avgEl = document.getElementById("avgScore");

    totalEl.textContent = data.length;

    const scores = data.map((d) => parseInt(d.impact_score, 10) || 0);
    const high = scores.filter((s) => s >= 7).length;
    highEl.textContent = high;

    const avg = scores.length > 0
        ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
        : "0";
    avgEl.textContent = avg;
}

function buildCard(item) {
    const card = el("article", "intel-card glass-card");

    // ── Header row: category badge + impact score ──
    const header = el("div", "card-header");

    const badge = el("span", `category-badge cat-${(item.category || "").toLowerCase()}`);
    badge.textContent = categoryLabel(item.category);
    header.appendChild(badge);

    const score = parseInt(item.impact_score, 10) || 0;
    const scoreEl = el("span", `impact-score ${impactColor(score)}`);
    scoreEl.textContent = `${score}/10`;
    header.appendChild(scoreEl);

    card.appendChild(header);

    // ── Hook (headline) ──
    const hook = el("h3", "card-hook", item.hook || item.name || "Untitled");
    card.appendChild(hook);

    // ── Company + Name ──
    const meta = el("div", "card-meta");
    const companySpan = el("span", "card-company", item.company || "Unknown");
    const nameSpan = el("span", "card-name", item.name || "");
    meta.appendChild(companySpan);
    if (item.name) {
        meta.appendChild(document.createTextNode(" · "));
        meta.appendChild(nameSpan);
    }
    card.appendChild(meta);

    // ── Explanation ──
    if (item.explanation) {
        const explSection = el("div", "card-section");
        explSection.appendChild(el("span", "section-label", "What is it?"));
        explSection.appendChild(el("p", "section-body", item.explanation));
        card.appendChild(explSection);
    }

    // ── Innovation ──
    if (item.innovation) {
        const innovSection = el("div", "card-section");
        innovSection.appendChild(el("span", "section-label", "Innovation"));
        innovSection.appendChild(el("p", "section-body", item.innovation));
        card.appendChild(innovSection);
    }

    // ── Why It Matters ──
    if (item.why_it_matters) {
        const whySection = el("div", "card-section highlight-section");
        whySection.appendChild(el("span", "section-label", "💡 Why It Matters"));
        whySection.appendChild(el("p", "section-body", item.why_it_matters));
        card.appendChild(whySection);
    }

    // ── Benchmark (if present) ──
    if (item.benchmark && item.benchmark !== "N/A") {
        const benchSection = el("div", "card-section");
        benchSection.appendChild(el("span", "section-label", "📊 Benchmark"));
        benchSection.appendChild(el("p", "section-body mono", item.benchmark));
        card.appendChild(benchSection);
    }

    // ── Content Idea ──
    if (item.content_idea) {
        const ideaSection = el("div", "card-section idea-section");
        ideaSection.appendChild(el("span", "section-label", "🎬 Content Idea"));
        ideaSection.appendChild(el("p", "section-body", item.content_idea));
        card.appendChild(ideaSection);
    }

    // ── Footer: use_case, depth, source link ──
    const footer = el("div", "card-footer");

    if (item.technical_depth) {
        const depthBadge = el("span", `depth-badge depth-${(item.technical_depth || "").toLowerCase()}`);
        depthBadge.textContent = `${(item.technical_depth || "").toUpperCase()} depth`;
        footer.appendChild(depthBadge);
    }

    if (item.SourceURL) {
        const link = document.createElement("a");
        link.href = item.SourceURL;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.className = "source-link";
        link.textContent = "View Source →";
        footer.appendChild(link);
    }

    card.appendChild(footer);

    return card;
}

async function fetchNews() {
    const container = document.getElementById("newsCards");
    try {
        const response = await fetch("/api/news");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        const data = result.data || [];

        updateStats(data);

        if (data.length === 0) {
            container.innerHTML = "";
            const empty = el("div", "empty-state glass-card");
            empty.appendChild(el("p", null, "No intelligence data yet. Start the agent!"));
            container.appendChild(empty);
            return;
        }

        // Newest first
        const sorted = [...data].reverse();

        container.innerHTML = "";
        sorted.forEach((item) => {
            container.appendChild(buildCard(item));
        });
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}
