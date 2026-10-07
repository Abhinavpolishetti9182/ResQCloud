(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {

        /* =========================================================
           RUNBOOK ELEMENTS
           ========================================================= */

        const incidentInput =
            document.getElementById("runbook-incident-id");

        const loadIncidentButton =
            document.getElementById("runbook-load-incident");

        const message =
            document.getElementById("runbook-message");

        const selectedIncident =
            document.getElementById("runbook-selected-incident");

        const diagnosisStatus =
            document.getElementById("runbook-diagnosis-status");

        const evidenceStatus =
            document.getElementById("runbook-evidence-status");

        const recoveryStatus =
            document.getElementById("runbook-recovery-status");

        const approvalStatus =
            document.getElementById("runbook-approval-status");

        const validationStatus =
            document.getElementById("runbook-validation-status");

        const closeStatus =
            document.getElementById("runbook-close-status");

        const procedureStatus =
            document.getElementById("runbook-procedure-status");

        const diagnoseButton =
            document.getElementById("runbook-diagnose-button");

        const evidenceButton =
            document.getElementById("runbook-evidence-button");

        const approvalButton =
            document.getElementById("runbook-approval-button");

        const recoveryButton =
            document.getElementById("runbook-recovery-button");


        /* =========================================================
           MESSAGE HELPER
           ========================================================= */

        function setMessage(text, type = "info") {

            if (!message) {
                return;
            }

            message.textContent = text;

            message.dataset.status = type;
        }


        /* =========================================================
           STATUS HELPER
           ========================================================= */

        function setStatus(element, text, type = "") {

            if (!element) {
                return;
            }

            element.textContent = text;

            element.className = "dashboard-detail-status";

            if (type) {
                element.classList.add(type);
            }
        }


        /* =========================================================
           GET INCIDENT ID
           ========================================================= */

        function getIncidentId() {

            if (!incidentInput) {
                return null;
            }

            const value = incidentInput.value.trim();

            if (!value) {
                return null;
            }

            const incidentId =
                Number.parseInt(value, 10);

            if (
                !Number.isInteger(incidentId) ||
                incidentId <= 0
            ) {
                return null;
            }

            return incidentId;
        }


        /* =========================================================
           RESET RUNBOOK
           ========================================================= */

        function resetRunbook() {

            setStatus(
                selectedIncident,
                "None"
            );

            setStatus(
                diagnosisStatus,
                "Not Started"
            );

            setStatus(
                evidenceStatus,
                "Not Collected"
            );

            setStatus(
                recoveryStatus,
                "Not Started"
            );

            setStatus(
                approvalStatus,
                "Approval Required",
                "warning"
            );

            setStatus(
                validationStatus,
                "Waiting"
            );

            setStatus(
                closeStatus,
                "Waiting"
            );

            setStatus(
                procedureStatus,
                "Procedure Ready"
            );
        }


        /* =========================================================
           LOAD INCIDENT
           ========================================================= */

        if (loadIncidentButton) {

            loadIncidentButton.addEventListener(
                "click",
                () => {

                    const incidentId =
                        getIncidentId();

                    if (!incidentId) {

                        setMessage(
                            "Please enter a valid incident ID.",
                            "error"
                        );

                        resetRunbook();

                        return;
                    }


                    /*
                     * Show selected incident
                     */

                    setStatus(
                        selectedIncident,
                        `#${incidentId}`,
                        "success"
                    );


                    /*
                     * Reset workflow for selected incident
                     */

                    setStatus(
                        diagnosisStatus,
                        "Ready"
                    );

                    setStatus(
                        evidenceStatus,
                        "Ready"
                    );

                    setStatus(
                        recoveryStatus,
                        "Waiting"
                    );

                    setStatus(
                        approvalStatus,
                        "Approval Required",
                        "warning"
                    );

                    setStatus(
                        validationStatus,
                        "Waiting"
                    );

                    setStatus(
                        closeStatus,
                        "Waiting"
                    );

                    setStatus(
                        procedureStatus,
                        "Procedure Ready"
                    );


                    setMessage(
                        `Incident #${incidentId} loaded into the response runbook.`,
                        "success"
                    );
                }
            );
        }


        /* =========================================================
           DIAGNOSE
           ========================================================= */

        if (diagnoseButton) {

            diagnoseButton.addEventListener(
                "click",
                () => {

                    const incidentId =
                        getIncidentId();

                    if (!incidentId) {

                        setMessage(
                            "Load an incident before starting diagnosis.",
                            "error"
                        );

                        return;
                    }


                    setStatus(
                        diagnosisStatus,
                        "Diagnosed",
                        "success"
                    );


                    setStatus(
                        procedureStatus,
                        "Procedure Selected",
                        "success"
                    );


                    setMessage(
                        `Diagnosis stage completed for incident #${incidentId}. Review the affected resource before continuing.`,
                        "success"
                    );
                }
            );
        }


        /* =========================================================
           EVIDENCE COLLECTION
           ========================================================= */

        if (evidenceButton) {

            evidenceButton.addEventListener(
                "click",
                () => {

                    const incidentId =
                        getIncidentId();

                    if (!incidentId) {

                        setMessage(
                            "Load an incident before collecting evidence.",
                            "error"
                        );

                        return;
                    }


                    setStatus(
                        evidenceStatus,
                        "Collected",
                        "success"
                    );


                    setMessage(
                        `Evidence collection recorded for incident #${incidentId}.`,
                        "success"
                    );
                }
            );
        }


        /* =========================================================
           APPROVAL
           ========================================================= */

        if (approvalButton) {

            approvalButton.addEventListener(
                "click",
                () => {

                    const incidentId =
                        getIncidentId();

                    if (!incidentId) {

                        setMessage(
                            "Load an incident before approving recovery.",
                            "error"
                        );

                        return;
                    }


                    setStatus(
                        approvalStatus,
                        "Approved",
                        "success"
                    );


                    setMessage(
                        `Recovery approval recorded for incident #${incidentId}.`,
                        "success"
                    );
                }
            );
        }


        /* =========================================================
           RECOVERY
           ========================================================= */

        if (recoveryButton) {

            recoveryButton.addEventListener(
                "click",
                () => {

                    const incidentId =
                        getIncidentId();

                    if (!incidentId) {

                        setMessage(
                            "Load an incident before starting recovery.",
                            "error"
                        );

                        return;
                    }


                    /*
                     * Recovery requires approval
                     */

                    const approved =
                        approvalStatus &&
                        approvalStatus.textContent
                            .trim()
                            .toLowerCase() === "approved";


                    if (!approved) {

                        setMessage(
                            "Recovery cannot start until operator approval is granted.",
                            "error"
                        );

                        return;
                    }


                    /*
                     * Mark recovery as ready
                     */

                    setStatus(
                        recoveryStatus,
                        "Ready",
                        "success"
                    );


                    setStatus(
                        validationStatus,
                        "Pending"
                    );


                    setMessage(
                        `Recovery workflow is ready for incident #${incidentId}. The actual Recovery Engine integration will execute the restore operation.`,
                        "success"
                    );
                }
            );
        }


        /* =========================================================
           INITIAL STATE
           ========================================================= */

        resetRunbook();

    });

})();