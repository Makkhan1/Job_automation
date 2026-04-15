// --- Configuration ---
const API_BASE_URL = 'http://localhost:8000'; // Your FastAPI backend

// --- DOM Elements ---
const incomingList = document.getElementById('incoming-list');
const outgoingList = document.getElementById('outgoing-list');

// --- UI Render Functions ---
function createIncomingCard(data) {
    return `
        <div class="msg-card">
            <div class="card-top">
                <span class="source-badge ${data.source.toLowerCase()}">${data.source}</span>
                <span class="time">${data.time}</span>
            </div>
            <div class="sender-name"><i class="fa-brands fa-${data.platform.toLowerCase()}"></i> ${data.name}</div>
            <div class="preview-text">${data.preview}</div>
        </div>
    `;
}

function createOutgoingCard(data) {
    return `
        <div class="msg-card" style="border-left: 3px solid var(--accent-green);">
            <div class="card-top">
                <span class="sender-name" style="margin:0;"><i class="fa-solid fa-paper-plane" style="color: var(--accent-green); margin-right: 5px;"></i> ${data.recipient}</span>
                <span class="time">${data.time}</span>
            </div>
            <div class="preview-text" style="margin-top: 8px;">${data.preview}</div>
        </div>
    `;
}

// --- Chart.js Configuration ---
const ctx = document.getElementById('activityChart').getContext('2d');

// Gradient for the line chart
let gradient = ctx.createLinearGradient(0, 0, 0, 400);
gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Blue
gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

const activityChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['12 AM', '2 AM', '4 AM', '6 AM', '8 AM', '10 AM', '12 PM'],
        datasets: [{
            label: 'Processed Jobs',
            data: [0, 0, 0, 0, 0, 0, 0],
            borderColor: '#3b82f6',
            backgroundColor: gradient,
            borderWidth: 2,
            tension: 0.4, // Smooth curves
            fill: true,
            pointBackgroundColor: '#111827',
            pointBorderColor: '#3b82f6',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.9)',
                titleColor: '#f3f4f6',
                bodyColor: '#9ca3af',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#9ca3af' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#9ca3af' }
            }
        }
    }
});

// --- Live API Fetching Logic ---
async function fetchDashboardData() {
    try {
        console.log(`🔄 Fetching dashboard data from ${API_BASE_URL}/api/dashboard...`);
        
        const response = await fetch(`${API_BASE_URL}/api/dashboard`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Dashboard data received:', data);

        // 1. Update Metrics
        document.getElementById('metric-received').innerText = data.metrics.received;
        document.getElementById('metric-processed').innerText = data.metrics.processed;
        document.getElementById('metric-ignored').innerText = data.metrics.ignored;
        document.getElementById('metric-errors').innerText = data.metrics.errors;

        // 2. Update Lists
        incomingList.innerHTML = data.incoming.length > 0 
            ? data.incoming.map(createIncomingCard).join('') 
            : '<p style="text-align: center; color: #9ca3af; padding: 20px;">No incoming messages yet</p>';
        
        outgoingList.innerHTML = data.outgoing.length > 0 
            ? data.outgoing.map(createOutgoingCard).join('') 
            : '<p style="text-align: center; color: #9ca3af; padding: 20px;">No outgoing messages yet</p>';

        // 3. Update Chart
        activityChart.data.datasets[0].data = data.chartData;
        activityChart.update();

    } catch (error) {
        console.error("❌ Failed to load live data:", error);
        console.error("Make sure:");
        console.error("1. FastAPI backend is running on http://localhost:8000");
        console.error("2. The database has been initialized with messages");
        console.error("3. CORS is properly configured");
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');
    
    // Fetch immediately on load
    fetchDashboardData();
    
    // Poll the backend every 5 seconds to keep the dashboard "Live"
    const pollInterval = setInterval(fetchDashboardData, 5000);
    console.log('📊 Live polling enabled (every 5 seconds)');
});