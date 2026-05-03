// Global State
let agentStatus = "Stopped";
let statusInterval = null;
let dataInterval = null;

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusValue = document.getElementById('statusValue');
const batteryValue = document.getElementById('batteryValue');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const tableBody = document.getElementById('newsTableBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    fetchNews();
    
    // Poll status every 2 seconds
    statusInterval = setInterval(fetchStatus, 2000);
    // Poll data every 10 seconds
    dataInterval = setInterval(fetchNews, 10000);
});

// Fetch Agent Status
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        agentStatus = data.status;
        const isPlugged = data.battery_plugged;
        
        // Update UI
        statusValue.textContent = agentStatus;
        batteryValue.textContent = isPlugged ? "Plugged In (AC)" : "On Battery";
        batteryValue.style.color = isPlugged ? "#10b981" : "#f59e0b";
        
        // Update Dot
        statusDot.className = 'status-dot';
        if (agentStatus.includes("Running") || agentStatus.includes("Starting") || agentStatus.includes("Sleeping")) {
            statusDot.classList.add('running');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else if (agentStatus.includes("Paused")) {
            statusDot.classList.add('paused');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusDot.classList.add('stopped');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
        
    } catch (error) {
        console.error("Error fetching status:", error);
        statusValue.textContent = "Server Offline";
        statusDot.className = 'status-dot stopped';
    }
}

// Start Agent
async function startAgent() {
    startBtn.disabled = true;
    try {
        await fetch('/api/start', { method: 'POST' });
        fetchStatus();
    } catch (error) {
        console.error("Error starting agent:", error);
        startBtn.disabled = false;
    }
}

// Stop Agent
async function stopAgent() {
    stopBtn.disabled = true;
    try {
        await fetch('/api/stop', { method: 'POST' });
        fetchStatus();
    } catch (error) {
        console.error("Error stopping agent:", error);
        stopBtn.disabled = false;
    }
}

// Fetch News Data
async function fetchNews() {
    try {
        const response = await fetch('/api/news');
        const result = await response.json();
        const data = result.data;
        
        if (data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">No intelligence data gathered yet. Start the agent!</td></tr>';
            return;
        }
        
        // Reverse array to show newest first (assuming appended rows are newer)
        const reversedData = [...data].reverse();
        
        tableBody.innerHTML = '';
        reversedData.forEach(item => {
            const tr = document.createElement('tr');
            
            // Format link
            const urlStr = item.SourceURL ? `<a href="${item.SourceURL}" target="_blank">View Article</a>` : 'N/A';
            
            tr.innerHTML = `
                <td><strong>${item.Company || 'N/A'}</strong></td>
                <td>${item.Model || 'N/A'}</td>
                <td><small>${item.Metrics || 'N/A'}</small></td>
                <td>${item.InnovationSummary || 'N/A'}</td>
                <td>${urlStr}</td>
            `;
            tableBody.appendChild(tr);
        });
        
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}
