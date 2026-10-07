(() => {
    const form = document.getElementById("backup-upload-form");
    const fileInput = document.getElementById("backup-file");
    const uploadButton = document.getElementById("backup-upload-button");
    const refreshButton = document.getElementById("backup-refresh-button");
    const historyBody = document.getElementById("backup-history-body");
    const message = document.getElementById("backup-message");

    if (!form || !fileInput || !historyBody || !message) {
        return;
    }

    function showMessage(text, isError = false) {
        message.textContent = text;
        message.style.color = isError ? "#b91c1c" : "#166534";
    }

    async function apiRequest(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.message || `Request failed: HTTP ${response.status}`
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

    async function restoreBackup(id, button) {
        button.disabled = true;
        button.textContent = "Restoring...";

        try {
            const result = await apiRequest(
                `/api/v1/backups/${encodeURIComponent(id)}/restore`,
                {
                    method: "POST"
                }
            );

            showMessage(
                result.success
                    ? `Backup ${id} restored and integrity verified successfully.`
                    : `Backup ${id} could not be restored.`,
                !result.success
            );

            await loadHistory();
        } catch (error) {
            showMessage(
                `Restore failed: ${error.message}`,
                true
            );
        } finally {
            button.disabled = false;
            button.textContent = "Restore & Verify";
        }
    }

    async function loadHistory() {
        historyBody.replaceChildren();

        const loadingRow = document.createElement("tr");
        const loadingCell = addCell(
            loadingRow,
            "Loading backup history..."
        );
        loadingCell.colSpan = 5;
        historyBody.appendChild(loadingRow);

        try {
            const data = await apiRequest("/api/v1/backups");

            const backups = Array.isArray(data)
                ? data
                : (data.backups || data.data || []);

            historyBody.replaceChildren();

            if (!backups.length) {
                const row = document.createElement("tr");
                const cell = addCell(row, "No backups found.");
                cell.colSpan = 5;
                historyBody.appendChild(row);
                return;
            }

            for (const backup of backups) {
                const row = document.createElement("tr");

                addCell(row, backup.id);
                addCell(row, backup.name);
                addCell(row, backup.status);
                addCell(row, backup.storage_location);

                const actionCell = document.createElement("td");
                const button = document.createElement("button");

                button.type = "button";
                button.className = "button button-small";
                button.textContent = "Restore & Verify";

                button.addEventListener("click", () => {
                    restoreBackup(backup.id, button);
                });

                actionCell.appendChild(button);
                row.appendChild(actionCell);
                historyBody.appendChild(row);
            }
        } catch (error) {
            historyBody.replaceChildren();

            const row = document.createElement("tr");
            const cell = addCell(row, error.message);
            cell.colSpan = 5;
            historyBody.appendChild(row);

            showMessage(
                "Could not load backup history: " + error.message,
                true
            );
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const file = fileInput.files[0];

        if (!file) {
            showMessage("Choose a file first.", true);
            return;
        }

        if (file.size === 0 || file.size > 25 * 1024 * 1024) {
            showMessage(
                "Choose a non-empty file no larger than 25 MiB.",
                true
            );
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        uploadButton.disabled = true;
        showMessage("Uploading backup to AWS S3...");

        try {
            const result = await apiRequest(
                "/api/v1/backups/upload-file",
                {
                    method: "POST",
                    body: formData
                }
            );

            showMessage(
                `Backup ${result.backup.id} uploaded successfully.`
            );

            form.reset();
            await loadHistory();
        } catch (error) {
            showMessage(
                "Upload failed: " + error.message,
                true
            );
        } finally {
            uploadButton.disabled = false;
        }
    });

    refreshButton?.addEventListener(
        "click",
        loadHistory
    );

    loadHistory();
})();