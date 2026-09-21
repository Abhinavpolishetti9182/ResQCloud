
async function fetchJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    return await response.json();
}


/*
 * Load infrastructure information
 */
async function loadInfrastructure() {
    const statusElement = document.getElementById("infrastructure-status");
    const listElement = document.getElementById("infrastructure-list");

    try {
        const data = await fetchJSON("/api/v1/infrastructure");

        statusElement.textContent = data.status.toUpperCase();

        listElement.innerHTML = "";

        if (!data.resources || data.resources.length === 0) {
            listElement.innerHTML = `
                <p class="loading-message">
                    No infrastructure resources found.
                </p>
            `;
            return;
        }

        data.resources.forEach(resource => {
            const resourceElement = document.createElement("div");

            resourceElement.className = "resource-item";

            resourceElement.innerHTML = `
                <div>
                    <div class="resource-name">
                        ${resource.name}
                    </div>

                    <div class="resource-type">
                        Type: ${resource.type}
                    </div>
                </div>

                <div class="resource-status">
                    ${resource.status}
                </div>
            `;

            listElement.appendChild(resourceElement);
        });

    } catch (error) {
        console.error("Infrastructure error:", error);

        statusElement.textContent = "ERROR";

        listElement.innerHTML = `
            <p class="error-message">
                Unable to load infrastructure data.
            </p>
        `;
    }
}


/*
 * Load backup information
 */
async function loadBackups() {
    const statusElement = document.getElementById("backup-status");
    const listElement = document.getElementById("backup-list");

    try {
        const data = await fetchJSON("/api/v1/backups");

        statusElement.textContent = data.status.toUpperCase();

        listElement.innerHTML = "";

        if (!data.backups || data.backups.length === 0) {
            listElement.innerHTML = `
                <div class="backup-item">
                    <div>
                        <div class="backup-name">
                            No backups available
                        </div>

                        <div class="backup-description">
                            Backup records will appear here.
                        </div>
                    </div>

                    <div class="resource-status">
                        Pending
                    </div>
                </div>
            `;

            return;
        }

        data.backups.forEach(backup => {
            const backupElement = document.createElement("div");

            backupElement.className = "backup-item";

            backupElement.innerHTML = `
                <div>
                    <div class="backup-name">
                        ${backup.name}
                    </div>

                    <div class="backup-description">
                        ${backup.description}
                    </div>
                </div>

                <div class="resource-status">
                    ${backup.status}
                </div>
            `;

            listElement.appendChild(backupElement);
        });

    } catch (error) {
        console.error("Backup error:", error);

        statusElement.textContent = "ERROR";

        listElement.innerHTML = `
            <p class="error-message">
                Unable to load backup data.
            </p>
        `;
    }
}


/*
 * Update the dashboard timestamp
 */
function updateTimestamp() {
    const timestampElement = document.getElementById("last-updated");

    const currentTime = new Date();

    timestampElement.textContent =
        `Last updated: ${currentTime.toLocaleString()}`;
}


/*
 * Load all dashboard information
 */
async function loadDashboard() {
    await Promise.all([
        loadInfrastructure(),
        loadBackups()
    ]);

    updateTimestamp();
}


/*
 * Start the dashboard after the page loads
 */
document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});