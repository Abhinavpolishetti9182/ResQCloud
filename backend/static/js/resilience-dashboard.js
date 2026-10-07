(() => {
    async function getJson(url) {
        const response = await fetch(url);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.message || `HTTP ${response.status}`
            );
        }

        return data;
    }

    function addCell(row, value) {
        const cell = document.createElement("td");
        cell.textContent = value ?? "";
        row.appendChild(cell);
        return cell;
    }

    async function loadIncidents() {
        const body = document.getElementById("incident-list");

        if (!body) {
            return;
        }

        try {
            const data = await getJson(
                "/api/v1/incidents"
            );

            const incidents = data.incidents || [];

            const countElement =
                document.getElementById("incident-count");

            if (countElement) {
                countElement.textContent = incidents.length;
            }

            body.replaceChildren();

            if (!incidents.length) {
                const row = document.createElement("tr");
                const cell = addCell(
                    row,
                    "No incidents recorded."
                );
                cell.colSpan = 5;
                body.appendChild(row);
                return;
            }

            for (const incident of incidents) {
                const row = document.createElement("tr");

                addCell(row, incident.id);
                addCell(row, incident.title);
                addCell(row, incident.severity);
                addCell(row, incident.status);
                addCell(row, incident.description);
            }
        } catch (error) {
            body.replaceChildren();

            const row = document.createElement("tr");
            const cell = addCell(
                row,
                "Unable to load incidents: " + error.message
            );

            cell.colSpan = 5;
            body.appendChild(row);
        }
    }

    async function loadRecoveryRequests() {
        const body = document.getElementById("recovery-list");

        if (!body) {
            return;
        }

        try {
            const data = await getJson(
                "/api/v1/recovery-requests"
            );

            const requests =
                data.recovery_requests || [];

            const statusElement =
                document.getElementById("recovery-status");

            if (statusElement) {
                if (!requests.length) {
                    statusElement.textContent = "No requests";
                } else {
                    const latest = requests[0];
                    statusElement.textContent =
                        latest.status || "Unknown";
                }
            }

            body.replaceChildren();

            if (!requests.length) {
                const row = document.createElement("tr");
                const cell = addCell(
                    row,
                    "No recovery requests recorded."
                );
                cell.colSpan = 5;
                body.appendChild(row);
                return;
            }

            for (const request of requests) {
                const row = document.createElement("tr");

                addCell(row, request.id);
                addCell(row, request.resource_name);
                addCell(row, request.recovery_type);
                addCell(row, request.status);
                addCell(row, request.reason);
            }
        } catch (error) {
            body.replaceChildren();

            const row = document.createElement("tr");
            const cell = addCell(
                row,
                "Unable to load recovery requests: "
                + error.message
            );

            cell.colSpan = 5;
            body.appendChild(row);
        }
    }

    async function loadBackups() {
        try {
            const data = await getJson(
                "/api/v1/backups"
            );

            const backups = data.backups || [];

            const backupStatus =
                document.getElementById("backup-status");

            if (backupStatus) {
                backupStatus.textContent =
                    `${backups.length} backup(s)`;
            }

            const backupList =
                document.getElementById("backup-list");

            if (!backupList) {
                return;
            }

            backupList.replaceChildren();

            const recentBackups =
                backups.slice(0, 5);

            if (!recentBackups.length) {
                const row = document.createElement("tr");
                const cell = addCell(
                    row,
                    "No backup records."
                );
                cell.colSpan = 3;
                backupList.appendChild(row);
                return;
            }

            for (const backup of recentBackups) {
                const row = document.createElement("tr");

                addCell(row, backup.name);
                addCell(row, backup.backup_type);
                addCell(row, backup.status);

                backupList.appendChild(row);
            }
        } catch (error) {
            const backupStatus =
                document.getElementById("backup-status");

            if (backupStatus) {
                backupStatus.textContent = "Unavailable";
            }
        }
    }

    async function loadInfrastructure() {
        try {
            const data = await getJson(
                "/api/v1/infrastructure"
            );

            const resources =
                data.resources || [];

            const statusElement =
                document.getElementById(
                    "infrastructure-status"
                );

            if (statusElement) {
                statusElement.textContent =
                    data.status || "Unknown";
            }

            const list =
                document.getElementById(
                    "infrastructure-list"
                );

            if (!list) {
                return;
            }

            list.replaceChildren();

            if (!resources.length) {
                const row = document.createElement("tr");
                const cell = addCell(
                    row,
                    "No infrastructure resources."
                );
                cell.colSpan = 3;
                list.appendChild(row);
                return;
            }

            for (const resource of resources) {
                const row = document.createElement("tr");

                addCell(row, resource.name);
                addCell(row, resource.resource_type);
                addCell(row, resource.status);

                list.appendChild(row);
            }
        } catch (error) {
            const statusElement =
                document.getElementById(
                    "infrastructure-status"
                );

            if (statusElement) {
                statusElement.textContent = "Unavailable";
            }
        }
    }

    async function refreshDashboard() {
        await Promise.all([
            loadIncidents(),
            loadRecoveryRequests(),
            loadBackups(),
            loadInfrastructure()
        ]);
    }

    document
        .getElementById("incident-refresh-button")
        ?.addEventListener(
            "click",
            loadIncidents
        );

    document
        .getElementById("recovery-refresh-button")
        ?.addEventListener(
            "click",
            loadRecoveryRequests
        );

    refreshDashboard();

    setInterval(
        refreshDashboard,
        30000
    );
})();