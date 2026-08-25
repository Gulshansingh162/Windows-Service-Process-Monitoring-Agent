let performanceChart = null;

const chartLabels = [];
const cpuData = [];
const memoryData = [];


function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


async function api(
    url,
    options = {}
) {

    const response =
        await fetch(
            url,
            options
        );

    if (
        response.status === 401
    ) {

        window.location.href =
            "/login";

        throw new Error(
            "Authentication required"
        );
    }

    const data =
        await response.json();

    if (!response.ok) {

        throw new Error(
            data.error ||
            "Request failed"
        );
    }

    return data;
}


/* =========================
   CHART
========================= */

function initializeChart() {

    const canvas =
        document.getElementById(
            "performanceChart"
        );

    if (!canvas) {
        return;
    }

    performanceChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels: chartLabels,

                    datasets: [

                        {
                            label: "CPU %",
                            data: cpuData,

                            borderWidth: 2,

                            tension: 0.35,

                            fill: false
                        },

                        {
                            label: "Memory %",
                            data: memoryData,

                            borderWidth: 2,

                            tension: 0.35,

                            fill: false
                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    scales: {

                        y: {

                            beginAtZero: true,

                            max: 100,

                            ticks: {
                                color: "#8493a8"
                            },

                            grid: {
                                color:
                                    "rgba(255,255,255,0.05)"
                            }

                        },

                        x: {

                            ticks: {
                                color: "#8493a8"
                            },

                            grid: {
                                display: false
                            }

                        }

                    },

                    plugins: {

                        legend: {
                            labels: {
                                color: "#dce6f2"
                            }
                        }

                    }

                }

            }
        );
}


function updateChart(
    cpu,
    memory
) {

    if (!performanceChart) {
        return;
    }

    const now =
        new Date();

    const label =
        now.toLocaleTimeString();

    chartLabels.push(label);

    cpuData.push(cpu);

    memoryData.push(memory);

    if (chartLabels.length > 20) {

        chartLabels.shift();

        cpuData.shift();

        memoryData.shift();
    }

    performanceChart.update();
}


/* =========================
   SYSTEM
========================= */

