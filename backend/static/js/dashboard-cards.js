document.addEventListener("DOMContentLoaded", function () {

    /*
     * =========================================================
     * RESQCLOUD DASHBOARD CONTROLLER
     * =========================================================
     *
     * Responsibilities:
     *
     * 1. Load dashboard statistics.
     * 2. Load infrastructure data.
     * 3. Load backup data.
     * 4. Load incident data.
     * 5. Load recovery data.
     * 6. Make dashboard cards interactive.
     * 7. Show operational details in a modal.
     * 8. Populate Incident and Recovery tabs.
     *
     * =========================================================
     */


    /* ---------------------------------------------------------
       DOM REFERENCES
       --------------------------------------------------------- */

    const modal =
        document.getElementById(
            "dashboard-details-modal"
        );

    const modalTitle =
        document.getElementById(
            "dashboard-modal-title"
        );

    const modalBody =
        document.getElementById(
            "dashboard-modal-body"
        );

    const modalClose =
        document.getElementById(
            "dashboard-modal-close"
        );

    const modalCloseFooter =
        document.getElementById(
            "dashboard-modal-close-footer"
        );

    const modalAction =
        document.getElementById(
            "dashboard-modal-action"
        );

    const lastRefresh =
        document.getElementById(
            "dashboard-last-refresh"
        );


    /* ---------------------------------------------------------
       CARD REFERENCES
       --------------------------------------------------------- */

    const infrastructureCards =
        document.querySelectorAll(
            '[data-dashboard-card="infrastructure"]'
        );

    const backupCards =
        document.querySelectorAll(
            '[data-dashboard-card="backups"]'
        );

    const incidentCards =
        document.querySelectorAll(
            '[data-dashboard-card="incidents"]'
        );

    const recoveryCards =
        document.querySelectorAll(
            '[data-dashboard-card="recovery"]'
        );


    /* ---------------------------------------------------------
       DATA CACHE
       --------------------------------------------------------- */

    let dashboardData = {

        infrastructure: null,

        backups: null,

        incidents: null,

        recovery: null

    };


    let currentActionTab = null;


    /* ---------------------------------------------------------
       HTML ESCAPE
       --------------------------------------------------------- */

    function escapeHtml(value) {

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


    /* ---------------------------------------------------------
       STATUS CLASS
       --------------------------------------------------------- */

    function getStatusClass(status) {

        const value =
            String(status || "")
                .toLowerCase();

        if (
            value.includes("complete") ||
            value.includes("success") ||
            value.includes("healthy") ||
            value.includes("operational") ||
            value.includes("running") ||
            value.includes("verified") ||
            value.includes("restored")
        ) {
            return "success";
        }

        if (
            value.includes("pending") ||
            value.includes("progress") ||
            value.includes("warning")
        ) {
            return "warning";
        }

        if (
            value.includes("failed") ||
            value.includes("critical") ||
            value.includes("error") ||
            value.includes("down")
        ) {
            return "danger";
        }

        return "";
    }


    /* ---------------------------------------------------------
       STATUS BADGE
       --------------------------------------------------------- */

    function statusBadge(status) {

        const safeStatus =
            escapeHtml(
                status || "unknown"
            );

        const statusClass =
            getStatusClass(status);

        return `
            <span
                class="dashboard-detail-status ${statusClass}">

                ${safeStatus}

            </span>
        `;
    }


    /* ---------------------------------------------------------
       API REQUEST
       --------------------------------------------------------- */

    async function getJson(url) {

        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );

        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );

        }

        return await response.json();
    }


    /* ---------------------------------------------------------
       UPDATE LAST REFRESH
       --------------------------------------------------------- */

    function updateLastRefresh() {

        if (!lastRefresh) {
            return;
        }

        const now =
            new Date();

        lastRefresh.textContent =
            "Last refreshed: " +
            now.toLocaleTimeString(
                [],
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            );
    }


    /* ---------------------------------------------------------
       MODAL OPEN
       --------------------------------------------------------- */

    function openModal(
        title,
        body,
        actionText = null,
        actionTab = null
    ) {

        if (!modal) {
            return;
        }

        modalTitle.textContent =
            title;

        modalBody.innerHTML =
            body;

        currentActionTab =
            actionTab;


        if (
            modalAction &&
            actionText &&
            actionTab
        ) {

            modalAction.textContent =
                actionText;

            modalAction.style.display =
                "inline-flex";

        } else if (modalAction) {

            modalAction.style.display =
                "none";

        }


        modal.classList.add(
            "active"
        );

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "modal-open"
        );

    }


    /* ---------------------------------------------------------
       MODAL CLOSE
       --------------------------------------------------------- */

    function closeModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove(
            "active"
        );

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );

        currentActionTab =
            null;

    }


    /* ---------------------------------------------------------
       INFRASTRUCTURE DETAILS
       --------------------------------------------------------- */

    async function showInfrastructureDetails() {

        openModal(
            "Infrastructure Details",
            `
                <div
                    class="dashboard-modal-loading">

                    Loading infrastructure information...

                </div>
            `
        );


        try {

            const data =
                await getJson(
                    "/api/v1/infrastructure"
                );


            dashboardData.infrastructure =
                data;


            const resources =
                data.resources || [];


            let html = `

                <div class="dashboard-detail-summary">

                    <div>

                        <span>
                            Platform Status
                        </span>

                        <strong>
                            ${escapeHtml(
                                data.status ||
                                "unknown"
                            )}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Environment
                        </span>

                        <strong>
                            ${escapeHtml(
                                data.environment ||
                                "unknown"
                            )}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Resources
                        </span>

                        <strong>
                            ${resources.length}
                        </strong>

                    </div>

                </div>
            `;


            if (
                resources.length === 0
            ) {

                html += `

                    <div
                        class="dashboard-detail-empty">

                        No infrastructure resources
                        are registered yet.

                    </div>

                `;

            } else {

                html += `
                    <div
                        class="dashboard-detail-list">
                `;


                resources.forEach(
                    resource => {

                        html += `

                            <div
                                class="dashboard-detail-item">

                                <div>

                                    <strong>
                                        ${escapeHtml(
                                            resource.name
                                        )}
                                    </strong>

                                    <small>
                                        ${escapeHtml(
                                            resource.resource_type
                                        )}

                                        ${
                                            resource.environment
                                                ? " • " +
                                                  escapeHtml(
                                                      resource.environment
                                                  )
                                                : ""
                                        }
                                    </small>

                                </div>


                                <div>

                                    ${statusBadge(
                                        resource.status
                                    )}

                                </div>

                            </div>

                        `;

                    }
                );


                html += `
                    </div>
                `;
            }


            openModal(
                "Infrastructure Details",
                html
            );

        }

        catch (error) {

            openModal(
                "Infrastructure Details",
                `
                    <div
                        class="dashboard-detail-error">

                        Unable to load infrastructure
                        information.

                        <br><br>

                        ${escapeHtml(
                            error.message
                        )}

                    </div>
                `
            );

        }

    }


    /* ---------------------------------------------------------
       BACKUP DETAILS
       --------------------------------------------------------- */

    async function showBackupDetails() {

        openModal(
            "Backup Details",
            `
                <div
                    class="dashboard-modal-loading">

                    Loading backup information...

                </div>
            `,
            "Open Backup Management",
            "backup-management"
        );


        try {

            const data =
                await getJson(
                    "/api/v1/backups"
                );


            dashboardData.backups =
                data;


            const backups =
                data.backups || [];


            const completed =
                backups.filter(
                    backup =>
                        String(
                            backup.status || ""
                        ).toLowerCase()
                        === "completed"
                ).length;


            let html = `

                <div class="dashboard-detail-summary">

                    <div>

                        <span>
                            Total Backups
                        </span>

                        <strong>
                            ${backups.length}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Completed
                        </span>

                        <strong>
                            ${completed}
                        </strong>

                    </div>


                    <div>

                        <span>
                            API Status
                        </span>

                        <strong>
                            ${escapeHtml(
                                data.status ||
                                "unknown"
                            )}
                        </strong>

                    </div>

                </div>

            `;


            if (
                backups.length === 0
            ) {

                html += `

                    <div
                        class="dashboard-detail-empty">

                        No backup records were found.

                    </div>

                `;

            } else {

                html += `
                    <div
                        class="dashboard-detail-list">
                `;


                backups
                    .slice(0, 8)
                    .forEach(
                        backup => {

                            html += `

                                <div
                                    class="dashboard-detail-item">

                                    <div>

                                        <strong>
                                            #${escapeHtml(
                                                backup.id
                                            )}

                                            —

                                            ${escapeHtml(
                                                backup.name
                                            )}
                                        </strong>

                                        <small>
                                            ${escapeHtml(
                                                backup.backup_type ||
                                                "manual"
                                            )}

                                            ${
                                                backup.created_at
                                                    ? " • " +
                                                      escapeHtml(
                                                          backup.created_at
                                                      )
                                                    : ""
                                            }
                                        </small>

                                    </div>


                                    <div>

                                        ${statusBadge(
                                            backup.status
                                        )}

                                    </div>

                                </div>

                            `;

                        }
                    );


                html += `
                    </div>
                `;


                if (
                    backups.length > 8
                ) {

                    html += `

                        <p
                            class="dashboard-detail-note">

                            Showing the latest 8 backups.
                            Open Backup Management to view
                            the complete history.

                        </p>

                    `;

                }

            }


            openModal(
                "Backup Details",
                html,
                "Open Backup Management",
                "backup-management"
            );

        }

        catch (error) {

            openModal(
                "Backup Details",
                `
                    <div
                        class="dashboard-detail-error">

                        Unable to load backup information.

                        <br><br>

                        ${escapeHtml(
                            error.message
                        )}

                    </div>
                `,
                "Open Backup Management",
                "backup-management"
            );

        }

    }


    /* ---------------------------------------------------------
       INCIDENT DETAILS
       --------------------------------------------------------- */

    async function showIncidentDetails() {

        openModal(
            "Incident Details",
            `
                <div
                    class="dashboard-modal-loading">

                    Loading incident information...

                </div>
            `,
            "Open Incident Management",
            "incidents-tab"
        );


        try {

            const data =
                await getJson(
                    "/api/v1/incidents"
                );


            dashboardData.incidents =
                data;


            const incidents =
                data.incidents || [];


            const openIncidents =
                incidents.filter(
                    incident =>
                        String(
                            incident.status || ""
                        ).toLowerCase()
                        === "open"
                ).length;


            const criticalIncidents =
                incidents.filter(
                    incident =>
                        String(
                            incident.severity || ""
                        ).toLowerCase()
                        === "critical"
                ).length;


            let html = `

                <div class="dashboard-detail-summary">

                    <div>

                        <span>
                            Total Incidents
                        </span>

                        <strong>
                            ${incidents.length}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Open
                        </span>

                        <strong>
                            ${openIncidents}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Critical
                        </span>

                        <strong>
                            ${criticalIncidents}
                        </strong>

                    </div>

                </div>

            `;


            if (
                incidents.length === 0
            ) {

                html += `

                    <div
                        class="dashboard-detail-empty">

                        No incidents have been recorded.

                    </div>

                `;

            } else {

                html += `
                    <div
                        class="dashboard-detail-list">
                `;


                incidents
                    .slice(0, 8)
                    .forEach(
                        incident => {

                            html += `

                                <div
                                    class="dashboard-detail-item">

                                    <div>

                                        <strong>
                                            #${escapeHtml(
                                                incident.id
                                            )}

                                            —

                                            ${escapeHtml(
                                                incident.title
                                            )}
                                        </strong>

                                        <small>
                                            ${escapeHtml(
                                                incident.description ||
                                                "No description provided."
                                            )}
                                        </small>

                                    </div>


                                    <div
                                        class="dashboard-detail-status-group">

                                        ${statusBadge(
                                            incident.severity
                                        )}

                                        ${statusBadge(
                                            incident.status
                                        )}

                                    </div>

                                </div>

                            `;

                        }
                    );


                html += `
                    </div>
                `;

            }


            openModal(
                "Incident Details",
                html,
                "Open Incident Management",
                "incidents-tab"
            );

        }

        catch (error) {

            openModal(
                "Incident Details",
                `
                    <div
                        class="dashboard-detail-error">

                        Unable to load incident information.

                        <br><br>

                        ${escapeHtml(
                            error.message
                        )}

                    </div>
                `,
                "Open Incident Management",
                "incidents-tab"
            );

        }

    }


    /* ---------------------------------------------------------
       RECOVERY DETAILS
       --------------------------------------------------------- */

    async function showRecoveryDetails() {

        openModal(
            "Recovery Details",
            `
                <div
                    class="dashboard-modal-loading">

                    Loading recovery information...

                </div>
            `,
            "Open Recovery Management",
            "recovery-tab"
        );


        try {

            const data =
                await getJson(
                    "/api/v1/recovery-requests"
                );


            dashboardData.recovery =
                data;


            const requests =
                data.recovery_requests || [];


            const completed =
                requests.filter(
                    request =>
                        String(
                            request.status || ""
                        ).toLowerCase()
                        === "completed"
                ).length;


            const active =
                requests.filter(
                    request => {

                        const status =
                            String(
                                request.status || ""
                            ).toLowerCase();

                        return (
                            status === "pending" ||
                            status === "in_progress"
                        );

                    }
                ).length;


            let html = `

                <div class="dashboard-detail-summary">

                    <div>

                        <span>
                            Total Requests
                        </span>

                        <strong>
                            ${requests.length}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Completed
                        </span>

                        <strong>
                            ${completed}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Active
                        </span>

                        <strong>
                            ${active}
                        </strong>

                    </div>

                </div>

            `;


            if (
                requests.length === 0
            ) {

                html += `

                    <div
                        class="dashboard-detail-empty">

                        No recovery requests have been
                        recorded.

                    </div>

                `;

            } else {

                html += `
                    <div
                        class="dashboard-detail-list">
                `;


                requests
                    .slice(0, 8)
                    .forEach(
                        request => {

                            html += `

                                <div
                                    class="dashboard-detail-item">

                                    <div>

                                        <strong>
                                            #${escapeHtml(
                                                request.id
                                            )}

                                            —

                                            ${escapeHtml(
                                                request.resource_name ||
                                                "Unknown resource"
                                            )}
                                        </strong>

                                        <small>

                                            ${escapeHtml(
                                                request.recovery_type ||
                                                "Recovery"
                                            )}

                                            ${
                                                request.reason
                                                    ? " • " +
                                                      escapeHtml(
                                                          request.reason
                                                      )
                                                    : ""
                                            }

                                        </small>

                                    </div>


                                    <div>

                                        ${statusBadge(
                                            request.status
                                        )}

                                    </div>

                                </div>

                            `;

                        }
                    );


                html += `
                    </div>
                `;

            }


            openModal(
                "Recovery Details",
                html,
                "Open Recovery Management",
                "recovery-tab"
            );

        }

        catch (error) {

            openModal(
                "Recovery Details",
                `
                    <div
                        class="dashboard-detail-error">

                        Unable to load recovery information.

                        <br><br>

                        ${escapeHtml(
                            error.message
                        )}

                    </div>
                `,
                "Open Recovery Management",
                "recovery-tab"
            );

        }

    }


    /* ---------------------------------------------------------
       LOAD DASHBOARD SUMMARY
       --------------------------------------------------------- */

    async function loadDashboardSummary() {

        try {

            const results =
                await Promise.allSettled([

                    getJson(
                        "/api/v1/infrastructure"
                    ),

                    getJson(
                        "/api/v1/backups"
                    ),

                    getJson(
                        "/api/v1/incidents"
                    ),

                    getJson(
                        "/api/v1/recovery-requests"
                    )

                ]);


            const infrastructure =
                results[0].status === "fulfilled"
                    ? results[0].value
                    : null;


            const backups =
                results[1].status === "fulfilled"
                    ? results[1].value
                    : null;


            const incidents =
                results[2].status === "fulfilled"
                    ? results[2].value
                    : null;


            const recovery =
                results[3].status === "fulfilled"
                    ? results[3].value
                    : null;


            dashboardData.infrastructure =
                infrastructure;

            dashboardData.backups =
                backups;

            dashboardData.incidents =
                incidents;

            dashboardData.recovery =
                recovery;


            /* ---------------------------------------------
               INFRASTRUCTURE CARD
               --------------------------------------------- */

            const infrastructureStatus =
                document.getElementById(
                    "infrastructure-status"
                );


            if (
                infrastructureStatus
            ) {

                infrastructureStatus.textContent =
                    infrastructure
                        ? (
                            infrastructure.status ||
                            "unknown"
                        )
                        : "unavailable";

            }


            /* ---------------------------------------------
               BACKUP CARD
               --------------------------------------------- */

            const backupStatus =
                document.getElementById(
                    "backup-status"
                );


            if (backupStatus) {

                const backupsList =
                    backups?.backups || [];


                const completed =
                    backupsList.filter(
                        backup =>
                            String(
                                backup.status || ""
                            ).toLowerCase()
                            === "completed"
                    ).length;


                backupStatus.textContent =
                    backups
                        ? `${completed}/${backupsList.length}`
                        : "unavailable";

            }


            /* ---------------------------------------------
               INCIDENT CARD
               --------------------------------------------- */

            const incidentCount =
                document.getElementById(
                    "incident-count"
                );


            if (incidentCount) {

                incidentCount.textContent =
                    incidents
                        ? (
                            incidents.incidents || []
                        ).length
                        : "—";

            }


            /* ---------------------------------------------
               RECOVERY CARD
               --------------------------------------------- */

            const recoveryStatus =
                document.getElementById(
                    "recovery-status"
                );


            if (recoveryStatus) {

                const recoveryList =
                    recovery?.recovery_requests ||
                    [];


                const completed =
                    recoveryList.filter(
                        request =>
                            String(
                                request.status || ""
                            ).toLowerCase()
                            === "completed"
                    ).length;


                const active =
                    recoveryList.filter(
                        request => {

                            const status =
                                String(
                                    request.status || ""
                                ).toLowerCase();

                            return (
                                status === "pending" ||
                                status === "in_progress"
                            );

                        }
                    ).length;


                if (
                    active > 0
                ) {

                    recoveryStatus.textContent =
                        `${active} active`;

                } else if (
                    completed > 0
                ) {

                    recoveryStatus.textContent =
                        "completed";

                } else {

                    recoveryStatus.textContent =
                        "ready";

                }

            }


            updateLastRefresh();

        }

        catch (error) {

            console.error(
                "Dashboard summary error:",
                error
            );

        }

    }


    /* ---------------------------------------------------------
       LOAD INFRASTRUCTURE TABLE
       --------------------------------------------------------- */

    async function loadInfrastructureTable() {

        const body =
            document.getElementById(
                "infrastructure-list"
            );


        if (!body) {
            return;
        }


        try {

            const data =
                dashboardData.infrastructure ||
                await getJson(
                    "/api/v1/infrastructure"
                );


            dashboardData.infrastructure =
                data;


            const resources =
                data.resources || [];


            if (
                resources.length === 0
            ) {

                body.innerHTML = `

                    <tr>

                        <td
                            colspan="3"
                            class="empty-state">

                            No infrastructure resources registered.

                        </td>

                    </tr>

                `;

                return;

            }


            body.innerHTML =
                resources
                    .slice(0, 8)
                    .map(
                        resource => `

                            <tr>

                                <td>
                                    ${escapeHtml(
                                        resource.name
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        resource.resource_type
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="
                                            dashboard-table-status
                                            ${getStatusClass(
                                                resource.status
                                            )}
                                        ">

                                        ${escapeHtml(
                                            resource.status
                                        )}

                                    </span>

                                </td>

                            </tr>

                        `
                    )
                    .join("");

        }

        catch (error) {

            body.innerHTML = `

                <tr>

                    <td
                        colspan="3"
                        class="empty-state">

                        Unable to load infrastructure data.

                    </td>

                </tr>

            `;

        }

    }


    /* ---------------------------------------------------------
       LOAD BACKUP TABLE
       --------------------------------------------------------- */

    async function loadBackupTable() {

        const body =
            document.getElementById(
                "backup-list"
            );


        if (!body) {
            return;
        }


        try {

            const data =
                dashboardData.backups ||
                await getJson(
                    "/api/v1/backups"
                );


            dashboardData.backups =
                data;


            const backups =
                data.backups || [];


            if (
                backups.length === 0
            ) {

                body.innerHTML = `

                    <tr>

                        <td
                            colspan="3"
                            class="empty-state">

                            No backup records found.

                        </td>

                    </tr>

                `;

                return;

            }


            body.innerHTML =
                backups
                    .slice(0, 8)
                    .map(
                        backup => `

                            <tr>

                                <td>
                                    ${escapeHtml(
                                        backup.name
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        backup.backup_type ||
                                        "manual"
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="
                                            dashboard-table-status
                                            ${getStatusClass(
                                                backup.status
                                            )}
                                        ">

                                        ${escapeHtml(
                                            backup.status
                                        )}

                                    </span>

                                </td>

                            </tr>

                        `
                    )
                    .join("");

        }

        catch (error) {

            body.innerHTML = `

                <tr>

                    <td
                        colspan="3"
                        class="empty-state">

                        Unable to load backup data.

                    </td>

                </tr>

            `;

        }

    }


    /* ---------------------------------------------------------
       LOAD INCIDENT TABLE
       --------------------------------------------------------- */

    async function loadIncidentTable() {

        const body =
            document.getElementById(
                "incident-list"
            );


        if (!body) {
            return;
        }


        try {

            const data =
                dashboardData.incidents ||
                await getJson(
                    "/api/v1/incidents"
                );


            dashboardData.incidents =
                data;


            const incidents =
                data.incidents || [];


            if (
                incidents.length === 0
            ) {

                body.innerHTML = `

                    <tr>

                        <td
                            colspan="5"
                            class="empty-state">

                            No incidents have been recorded.

                        </td>

                    </tr>

                `;

                return;

            }


            body.innerHTML =
                incidents
                    .map(
                        incident => `

                            <tr>

                                <td>
                                    #${escapeHtml(
                                        incident.id
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        incident.title
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="
                                            dashboard-table-status
                                            ${getStatusClass(
                                                incident.severity
                                            )}
                                        ">

                                        ${escapeHtml(
                                            incident.severity
                                        )}

                                    </span>

                                </td>

                                <td>

                                    <span
                                        class="
                                            dashboard-table-status
                                            ${getStatusClass(
                                                incident.status
                                            )}
                                        ">

                                        ${escapeHtml(
                                            incident.status
                                        )}

                                    </span>

                                </td>

                                <td>
                                    ${escapeHtml(
                                        incident.description ||
                                        "—"
                                    )}
                                </td>

                            </tr>

                        `
                    )
                    .join("");

        }

        catch (error) {

            body.innerHTML = `

                <tr>

                    <td
                        colspan="5"
                        class="empty-state">

                        Unable to load incident data.

                    </td>

                </tr>

            `;

        }

    }


    /* ---------------------------------------------------------
       LOAD RECOVERY TABLE
       --------------------------------------------------------- */

    async function loadRecoveryTable() {

        const body =
            document.getElementById(
                "recovery-list"
            );


        if (!body) {
            return;
        }


        try {

            const data =
                dashboardData.recovery ||
                await getJson(
                    "/api/v1/recovery-requests"
                );


            dashboardData.recovery =
                data;


            const requests =
                data.recovery_requests || [];


            if (
                requests.length === 0
            ) {

                body.innerHTML = `

                    <tr>

                        <td
                            colspan="5"
                            class="empty-state">

                            No recovery requests have been recorded.

                        </td>

                    </tr>

                `;

                return;

            }


            body.innerHTML =
                requests
                    .map(
                        request => `

                            <tr>

                                <td>
                                    #${escapeHtml(
                                        request.id
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        request.resource_name ||
                                        "Unknown"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        request.recovery_type ||
                                        "Recovery"
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="
                                            dashboard-table-status
                                            ${getStatusClass(
                                                request.status
                                            )}
                                        ">

                                        ${escapeHtml(
                                            request.status
                                        )}

                                    </span>

                                </td>

                                <td>
                                    ${escapeHtml(
                                        request.reason ||
                                        "—"
                                    )}
                                </td>

                            </tr>

                        `
                    )
                    .join("");

        }

        catch (error) {

            body.innerHTML = `

                <tr>

                    <td
                        colspan="5"
                        class="empty-state">

                        Unable to load recovery data.

                    </td>

                </tr>

            `;

        }

    }


    /* ---------------------------------------------------------
       LOAD EVERYTHING
       --------------------------------------------------------- */

    async function refreshDashboard() {

        await loadDashboardSummary();

        await Promise.all([

            loadInfrastructureTable(),

            loadBackupTable(),

            loadIncidentTable(),

            loadRecoveryTable()

        ]);

    }


    /* ---------------------------------------------------------
       CARD CLICK HANDLERS
       --------------------------------------------------------- */

    infrastructureCards.forEach(
        card => {

            card.addEventListener(
                "click",
                showInfrastructureDetails
            );


            card.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();

                        showInfrastructureDetails();

                    }

                }
            );

        }
    );


    backupCards.forEach(
        card => {

            card.addEventListener(
                "click",
                showBackupDetails
            );


            card.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();

                        showBackupDetails();

                    }

                }
            );

        }
    );


    incidentCards.forEach(
        card => {

            card.addEventListener(
                "click",
                showIncidentDetails
            );


            card.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();

                        showIncidentDetails();

                    }

                }
            );

        }
    );


    recoveryCards.forEach(
        card => {

            card.addEventListener(
                "click",
                showRecoveryDetails
            );


            card.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();

                        showRecoveryDetails();

                    }

                }
            );

        }
    );


    /* ---------------------------------------------------------
       MODAL CLOSE BUTTONS
       --------------------------------------------------------- */

    if (modalClose) {

        modalClose.addEventListener(
            "click",
            closeModal
        );

    }


    if (modalCloseFooter) {

        modalCloseFooter.addEventListener(
            "click",
            closeModal
        );

    }


    if (modal) {

        modal.addEventListener(
            "click",
            event => {

                if (
                    event.target === modal
                ) {

                    closeModal();

                }

            }
        );

    }


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Escape" &&
                modal &&
                modal.classList.contains("active")
            ) {

                closeModal();

            }

        }
    );


    /* ---------------------------------------------------------
       MODAL ACTION BUTTON
       --------------------------------------------------------- */

    if (modalAction) {

        modalAction.addEventListener(
            "click",
            function () {

                if (
                    !currentActionTab
                ) {
                    return;
                }


                const tabId =
                    currentActionTab;


                closeModal();


                const trigger =
                    document.querySelector(
                        `[data-tab-target="${tabId}"]`
                    );


                if (trigger) {

                    trigger.click();

                }

            }
        );

    }


    /* ---------------------------------------------------------
       REFRESH BUTTONS
       --------------------------------------------------------- */

    const incidentRefresh =
        document.getElementById(
            "incident-refresh-button"
        );


    if (incidentRefresh) {

        incidentRefresh.addEventListener(
            "click",
            async function () {

                await loadDashboardSummary();

                await loadIncidentTable();

                updateLastRefresh();

            }
        );

    }


    const recoveryRefresh =
        document.getElementById(
            "recovery-refresh-button"
        );


    if (recoveryRefresh) {

        recoveryRefresh.addEventListener(
            "click",
            async function () {

                await loadDashboardSummary();

                await loadRecoveryTable();

                updateLastRefresh();

            }
        );

    }


    /* ---------------------------------------------------------
       INITIAL LOAD
       --------------------------------------------------------- */

    refreshDashboard();


    /* ---------------------------------------------------------
       PERIODIC REFRESH
       --------------------------------------------------------- */

    setInterval(
        refreshDashboard,
        60000
    );

});