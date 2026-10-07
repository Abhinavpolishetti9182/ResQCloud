"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const METRICS_URL = "/api/v1/monitoring/metrics";
    const INFRASTRUCTURE_URL = "/api/v1/infrastructure";
    const BACKUPS_URL = "/api/v1/backups";
    const INCIDENTS_URL = "/api/v1/incidents";
    const RECOVERY_URL = "/api/v1/recovery-requests";

    const $ = (id) => document.getElementById(id);

    function setText(id, value) {
        const element = $(id);

        if (element) {
            element.textContent = value;
        }
    }

    function formatNumber(value, decimals = 2) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "Unavailable";
        }

        return number.toFixed(decimals);
    }

    function formatPercent(value) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "Unavailable";
        }

        return `${number.toFixed(2)}%`;
    }

    function formatBytes(value) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "Unavailable";
        }

        if (number >= 1024 ** 3) {
            return `${(number / (1024 ** 3)).toFixed(2)} GB`;
        }

        if (number >= 1024 ** 2) {
            return `${(number / (1024 ** 2)).toFixed(2)} MB`;
        }

        if (number >= 1024) {
            return `${(number / 1024).toFixed(2)} KB`;
        }

        return `${number.toFixed(0)} B`;
    }

    function formatDate(value) {
        if (!value) {
            return "Unavailable";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return date.toLocaleString();
    }

    /*
     * =========================================================
     * CLOUDWATCH STATUS
     * =========================================================
     */

    function setMonitoringStatus(message, status) {
        const element = $("metrics-status");

        if (!element) {
            return;
        }

        element.textContent = message;

        element.classList.remove(
            "monitoring-success",
            "monitoring-error"
        );

        if (status === "success") {
            element.classList.add("monitoring-success");
        }

        if (status === "error") {
            element.classList.add("monitoring-error");
        }
    }

    /*
     * =========================================================
     * METRIC HELPERS
     * =========================================================
     */

    function getMetricValue(metric) {
        if (metric === null || metric === undefined) {
            return null;
        }

        if (typeof metric === "number") {
            return metric;
        }

        if (typeof metric === "object") {
            if (metric.value !== undefined) {
                return Number(metric.value);
            }

            if (metric.average !== undefined) {
                return Number(metric.average);
            }

            if (metric.Average !== undefined) {
                return Number(metric.Average);
            }
        }

        return Number(metric);
    }

    function getLatestMetric(metrics) {
        if (!Array.isArray(metrics) || metrics.length === 0) {
            return null;
        }

        const valid = metrics
            .map((item) => ({
                raw: item,
                value: getMetricValue(item)
            }))
            .filter((item) => Number.isFinite(item.value));

        if (valid.length === 0) {
            return null;
        }

        return valid[valid.length - 1].value;
    }

    /*
     * =========================================================
     * CHART DRAWING
     * =========================================================
     */

    function drawChart(canvasId, points, title, formatter) {
        const canvas = $(canvasId);

        if (!canvas) {
            return;
        }

        const context = canvas.getContext("2d");

        if (!context) {
            return;
        }

        const width = canvas.width;
        const height = canvas.height;

        context.clearRect(0, 0, width, height);

        const values = (Array.isArray(points) ? points : [])
            .map(getMetricValue)
            .filter((value) => Number.isFinite(value));

        context.font = "12px Segoe UI, Arial, sans-serif";
        context.fillStyle = "#93a4bd";

        if (values.length === 0) {
            context.fillText(
                "No metric data available",
                24,
                35
            );

            return;
        }

        const padding = 38;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        let min = Math.min(...values);
        let max = Math.max(...values);

        if (min === max) {
            min -= 1;
            max += 1;
        }

        /*
         * Grid
         */

        context.strokeStyle = "#263750";
        context.lineWidth = 1;

        for (let i = 0; i <= 4; i += 1) {
            const y =
                padding +
                (chartHeight / 4) * i;

            context.beginPath();
            context.moveTo(padding, y);
            context.lineTo(width - padding, y);
            context.stroke();
        }

        /*
         * Chart title
         */

        context.fillStyle = "#e8eef8";
        context.font = "600 12px Segoe UI, Arial, sans-serif";

        context.fillText(
            title,
            padding,
            18
        );

        /*
         * Line
         */

        context.beginPath();

        values.forEach((value, index) => {
            const x =
                padding +
                (chartWidth *
                    index /
                    Math.max(values.length - 1, 1));

            const normalized =
                (value - min) /
                (max - min);

            const y =
                padding +
                chartHeight -
                normalized * chartHeight;

            if (index === 0) {
                context.moveTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        });

        context.strokeStyle = "#3b82f6";
        context.lineWidth = 2;
        context.stroke();

        /*
         * Latest value
         */

        const latest = values[values.length - 1];

        context.fillStyle = "#e8eef8";
        context.font = "600 12px Segoe UI, Arial, sans-serif";

        context.fillText(
            formatter(latest),
            width - 105,
            18
        );
    }

    /*
     * =========================================================
     * API HELPER
     * =========================================================
     */

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
            cache: "no-store",
            ...options
        });

        let data = null;

        try {
            data = await response.json();
        } catch (error) {
            throw new Error(
                `Invalid JSON response from ${url}`
            );
        }

        if (!response.ok) {
            throw new Error(
                data.message ||
                data.error ||
                `Request failed: ${response.status}`
            );
        }

        return data;
    }

    /*
     * =========================================================
     * CLOUDWATCH METRICS
     * =========================================================
     */

    async function loadMetrics() {
        setMonitoringStatus(
            "Loading CloudWatch...",
            null
        );

        try {
            const data =
                await fetchJson(METRICS_URL);

            if (data.success === false) {
                throw new Error(
                    data.message ||
                    "CloudWatch metrics unavailable."
                );
            }

            /*
             * Resource information
             */

            setText(
                "metric-instance-id",
                data.instance_id || "Unavailable"
            );

            setText(
                "metric-region",
                data.region || "Unavailable"
            );

            setText(
                "metrics-last-updated",
                formatDate(data.generated_at)
            );

            const metrics =
                data.metrics || {};

            const latest =
                data.latest || {};

            /*
             * CPU
             */

            const latestCpu =
                latest.cpu !== undefined &&
                latest.cpu !== null
                    ? latest.cpu
                    : getLatestMetric(metrics.cpu);

            setText(
                "latest-cpu",
                formatPercent(latestCpu)
            );

            /*
             * Memory
             */

            const latestMemory =
                latest.memory !== undefined &&
                latest.memory !== null
                    ? latest.memory
                    : getLatestMetric(metrics.memory);

            setText(
                "latest-memory",
                formatPercent(latestMemory)
            );

            /*
             * Disk
             */

            const latestDisk =
                latest.disk !== undefined &&
                latest.disk !== null
                    ? latest.disk
                    : getLatestMetric(metrics.disk);

            setText(
                "latest-disk",
                formatPercent(latestDisk)
            );

            /*
             * Network
             */

            const latestNetworkIn =
                getLatestMetric(
                    metrics.network_in
                );

            const latestNetworkOut =
                getLatestMetric(
                    metrics.network_out
                );

            setText(
                "latest-network-in",
                formatBytes(latestNetworkIn)
            );

            setText(
                "latest-network-out",
                formatBytes(latestNetworkOut)
            );

            /*
             * Charts
             */

            drawChart(
                "cpu-chart",
                metrics.cpu || [],
                "CPU Utilization",
                formatPercent
            );

            drawChart(
                "memory-chart",
                metrics.memory || [],
                "Memory Utilization",
                formatPercent
            );

            drawChart(
                "disk-chart",
                metrics.disk || [],
                "Disk Utilization",
                formatPercent
            );

            drawChart(
                "network-in-chart",
                metrics.network_in || [],
                "Network In",
                formatBytes
            );

            drawChart(
                "network-out-chart",
                metrics.network_out || [],
                "Network Out",
                formatBytes
            );

            setMonitoringStatus(
                "CloudWatch Connected",
                "success"
            );

            return data;

        } catch (error) {
            console.error(
                "ResQCloud CloudWatch error:",
                error
            );

            setMonitoringStatus(
                "CloudWatch Error",
                "error"
            );

            setText(
                "metrics-last-updated",
                "Unable to retrieve metrics"
            );

            return null;
        }
    }

    /*
     * =========================================================
     * DASHBOARD SUMMARY
     * =========================================================
     */

    async function loadDashboardSummary() {
        try {
            const [
                infrastructure,
                backups,
                incidents,
                recovery
            ] = await Promise.all([
                fetchJson(INFRASTRUCTURE_URL),
                fetchJson(BACKUPS_URL),
                fetchJson(INCIDENTS_URL),
                fetchJson(RECOVERY_URL)
            ]);

            updateDashboardCards(
                infrastructure,
                backups,
                incidents,
                recovery
            );

            renderIncidentTable(incidents);
            renderRecoveryTable(recovery);

        } catch (error) {
            console.error(
                "ResQCloud dashboard summary error:",
                error
            );
        }
    }

    function getArrayFromResponse(data, keys) {
        if (Array.isArray(data)) {
            return data;
        }

        if (!data || typeof data !== "object") {
            return [];
        }

        for (const key of keys) {
            if (Array.isArray(data[key])) {
                return data[key];
            }
        }

        return [];
    }

    function updateDashboardCards(
        infrastructure,
        backups,
        incidents,
        recovery
    ) {
        const infrastructureItems =
            getArrayFromResponse(
                infrastructure,
                [
                    "resources",
                    "infrastructure",
                    "items",
                    "data"
                ]
            );

        const backupItems =
            getArrayFromResponse(
                backups,
                [
                    "backups",
                    "items",
                    "data"
                ]
            );

        const incidentItems =
            getArrayFromResponse(
                incidents,
                [
                    "incidents",
                    "items",
                    "data"
                ]
            );

        const recoveryItems =
            getArrayFromResponse(
                recovery,
                [
                    "recovery_requests",
                    "requests",
                    "items",
                    "data"
                ]
            );

        const openIncidents =
            incidentItems.filter((item) => {
                const status =
                    String(item.status || "")
                        .toLowerCase();

                return [
                    "open",
                    "active",
                    "investigating",
                    "detected"
                ].includes(status);
            });

        const activeRecovery =
            recoveryItems.filter((item) => {
                const status =
                    String(item.status || "")
                        .toLowerCase();

                return [
                    "pending",
                    "approved",
                    "executing",
                    "verifying",
                    "in_progress"
                ].includes(status);
            });

        /*
         * These IDs are used only when they exist
         * in the current dashboard.
         */

        setText(
            "infrastructure-count",
            infrastructureItems.length
        );

        setText(
            "backup-count",
            backupItems.length
        );

        setText(
            "incident-count",
            openIncidents.length
        );

        setText(
            "recovery-count",
            activeRecovery.length
        );
    }

    /*
     * =========================================================
     * INCIDENT TABLE
     * =========================================================
     */

    function renderIncidentTable(data) {
        const tableBody =
            $("dashboard-incidents-body");

        if (!tableBody) {
            return;
        }

        const incidents =
            getArrayFromResponse(
                data,
                [
                    "incidents",
                    "items",
                    "data"
                ]
            );

        tableBody.innerHTML = "";

        if (incidents.length === 0) {
            tableBody.innerHTML =
                '<tr><td colspan="6" class="empty-state">No incidents found.</td></tr>';

            return;
        }

        incidents.slice(0, 10).forEach((incident) => {
            const row =
                document.createElement("tr");

            const severity =
                incident.severity ||
                "unknown";

            const status =
                incident.status ||
                "unknown";

            row.innerHTML = `
                <td>${escapeHtml(
                    incident.id ??
                    incident.incident_id ??
                    "-"
                )}</td>

                <td>${escapeHtml(
                    severity
                )}</td>

                <td>${escapeHtml(
                    incident.title ||
                    incident.name ||
                    incident.description ||
                    "-"
                )}</td>

                <td>${escapeHtml(
                    incident.resource_id ||
                    incident.resource ||
                    "-"
                )}</td>

                <td>
                    <span class="badge ${getStatusBadgeClass(status)}">
                        ${escapeHtml(status)}
                    </span>
                </td>

                <td>${escapeHtml(
                    formatDate(
                        incident.created_at ||
                        incident.detected_at ||
                        incident.timestamp
                    )
                )}</td>
            `;

            tableBody.appendChild(row);
        });
    }

    /*
     * =========================================================
     * RECOVERY TABLE
     * =========================================================
     */

    function renderRecoveryTable(data) {
        const tableBody =
            $("dashboard-recovery-body");

        if (!tableBody) {
            return;
        }

        const requests =
            getArrayFromResponse(
                data,
                [
                    "recovery_requests",
                    "requests",
                    "items",
                    "data"
                ]
            );

        tableBody.innerHTML = "";

        if (requests.length === 0) {
            tableBody.innerHTML =
                '<tr><td colspan="6" class="empty-state">No recovery requests found.</td></tr>';

            return;
        }

        requests.slice(0, 10).forEach((request) => {
            const row =
                document.createElement("tr");

            const status =
                request.status ||
                "unknown";

            row.innerHTML = `
                <td>${escapeHtml(
                    request.id ??
                    request.request_id ??
                    "-"
                )}</td>

                <td>${escapeHtml(
                    request.incident_id ||
                    "-"
                )}</td>

                <td>${escapeHtml(
                    request.backup_id ||
                    "-"
                )}</td>

                <td>${escapeHtml(
                    request.requested_by ||
                    "-"
                )}</td>

                <td>
                    <span class="badge ${getStatusBadgeClass(status)}">
                        ${escapeHtml(status)}
                    </span>
                </td>

                <td>${escapeHtml(
                    formatDate(
                        request.created_at ||
                        request.requested_at
                    )
                )}</td>
            `;

            tableBody.appendChild(row);
        });
    }

    /*
     * =========================================================
     * STATUS BADGES
     * =========================================================
     */

    function getStatusBadgeClass(status) {
        const value =
            String(status || "")
                .toLowerCase();

        if (
            [
                "completed",
                "success",
                "successful",
                "verified",
                "healthy",
                "resolved"
            ].includes(value)
        ) {
            return "badge-success";
        }

        if (
            [
                "pending",
                "approved",
                "executing",
                "verifying",
                "warning",
                "investigating"
            ].includes(value)
        ) {
            return "badge-warning";
        }

        if (
            [
                "failed",
                "error",
                "critical",
                "rejected"
            ].includes(value)
        ) {
            return "badge-danger";
        }

        return "badge-info";
    }

    /*
     * =========================================================
     * HTML ESCAPING
     * =========================================================
     */

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    /*
     * =========================================================
     * REFRESH
     * =========================================================
     */

    const refreshButton =
        $("metrics-refresh");

    if (refreshButton) {
        refreshButton.addEventListener(
            "click",
            async function () {

                refreshButton.disabled = true;

                try {
                    await Promise.all([
                        loadMetrics(),
                        loadDashboardSummary()
                    ]);
                } finally {
                    refreshButton.disabled = false;
                }
            }
        );
    }

    /*
     * =========================================================
     * INITIAL LOAD
     * =========================================================
     */

    loadMetrics();
    loadDashboardSummary();

    /*
     * Refresh CloudWatch metrics every 60 seconds.
     */

    setInterval(
        loadMetrics,
        60000
    );

    /*
     * Refresh dashboard summary every 60 seconds.
     */

    setInterval(
        loadDashboardSummary,
        60000
    );

    /*
     * =========================================================
     * PUBLIC DASHBOARD API
     * =========================================================
     */

    window.ResQCloudDashboard = {
        refreshMetrics: loadMetrics,

        refreshSummary: loadDashboardSummary,

        refreshAll: async function () {
            await Promise.all([
                loadMetrics(),
                loadDashboardSummary()
            ]);
        }
    };
});