async function loadSystem() {

    try {

        const data =
            await api(
                "/api/system"
            );

        document.getElementById(
            "cpuValue"
        ).textContent =
            data.cpu_percent + "%";

        document.getElementById(
            "memoryValue"
        ).textContent =
            data.memory_percent + "%";

        document.getElementById(
            "processValue"
        ).textContent =
            data.process_count;

        updateChart(
            data.cpu_percent,
            data.memory_percent
        );

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   AGENT STATUS
========================= */

async function loadAgentStatus() {

    try {

        const data =
            await api(
                "/api/agent/status"
            );

        const status =
            data.status;

        const element =
            document.getElementById(
                "agentStatus"
            );

        const securityAgent =
            document.getElementById(
                "securityAgent"
            );

        if (
            status === "running"
        ) {

            element.textContent =
                "● Agent Running";

            securityAgent.textContent =
                "RUNNING";

        } else {

            element.textContent =
                "● " + status;

            securityAgent.textContent =
                String(status).toUpperCase();
        }

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   USER
========================= */

async function loadUser() {

    try {

        const data =
            await api(
                "/api/me"
            );

        document.getElementById(
            "currentUser"
        ).textContent =
            data.username;

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   PROCESSES
========================= */

async function loadProcesses() {

    try {

        const search =
            document.getElementById(
                "processSearch"
            ).value;

        const url =
            "/api/processes?search="
            +
            encodeURIComponent(
                search
            );

        const processes =
            await api(url);

        const table =
            document.getElementById(
                "processTable"
            );

        table.innerHTML = "";

        if (
            processes.length === 0
        ) {

            table.innerHTML = `
                <tr>
                    <td colspan="6"
                        class="empty-state">
                        No processes found.
                    </td>
                </tr>
            `;

            return;
        }

        processes.forEach(
            process => {

                const row =
                    document.createElement(
                        "tr"
                    );

                let cpuClass = "";

                if (
                    process.cpu_percent >= 90
                ) {

                    cpuClass =
                        "status-stopped";

                } else if (
                    process.cpu_percent >= 70
                ) {

                    cpuClass =
                        "status-warning";
                }

                row.innerHTML = `
                    <td>${escapeHTML(process.pid)}</td>

                    <td>
                        <strong>
                            ${escapeHTML(process.name)}
                        </strong>
                    </td>

                    <td>
                        ${escapeHTML(process.status)}
                    </td>

                    <td class="${cpuClass}">
                        ${escapeHTML(process.cpu_percent)}%
                    </td>

                    <td>
                        ${escapeHTML(process.memory_percent)}%
                    </td>

                    <td>
                        ${escapeHTML(process.username)}
                    </td>
                `;

                table.appendChild(row);
            }
        );

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   SERVICES
========================= */

async function loadServices() {

    try {

        const search =
            document.getElementById(
                "serviceSearch"
            ).value;

        const services =
            await api(
                "/api/services?search="
                +
                encodeURIComponent(
                    search
                )
            );

        const table =
            document.getElementById(
                "serviceTable"
            );

        table.innerHTML = "";

        services.forEach(
            service => {

                const row =
                    document.createElement(
                        "tr"
                    );

                const running =
                    service.status ===
                    "running";

                const statusClass =
                    running
                        ? "status-running"
                        : "status-stopped";

                const controlButtons =
                    running

                        ? `
                            <button
                                class="control-button stop-button"
                                onclick="controlService(
                                    '${escapeHTML(service.name)}',
                                    'stop'
                                )"
                            >
                                Stop
                            </button>
                        `

                        : `
                            <button
                                class="control-button start-button"
                                onclick="controlService(
                                    '${escapeHTML(service.name)}',
                                    'start'
                                )"
                            >
                                Start
                            </button>
                        `;

                row.innerHTML = `

                    <td>
                        <strong>
                            ${escapeHTML(service.name)}
                        </strong>
                    </td>

                    <td>
                        ${escapeHTML(service.display_name)}
                    </td>

                    <td class="${statusClass}">
                        ${escapeHTML(service.status)}
                    </td>

                    <td>
                        ${escapeHTML(service.start_type)}
                    </td>

                    <td>
                        ${controlButtons}
                    </td>

                `;

                table.appendChild(row);
            }
        );

    } catch (error) {

        console.error(error);
    }
}


async function controlService(
    serviceName,
    action
) {

    const confirmed =
        confirm(
            `Are you sure you want to ${action} "${serviceName}"?`
        );

    if (!confirmed) {
        return;
    }

    try {

        const data =
            await api(
                "/api/services/control",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        name: serviceName,
                        action: action
                    })
                }
            );

        alert(
            data.message ||
            "Command sent successfully."
        );

        setTimeout(
            loadServices,
            1500
        );

    } catch (error) {

        alert(
            "Service control failed:\n\n"
            +
            error.message
        );
    }
}


/* =========================
   ALERTS
========================= */

async function loadAlerts() {

    try {

        const alerts =
            await api(
                "/api/alerts"
            );

        const count =
            await api(
                "/api/alerts/count"
            );

        document.getElementById(
            "alertValue"
        ).textContent =
            count.count;

        const container =
            document.getElementById(
                "alertsContainer"
            );

        container.innerHTML = "";

        if (
            alerts.length === 0
        ) {

            container.innerHTML = `
                <div class="empty-state">
                    ✓ No active security alerts.
                </div>
            `;

            return;
        }

        alerts.forEach(
            alertItem => {

                const div =
                    document.createElement(
                        "div"
                    );

                const high =
                    alertItem.severity
                    === "HIGH";

                div.className =
                    high
                        ? "alert high"
                        : "alert";

                div.innerHTML = `

                    <div>

                        <div class="alert-title">

                            ${escapeHTML(
                                alertItem.title
                            )}

                        </div>

                        <div class="alert-message">

                            ${escapeHTML(
                                alertItem.message
                            )}

                        </div>

                        <div class="alert-time">

                            ${escapeHTML(
                                alertItem.timestamp
                            )}

                        </div>

                    </div>

                    <button
                        class="ack-button"
                        onclick="acknowledgeAlert(
                            ${alertItem.id}
                        )"
                    >
                        Acknowledge
                    </button>
                `;

                container.appendChild(div);
            }
        );

    } catch (error) {

        console.error(error);
    }
}


async function acknowledgeAlert(
    id
) {

    try {

        await api(
            `/api/alerts/${id}/acknowledge`,
            {
                method: "POST"
            }
        );

        await loadAlerts();

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   EVENTS
========================= */

async function loadEvents() {

    try {

        const events =
            await api(
                "/api/events"
            );

        const table =
            document.getElementById(
                "eventTable"
            );

        table.innerHTML = "";

        events.forEach(
            event => {

                const row =
                    document.createElement(
                        "tr"
                    );

                row.innerHTML = `

                    <td>
                        ${escapeHTML(
                            event.timestamp
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            event.event_type
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            event.name
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            event.status
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            event.message
                        )}
                    </td>

                `;

                table.appendChild(row);
            }
        );

    } catch (error) {

        console.error(error);
    }
}


/* =========================
   LOGOUT
========================= */

document.getElementById(
    "logoutButton"
).addEventListener(
    "click",
    async function() {

        try {

            await api(
                "/api/logout",
                {
                    method: "POST"
                }
            );

        } finally {

            window.location.href =
                "/login";
        }

    }
);


/* =========================
   SEARCH ENTER KEY
========================= */

document.getElementById(
    "processSearch"
).addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            loadProcesses();
        }
    }
);


document.getElementById(
    "serviceSearch"
).addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            loadServices();
        }
    }
);


/* =========================
   INITIALIZATION
========================= */

async function refreshDashboard() {

    await Promise.all([
        loadSystem(),
        loadAgentStatus(),
        loadProcesses(),
        loadServices(),
        loadAlerts(),
        loadEvents()
    ]);
}


initializeChart();

loadUser();

refreshDashboard();


setInterval(
    refreshDashboard,
    5000
);