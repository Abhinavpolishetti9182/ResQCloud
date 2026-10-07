/**
 * ============================================================
 * RESQCLOUD — DASHBOARD TAB NAVIGATION
 * ============================================================
 *
 * Handles:
 * - Sidebar navigation
 * - Dashboard tab switching
 * - Page title / description updates
 * - Active navigation state
 *
 * Monitoring is now a separate sidebar tab.
 * ============================================================
 */

(function () {
    "use strict";

    /**
     * ----------------------------------------------------------
     * TAB INFORMATION
     * ----------------------------------------------------------
     */

    const TAB_INFO = {

        "dashboard-tab": {
            title: "Dashboard",
            description:
                "Overview of your ResQCloud backup, recovery, incidents, and cloud infrastructure."
        },

        "monitoring-tab": {
            title: "CloudWatch Monitoring",
            description:
                "View live AWS EC2 CPU, memory, disk, and network metrics."
        },

        "backup-management": {
            title: "Backup Management",
            description:
                "Manage and monitor your AWS backup operations."
        },

        "recovery-management": {
            title: "Recovery",
            description:
                "Restore applications and data from available backups."
        },

        "incident-management": {
            title: "Incident Management",
            description:
                "View, investigate, and manage cloud infrastructure incidents."
        },

        "audit-logs": {
            title: "Audit Logs",
            description:
                "Review system activity and security-related events."
        },

        "settings": {
            title: "Settings",
            description:
                "Configure ResQCloud application and cloud integration settings."
        }
    };


    /**
     * ----------------------------------------------------------
     * DOM ELEMENTS
     * ----------------------------------------------------------
     */

    const pageTitle = document.getElementById("page-title");
    const pageDescription = document.getElementById("page-description");

    const navItems = document.querySelectorAll(
        ".nav-item[data-tab-target]"
    );

    const tabPanels = document.querySelectorAll(
        ".tab-panel"
    );


    /**
     * ----------------------------------------------------------
     * UPDATE PAGE HEADER
     * ----------------------------------------------------------
     */

    function updatePageHeader(tabId) {

        const info = TAB_INFO[tabId];

        if (!info) {
            return;
        }

        if (pageTitle) {
            pageTitle.textContent = info.title;
        }

        if (pageDescription) {
            pageDescription.textContent = info.description;
        }
    }


    /**
     * ----------------------------------------------------------
     * SHOW TAB
     * ----------------------------------------------------------
     */

    function showTab(tabId) {

        if (!tabId) {
            return;
        }

        /**
         * Hide all tab panels
         */
        tabPanels.forEach(function (panel) {

            panel.classList.remove("active");

            panel.style.display = "none";

        });


        /**
         * Show requested tab
         */
        const selectedPanel = document.getElementById(tabId);

        if (!selectedPanel) {
            console.warn(
                "ResQCloud: Tab not found:",
                tabId
            );

            return;
        }

        selectedPanel.classList.add("active");

        selectedPanel.style.display = "";


        /**
         * Update sidebar active state
         */
        navItems.forEach(function (navItem) {

            const target =
                navItem.getAttribute("data-tab-target");

            navItem.classList.toggle(
                "active",
                target === tabId
            );

        });


        /**
         * Update page title and description
         */
        updatePageHeader(tabId);


        /**
         * Update URL hash
         */
        if (window.location.hash !== "#" + tabId) {

            history.replaceState(
                null,
                "",
                "#" + tabId
            );

        }


        /**
         * Dispatch custom event.
         *
         * Other ResQCloud modules can listen for this event
         * when a particular dashboard section becomes active.
         */
        document.dispatchEvent(
            new CustomEvent(
                "resqcloud:tab-changed",
                {
                    detail: {
                        tabId: tabId
                    }
                }
            )
        );
    }


    /**
     * ----------------------------------------------------------
     * NAVIGATION CLICK HANDLER
     * ----------------------------------------------------------
     */

    navItems.forEach(function (navItem) {

        navItem.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                const tabId =
                    navItem.getAttribute(
                        "data-tab-target"
                    );

                if (tabId) {
                    showTab(tabId);
                }

            }
        );

    });


    /**
     * ----------------------------------------------------------
     * HASH NAVIGATION
     * ----------------------------------------------------------
     *
     * Example:
     *
     * #dashboard-tab
     * #monitoring-tab
     * #backup-management
     *
     * This allows the browser URL to directly open
     * a specific dashboard section.
     */

    function loadTabFromHash() {

        const hash =
            window.location.hash.replace(
                "#",
                ""
            );

        if (
            hash &&
            document.getElementById(hash)
        ) {

            showTab(hash);

        } else {

            /**
             * Default tab
             */
            showTab("dashboard-tab");

        }
    }


    /**
     * ----------------------------------------------------------
     * BROWSER BACK / FORWARD
     * ----------------------------------------------------------
     */

    window.addEventListener(
        "hashchange",
        function () {

            loadTabFromHash();

        }
    );


    /**
     * ----------------------------------------------------------
     * INITIALIZE DASHBOARD
     * ----------------------------------------------------------
     */

    function initializeDashboardTabs() {

        loadTabFromHash();

    }


    /**
     * ----------------------------------------------------------
     * DOM READY
     * ----------------------------------------------------------
     */

    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeDashboardTabs
        );

    } else {

        initializeDashboardTabs();

    }


    /**
     * ----------------------------------------------------------
     * PUBLIC API
     * ----------------------------------------------------------
     *
     * Other JavaScript files can use:
     *
     * window.ResQCloudTabs.show("monitoring-tab");
     *
     */

    window.ResQCloudTabs = {

        show: showTab,

        getCurrentTab: function () {

            const activePanel =
                document.querySelector(
                    ".tab-panel.active"
                );

            return activePanel
                ? activePanel.id
                : null;
        }

    };

})();