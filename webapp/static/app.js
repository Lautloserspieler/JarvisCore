const dom = {
    chatLog: document.getElementById("chat-log"),
    statusBadge: document.getElementById("assistant-status"),
    form: document.getElementById("command-form"),
    input: document.getElementById("command-input"),
    sendButton: document.getElementById("send-button"),
    cpu: document.getElementById("cpu-usage"),
    ram: document.getElementById("ram-usage"),
    disk: document.getElementById("disk-usage"),
    gpuLoad: document.getElementById("gpu-load"),
    gpuMem: document.getElementById("gpu-mem"),
    cpuFreq: document.getElementById("cpu-freq"),
    ramFree: document.getElementById("ram-free"),
    uptime: document.getElementById("uptime-value"),
    uptimeBoot: document.getElementById("uptime-boot"),
    contextList: document.getElementById("context-list"),
    pluginContext: document.getElementById("plugin-context"),
    logOutput: document.getElementById("log-output"),
    refreshLogs: document.getElementById("refresh-logs"),
    logSearch: document.getElementById("log-search"),
    logLines: document.getElementById("log-lines"),
    knowledgeFeed: document.getElementById("knowledge-feed"),
    tokenInput: document.getElementById("auth-token"),
    tokenToggle: document.getElementById("auth-token-toggle"),
    tokenError: document.getElementById("auth-token-error"),
    commandHistory: document.getElementById("command-history"),
    ttsStreamToggle: document.getElementById("tts-stream-toggle"),
    busyOverlay: document.getElementById("busy-overlay"),
    toastContainer: document.getElementById("toast-container"),
    wsIndicator: document.getElementById("ws-indicator"),
    securityOverlay: document.getElementById("security-overlay"),
    securityMessage: document.getElementById("security-message"),
    securityForm: document.getElementById("security-form"),
    securityInput: document.getElementById("security-input"),
    securityCancel: document.getElementById("security-cancel"),
    networkTable: document.querySelector("#network-table tbody"),
    diskTable: document.querySelector("#disk-table tbody"),
    systemInfo: document.getElementById("system-info"),
    speedtest: document.getElementById("speedtest-btn"),
    modelList: document.getElementById("model-overview"),
    modelActions: document.querySelectorAll(".model-actions button"),
    currentModelLabel: document.getElementById("current-model-label"),
    modelMetadata: document.getElementById("model-metadata"),
    pluginTable: document.querySelector("#plugin-table tbody"),
    pluginDetails: document.getElementById("plugin-details"),
    refreshPlugins: document.getElementById("refresh-plugins"),
    trainingLog: document.getElementById("training-log"),
    topCommands: document.getElementById("top-commands"),
    reinforcementInfo: document.getElementById("reinforcement-info"),
    runTraining: document.getElementById("run-training"),
    audioDeviceSelect: document.getElementById("audio-device-select"),
    refreshAudioDevices: document.getElementById("refresh-audio-devices"),
    measureAudio: document.getElementById("measure-audio"),
    audioLevelLabel: document.getElementById("audio-level-label"),
    speechForm: document.getElementById("speech-form"),
    audioForm: document.getElementById("audio-form"),
    webForm: document.getElementById("web-form"),
    systemForm: document.getElementById("system-form"),
    knowledgeStats: document.getElementById("knowledge-stats"),
    customCommandForm: document.getElementById("custom-command-form"),
    customCommandPattern: document.getElementById("custom-command-pattern"),
    customCommandResponse: document.getElementById("custom-command-response"),
    commandsTable: document.querySelector("#commands-table tbody"),
    clearLogs: document.getElementById("clear-logs"),
    speechToggleBtn: document.getElementById("speech-toggle-btn"),
    wakeWordToggle: document.getElementById("wake-word-toggle"),
    speechControlStatus: document.getElementById("speech-control-status"),
    speechModeLabel: document.getElementById("speech-mode-label"),
    memorySummary: document.getElementById("memory-summary"),
    memoryTopics: document.getElementById("memory-topics"),
    memoryContext: document.getElementById("memory-context"),
    memoryMessages: document.getElementById("memory-messages"),
    memoryTimeline: document.getElementById("memory-timeline"),
    memorySearchResults: document.getElementById("memory-search-results"),
    memorySearchForm: document.getElementById("memory-search"),
    memoryQuery: document.getElementById("memory-query"),
    modelProgressWrapper: document.getElementById("model-download-progress"),
    modelProgressBar: document.querySelector("#model-download-progress .model-progress-track-bar"),
    modelProgressLabel: document.getElementById("model-download-progress-label"),
    tabNav: document.querySelector(".tab-nav"),
    tabContainer: document.querySelector(".tab-container"),
    crawlerPanel: document.getElementById("panel-crawler"),
    crawlerRefresh: document.getElementById("crawler-refresh"),
    crawlerSyncNow: document.getElementById("crawler-sync-now"),
    crawlerControlPause: document.getElementById("crawler-control-pause"),
    crawlerControlResume: document.getElementById("crawler-control-resume"),
    crawlerConnectionLabel: document.getElementById("crawler-connection-label"),
    crawlerWorkerCount: document.getElementById("crawler-worker-count"),
    crawlerLastSync: document.getElementById("crawler-last-sync"),
    crawlerDocTotal: document.getElementById("crawler-doc-total"),
    crawlerDoc24h: document.getElementById("crawler-doc-24h"),
    crawlerDocSince: document.getElementById("crawler-doc-since"),
    crawlerOpenJobs: document.getElementById("crawler-open-jobs"),
    crawlerRunningCount: document.getElementById("crawler-running-count"),
    crawlerCpuUsage: document.getElementById("crawler-cpu-usage"),
    crawlerStatusNote: document.getElementById("crawler-status-note"),
    crawlerAutoSync: document.getElementById("crawler-auto-sync"),
    crawlerJobForm: document.getElementById("crawler-job-form"),
    crawlerJobTopic: document.getElementById("crawler-job-topic"),
    crawlerJobUrls: document.getElementById("crawler-job-urls"),
    crawlerJobPages: document.getElementById("crawler-job-pages"),
    crawlerJobDepth: document.getElementById("crawler-job-depth"),
    crawlerJobProfile: document.getElementById("crawler-job-profile"),
    crawlerJobFeedback: document.getElementById("crawler-job-feedback"),
    crawlerRunningTable: document.getElementById("crawler-running-table"),
    crawlerCompletedTable: document.getElementById("crawler-completed-table"),
    crawlerSyncSummary: document.getElementById("crawler-sync-summary"),
    crawlerSyncSummaryCard: document.getElementById("crawler-sync-summary-card"),
    crawlerSyncDocs: document.getElementById("crawler-sync-docs"),
    crawlerSyncTotal: document.getElementById("crawler-sync-total"),
    crawlerSyncTotalCard: document.getElementById("crawler-sync-total-card"),
    crawlerDocumentsList: document.getElementById("crawler-documents-list"),
    crawlerRecentDocs: document.getElementById("crawler-recent-docs"),
    crawlerConfigForm: document.getElementById("crawler-config-form"),
    crawlerDomains: document.getElementById("crawler-domains"),
    crawlerRateLimit: document.getElementById("crawler-rate-limit"),
    crawlerRobots: document.getElementById("crawler-robots"),
    crawlerMaxWorkers: document.getElementById("crawler-max-workers"),
    crawlerMaxCpu: document.getElementById("crawler-max-cpu"),
    crawlerMaxRam: document.getElementById("crawler-max-ram"),
    crawlerMaxPages: document.getElementById("crawler-max-pages"),
    crawlerMaxDepth: document.getElementById("crawler-max-depth"),
    crawlerBaseUrl: document.getElementById("crawler-base-url"),
    crawlerApiKey: document.getElementById("crawler-api-key"),
    crawlerSyncInterval: document.getElementById("crawler-sync-interval"),
    crawlerSaveConfig: document.getElementById("crawler-save-config"),
    crawlerRestartBtn: document.getElementById("crawler-restart-btn"),
    crawlerSecurityRole: document.getElementById("crawler-security-role"),
    crawlerSecurityKey: document.getElementById("crawler-security-key"),
    crawlerSecurityDomain: document.getElementById("crawler-security-domain"),
    crawlerSecuritySafe: document.getElementById("crawler-security-safe"),
    crawlerSafeAllow: document.getElementById("crawler-safe-allow"),
    crawlerSafeBlock: document.getElementById("crawler-safe-block"),
    crawlerAlerts: document.getElementById("crawler-alerts"),
    crawlerSyncBtn: document.getElementById("crawler-sync-btn"),
};

const state = {
    ws: null,
    reconnectTimer: null,
    historyLoaded: false,
    knowledgeEntries: [],
    activeTab: "chat",
    models: {},
    selectedModel: null,
    modelDownloads: {},
    speech: null,
    commandHistory: [],
    tts: { stream_enabled: true },
    pendingRequests: 0,
    plugins: [],
    selectedPlugin: null,
    memorySnapshot: {},
    memoryQuery: "",
    lastAppliedToken: "",
    tokenSyncTimer: null,
    crawler: {
        status: null,
        documents: [],
        alerts: [],
        refreshTimer: null,
        jobCache: {},
    },
};

function ensureAssistantView() {
    const chatPanel = document.getElementById("panel-chat");
    if (!chatPanel) return;
    const sidebar = chatPanel.querySelector(".context-panel");
    if (!sidebar) return;

    const tabContainer = dom.tabContainer || document.querySelector(".tab-container");
    if (!tabContainer) return;

    let assistantPanel = document.getElementById("panel-assistant");
    if (!assistantPanel) {
        assistantPanel = document.createElement("section");
        assistantPanel.className = "tab-panel";
        assistantPanel.dataset.panel = "assistant";
        assistantPanel.id = "panel-assistant";
        assistantPanel.setAttribute("role", "tabpanel");
        assistantPanel.setAttribute("aria-labelledby", "tab-assistant");
        assistantPanel.setAttribute("tabindex", "0");
        assistantPanel.hidden = true;
        const systemPanel = document.getElementById("panel-system");
        tabContainer.insertBefore(assistantPanel, systemPanel || tabContainer.firstElementChild?.nextElementSibling || null);
    }

    if (!assistantPanel.contains(sidebar)) {
        sidebar.remove();
        assistantPanel.appendChild(sidebar);
    }

    let assistantButton = document.getElementById("tab-assistant");
    if (!assistantButton && dom.tabNav) {
        assistantButton = document.createElement("button");
        assistantButton.type = "button";
        assistantButton.id = "tab-assistant";
        assistantButton.dataset.tab = "assistant";
        assistantButton.textContent = "Assistenz";
        assistantButton.role = "tab";
        assistantButton.setAttribute("aria-selected", "false");
        assistantButton.setAttribute("aria-controls", "panel-assistant");
        assistantButton.tabIndex = -1;
        const systemButton = document.getElementById("tab-system");
        dom.tabNav.insertBefore(assistantButton, systemButton || dom.tabNav.firstChild);
    }
}

function collectFormValues(form) {
    const data = {};
    Array.from(form.elements).forEach((element) => {
        if (!element.name) {
            return;
        }
        if (element.type === "checkbox") {
            data[element.name] = element.checked;
        } else if (element.type === "number") {
            const value = element.value;
            data[element.name] = value === "" ? null : Number(value);
        } else if (element.tagName === "SELECT") {
            data[element.name] = element.value;
        } else {
            data[element.name] = element.value;
        }
    });
    return data;
}

function authHeaders() {
    const token = dom.tokenInput.value.trim();
    return token ? { "X-Auth-Token": token } : {};
}

function persistToken() {
    const value = dom.tokenInput.value.trim();
    if (value) {
        localStorage.setItem("jarvisWebToken", value);
    } else {
        localStorage.removeItem("jarvisWebToken");
    }
}

function setTokenError(message) {
    if (!dom.tokenError) return;
    const wrapper = dom.tokenError.closest(".token-field");
    if (message) {
        dom.tokenError.textContent = message;
        dom.tokenError.classList.remove("hidden");
        if (wrapper) wrapper.classList.add("has-error");
    } else {
        dom.tokenError.textContent = "";
        dom.tokenError.classList.add("hidden");
        if (wrapper) wrapper.classList.remove("has-error");
    }
}

function handleAuthStatus(status, message) {
    if (status === 401) {
        setTokenError(message || "Nicht autorisiert. Bitte Token ueberpruefen.");
        return true;
    }
    if (status === null) {
        setTokenError("");
    }
    return false;
}

function escapeHtml(value) {
    return (value ?? "")
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function renderMarkdown(text) {
    const placeholders = [];
    let html = escapeHtml(text || "");
    html = html.replace(/```([\s\S]*?)```/g, (_, code) => {
        const idx = placeholders.length;
        const normalized = escapeHtml(code).replace(/\n/g, "<br>");
        placeholders.push(`<pre><code>${normalized}</code></pre>`);
        return `__CODE_BLOCK_${idx}__`;
    });
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    const lines = html.replace(/\r\n?/g, "\n").split("\n");
    const output = [];
    let listBuffer = [];

    const flushList = () => {
        if (!listBuffer.length) return;
        output.push(`<ul>${listBuffer.join("")}</ul>`);
        listBuffer = [];
    };

    for (const line of lines) {
        if (/^\s*-\s+/.test(line)) {
            const item = line.replace(/^\s*-\s+/, "");
            listBuffer.push(`<li>${item}</li>`);
            continue;
        }
        flushList();
        if (!line.trim()) {
            continue;
        }
        if (/__CODE_BLOCK_\d+__/.test(line)) {
            output.push(line);
            continue;
        }
        output.push(`<p>${line}</p>`);
    }
    flushList();
    let result = output.filter(Boolean).join("");
    placeholders.forEach((snippet, idx) => {
        result = result.replace(`__CODE_BLOCK_${idx}__`, snippet);
    });
    return result || "";
}

function truncateText(text, maxLength = 80) {
    if (!text) return "";
    const normalized = text.trim();
    return normalized.length > maxLength ? `${normalized.slice(0, maxLength - 1)}…` : normalized;
}

function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "–";
    }
    return new Intl.NumberFormat("de-DE").format(Number(value));
}

function formatDuration(seconds) {
    if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
        return null;
    }
    const totalSeconds = Math.max(0, Math.round(Number(seconds)));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    if (hours > 0) {
        return `${hours}h ${minutes.toString().padStart(2, "0")}m`;
    }
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

function formatRelativeTime(value) {
    if (!value) return "–";
    try {
        const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);
        const diff = Date.now() - date.getTime();
        if (Number.isNaN(diff)) return date.toLocaleString();
        const minutes = Math.floor(diff / 60000);
        if (minutes < 1) return "gerade eben";
        if (minutes === 1) return "vor einer Minute";
        if (minutes < 60) return `vor ${minutes} Minuten`;
        const hours = Math.floor(minutes / 60);
        if (hours === 1) return "vor einer Stunde";
        if (hours < 24) return `vor ${hours} Stunden`;
        const days = Math.floor(hours / 24);
        if (days === 1) return "gestern";
        return `vor ${days} Tagen`;
    } catch (error) {
        return "–";
    }
}

function updateBusyOverlay() {
    if (!dom.busyOverlay) return;
    if ((state.pendingRequests || 0) > 0) {
        dom.busyOverlay.classList.remove("hidden");
    } else {
        dom.busyOverlay.classList.add("hidden");
    }
}

function beginRequest() {
    state.pendingRequests = (state.pendingRequests || 0) + 1;
    updateBusyOverlay();
}

function endRequest() {
    state.pendingRequests = Math.max(0, (state.pendingRequests || 1) - 1);
    updateBusyOverlay();
}

function showToast(message, type = "info", options = {}) {
    if (!dom.toastContainer || !message) return;
    const duration = typeof options.duration === "number" ? options.duration : 4000;
    const title = options.title || (type === "error" ? "Fehler" : type === "success" ? "Erfolg" : "Hinweis");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const titleEl = document.createElement("div");
    titleEl.className = "title";
    titleEl.textContent = title;
    toast.appendChild(titleEl);

    const bodyEl = document.createElement("div");
    bodyEl.textContent = message;
    toast.appendChild(bodyEl);

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.textContent = "Schliessen";

    const removeToast = () => {
        toast.classList.add("hidden");
        setTimeout(() => {
            toast.remove();
        }, 200);
    };

    closeBtn.addEventListener("click", removeToast);
    toast.appendChild(closeBtn);

    dom.toastContainer.appendChild(toast);

    if (duration > 0) {
        setTimeout(removeToast, duration);
    }
}

async function apiFetch(url, options = {}) {
    const init = { ...options };
    const headers = {
        ...authHeaders(),
        ...(options.headers || {}),
    };
    init.headers = headers;
    beginRequest();
    try {
        let response;
        try {
            response = await fetch(url, init);
        } catch (networkError) {
            showToast(networkError.message || "Netzwerkfehler", "error", { title: "Netzwerk" });
            throw networkError;
        }

        const contentType = response.headers.get("content-type") || "";
        let payload;
        if (contentType.includes("application/json")) {
            try {
                payload = await response.json();
            } catch {
                payload = {};
            }
        } else {
            try {
                payload = await response.text();
            } catch {
                payload = "";
            }
        }

        if (!response.ok) {
            const message =
                payload && typeof payload === "object" && payload !== null && "message" in payload
                    ? payload.message
                    : undefined;
            handleAuthStatus(response.status, message);
            if (response.status !== 401) {
                showToast(message || `HTTP ${response.status}`, "error");
            }
            const error = new Error(message || `HTTP ${response.status}`);
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        handleAuthStatus(null, null);
        return payload;
    } finally {
        endRequest();
    }
}

async function fetchJSON(url) {
    const data = await apiFetch(url);
    return data || {};
}

async function fetchStatus() {
    const { data } = await fetchJSON("/api/status");
    updateRuntimeStatus(data?.runtime);
    if (data?.system) {
        dom.cpu.textContent = `${data.system.cpu ?? "--"}%`;
        dom.ram.textContent = `${data.system.memory ?? "--"}%`;
        dom.disk.textContent = `${data.system.disk ?? "--"}%`;
        dom.uptime.textContent = data.system.uptime ?? "--";
    }
}

function updateRuntimeStatus(runtime) {
    if (!runtime) {
        setStatusBadge("Unbekannt", false);
        updateSpeechControls({ available: false, enabled: false, listening: false });
        return;
    }
    const ready = Boolean(runtime.ready ?? runtime.running);
    const listening = Boolean(runtime.listening);
    const state = runtime.state;
    let label = listening ? "Hoert zu" : ready ? "Bereit" : state === "processing" ? "Verarbeite..." : state === "idle" ? "Bereit" : "Startet";
    if (runtime.status_message) {
        label = runtime.status_message;
    }
    const active = listening || ready || state === "processing";
    setStatusBadge(label, active);
    if (runtime.speech_status) {
        updateSpeechControls(runtime.speech_status);
    }
}

function setStatusBadge(text, active) {
    dom.statusBadge.textContent = text;
    dom.statusBadge.classList.toggle("active", Boolean(active));
}

async function fetchContext() {
    const { context, history } = await fetchJSON("/api/context");
    renderContext(context);
    if (Array.isArray(history)) {
        const commands = buildCommandHistory(history, 20);
        state.commandHistory = commands;
        renderCommandHistory(commands);
        if (!state.historyLoaded) {
            dom.chatLog.innerHTML = "";
            history.forEach(appendMessage);
            state.historyLoaded = true;
            scrollChatToBottom();
        }
    }
}

function renderContext(context = {}) {
    dom.contextList.innerHTML = "";
    const map = {
        "Use-Case": context.use_case,
        "Prioritaet": context.priority,
        "Logikpfad": context.logic_path,
    };
    Object.entries(map).forEach(([key, value]) => {
        const dt = document.createElement("dt");
        dt.textContent = key;
        const dd = document.createElement("dd");
        dd.textContent = value ?? "--";
        dom.contextList.append(dt, dd);
    });
    const plugin = context.plugin_context || {};
    dom.pluginContext.textContent = Object.keys(plugin).length
        ? JSON.stringify(plugin, null, 2)
        : "Kein Plugin-Kontext verfuegbar.";
}

async function fetchLogs() {
    const q = dom.logSearch.value.trim();
    const lines = Number(dom.logLines.value) || 200;
    const url = new URL("/api/logs", window.location.origin);
    url.searchParams.set("lines", lines.toString());
    if (q) url.searchParams.set("q", q);
    const { logs } = await fetchJSON(`${url.pathname}${url.search}`);
    dom.logOutput.textContent = Array.isArray(logs) ? logs.join("\n") : "";
}

function selectPlugin(name) {
    state.selectedPlugin = name || null;
    if (!dom.pluginDetails) {
        return;
    }
    const plugin =
        state.plugins.find((entry) => entry.name === name) ||
        state.plugins.find((entry) => entry.class === name);
    if (!plugin) {
        dom.pluginDetails.textContent = "Keine Plugin-Daten verfuegbar.";
        return;
    }
    dom.pluginDetails.textContent = JSON.stringify(plugin, null, 2);
}

function renderPluginTable(plugins = []) {
    if (!dom.pluginTable) return;
    dom.pluginTable.innerHTML = "";
    if (!plugins.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 5;
        cell.textContent = "Keine Plugins gefunden.";
        row.appendChild(cell);
        dom.pluginTable.appendChild(row);
        dom.pluginDetails.textContent = "Keine Plugin-Daten verfuegbar.";
        return;
    }
    plugins.forEach((plugin) => {
        const row = document.createElement("tr");
        row.dataset.plugin = plugin.name;
        const status = plugin.enabled ? (plugin.active ? "Aktiv" : "Geladen") : "Deaktiviert";
        row.innerHTML = `
            <td>${plugin.name}</td>
            <td>${plugin.module || ""}</td>
            <td>${status}</td>
            <td>${plugin.sandbox ? "ja" : "nein"}</td>
            <td class="plugin-actions"></td>
        `;
        const actionsCell = row.querySelector(".plugin-actions");
        const toggleBtn = document.createElement("button");
        toggleBtn.textContent = plugin.enabled ? "Deaktivieren" : "Aktivieren";
        toggleBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            pluginAction(plugin.name, plugin.enabled ? "disable" : "enable").catch((error) => {
                if (error.status !== 401) {
                    showToast(error.message, "error");
                }
            });
        });
        const reloadBtn = document.createElement("button");
        reloadBtn.textContent = "Reload";
        reloadBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            pluginAction(plugin.name, "reload").catch((error) => {
                if (error.status !== 401) {
                    showToast(error.message, "error");
                }
            });
        });
        actionsCell.append(toggleBtn, reloadBtn);
        row.addEventListener("click", () => selectPlugin(plugin.name));
        dom.pluginTable.appendChild(row);
    });
    if (state.selectedPlugin) {
        selectPlugin(state.selectedPlugin);
    } else {
        selectPlugin(plugins[0]?.name || null);
    }
}

async function fetchPlugins() {
    if (!dom.pluginTable) return;
    const { plugins } = await fetchJSON("/api/plugins");
    state.plugins = Array.isArray(plugins) ? plugins : [];
    renderPluginTable(state.plugins);
}

async function pluginAction(name, action) {
    const payload = await apiFetch("/api/plugins", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, action }),
    });
    const updated = Array.isArray(payload.plugins) ? payload.plugins : state.plugins;
    state.plugins = updated;
    renderPluginTable(updated);
    let toastMessage;
    if (action === "reload") {
        toastMessage = `Plugin ${name} wurde neu geladen.`;
    } else if (action === "disable") {
        toastMessage = `Plugin ${name} wurde deaktiviert.`;
    } else if (action === "enable") {
        toastMessage = `Plugin ${name} wurde aktiviert.`;
    }
    if (toastMessage) {
        showToast(toastMessage, "success");
    }
}

function renderMemoryTopics(topics = []) {
    if (!dom.memoryTopics) return;
    dom.memoryTopics.innerHTML = "";
    if (!topics || !topics.length) {
        const li = document.createElement("li");
        li.textContent = "Keine aktiven Themen";
        dom.memoryTopics.appendChild(li);
        return;
    }
    topics.forEach((topic) => {
        const li = document.createElement("li");
        li.textContent = topic;
        dom.memoryTopics.appendChild(li);
    });
}

function renderMemoryMessages(messages = []) {
    if (!dom.memoryMessages) return;
    dom.memoryMessages.innerHTML = "";
    if (!messages || !messages.length) {
        const li = document.createElement("li");
        li.textContent = "Noch keine Konversation gespeichert.";
        dom.memoryMessages.appendChild(li);
        return;
    }
    messages.slice().reverse().forEach((entry) => {
        const li = document.createElement("li");
        const meta = document.createElement("div");
        meta.className = "meta";
        const time = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : "--:--";
        meta.innerHTML = `<span>${entry.role}</span><span>${time}</span>`;
        const text = document.createElement("div");
        text.textContent = entry.content;
        li.append(meta, text);
        dom.memoryMessages.appendChild(li);
    });
}

function renderMemoryTimeline(events = []) {
    if (!dom.memoryTimeline) return;
    dom.memoryTimeline.innerHTML = "";
    if (!events || !events.length) {
        const li = document.createElement("li");
        li.textContent = "Keine Timeline-Eintraege.";
        dom.memoryTimeline.appendChild(li);
        return;
    }
    events.forEach((event) => {
        const li = document.createElement("li");
        const meta = document.createElement("div");
        meta.className = "meta";
        const time = event.timestamp ? new Date(event.timestamp).toLocaleString() : "--";
        meta.innerHTML = `<span>${event.event_type}</span><span>${time}</span>`;
        const payload = document.createElement("div");
        payload.textContent = JSON.stringify(event.payload || {}, null, 2);
        li.append(meta, payload);
        dom.memoryTimeline.appendChild(li);
    });
}

function renderMemorySearch(results = [], query = "") {
    if (!dom.memorySearchResults) return;
    dom.memorySearchResults.innerHTML = "";
    if (query && (!results || !results.length)) {
        const li = document.createElement("li");
        li.textContent = "Keine Ergebnisse fuer die aktuelle Suche.";
        dom.memorySearchResults.appendChild(li);
        return;
    }
    (results || []).forEach((item) => {
        const li = document.createElement("li");
        const meta = document.createElement("div");
        meta.className = "meta";
        meta.innerHTML = `<span>Score ${item.score ?? "--"}</span><span>${item.timestamp || ""}</span>`;
        const body = document.createElement("div");
        body.textContent = item.text || JSON.stringify(item.metadata || {}, null, 2);
        li.append(meta, body);
        dom.memorySearchResults.appendChild(li);
    });
}

function renderMemory(snapshot = {}, query = "") {
    state.memorySnapshot = snapshot || {};
    if (dom.memorySummary) {
        const summary = snapshot.short_term_summary || "Keine Daten verfuegbar.";
        dom.memorySummary.textContent = summary;
    }
    if (dom.memoryContext) {
        dom.memoryContext.textContent = snapshot.conversation_context || "";
    }
    if (dom.memoryQuery) {
        dom.memoryQuery.value = query;
    }
    renderMemoryTopics(snapshot.active_topics || []);
    renderMemoryMessages(snapshot.recent_messages || []);
    renderMemoryTimeline(snapshot.timeline || []);
    renderMemorySearch(snapshot.search_results || [], query);
}

async function loadMemory(query = state.memoryQuery) {
    if (!dom.memorySummary) return;
    const trimmed = (query || "").trim();
    state.memoryQuery = trimmed;
    const url = new URL("/api/memory", window.location.origin);
    if (trimmed) {
        url.searchParams.set("q", trimmed);
    }
    const { memory } = await fetchJSON(`${url.pathname}${url.search}`);
    renderMemory(memory || {}, trimmed);
}

function appendMessage(entry) {
    if (!entry?.text) return;
    const template = document.getElementById("message-template");
    const fragment = template.content.cloneNode(true);
    const container = fragment.querySelector(".chat-message");
    container.classList.add(entry.role);
    const roleLabel = fragment.querySelector(".role");
    const timeLabel = fragment.querySelector(".time");
    const textEl = fragment.querySelector(".text");
    const copyBtn = fragment.querySelector(".copy-btn");

    roleLabel.textContent = entry.role === "assistant" ? "J.A.R.V.I.S." : "Du";
    const timestamp = entry.timestamp ? entry.timestamp * 1000 : Date.now();
    timeLabel.textContent = new Date(timestamp).toLocaleTimeString();

    if (entry.role === "assistant") {
        textEl.innerHTML = renderMarkdown(entry.text);
        const feedbackBar = document.createElement("div");
        feedbackBar.className = "feedback-bar";
        const goodBtn = document.createElement("button");
        goodBtn.type = "button";
        goodBtn.textContent = "👍 Gut";
        goodBtn.addEventListener("click", () => submitFeedback(1, entry.text));
        const badBtn = document.createElement("button");
        badBtn.type = "button";
        badBtn.textContent = "👎 Schlecht";
        badBtn.addEventListener("click", () => submitFeedback(-1, entry.text));
        feedbackBar.append(goodBtn, badBtn);
        container.appendChild(feedbackBar);
        if (copyBtn) {
            copyBtn.classList.remove("hidden");
            copyBtn.addEventListener("click", () => {
                const plain = entry.text;
                const handleError = (error) => {
                    showToast(error?.message || "Konnte nicht kopiert werden.", "error");
                };
                if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
                    navigator.clipboard.writeText(plain).then(
                        () => showToast("Antwort kopiert.", "success", { duration: 2500 }),
                        handleError,
                    );
                } else {
                    try {
                        const temp = document.createElement("textarea");
                        temp.value = plain;
                        temp.setAttribute("readonly", "true");
                        temp.style.position = "absolute";
                        temp.style.left = "-9999px";
                        document.body.appendChild(temp);
                        temp.select();
                        const success = document.execCommand("copy");
                        document.body.removeChild(temp);
                        if (success) {
                            showToast("Antwort kopiert.", "success", { duration: 2500 });
                        } else {
                            handleError();
                        }
                    } catch (error) {
                        handleError(error);
                    }
                }
            });
        }
    } else {
        textEl.textContent = entry.text;
        if (copyBtn) {
            copyBtn.remove();
        }
        const historyEntry = {
            text: entry.text,
            timestamp: entry.timestamp || Date.now() / 1000,
        };
        state.commandHistory.unshift(historyEntry);
        if (state.commandHistory.length > 20) {
            state.commandHistory = state.commandHistory.slice(0, 20);
        }
        renderCommandHistory(state.commandHistory);
    }

    dom.chatLog.appendChild(fragment);
    while (dom.chatLog.children.length > 200) {
        dom.chatLog.firstElementChild?.remove();
    }
    scrollChatToBottom();
}

function scrollChatToBottom() {
    dom.chatLog.scrollTop = dom.chatLog.scrollHeight;
}

function connectWebsocket() {
    if (state.ws) {
        state.ws.close();
        state.ws = null;
    }
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const token = dom.tokenInput.value.trim();
    const query = token ? `?token=${encodeURIComponent(token)}` : "";
    const ws = new WebSocket(`${protocol}://${window.location.host}/events${query}`);
    state.ws = ws;
    ws.addEventListener("open", () => {
        dom.wsIndicator.classList.add("online");
        dom.wsIndicator.querySelector(".label").textContent = "Live";
    });
    ws.addEventListener("close", () => {
        dom.wsIndicator.classList.remove("online");
        dom.wsIndicator.querySelector(".label").textContent = "Offline";
        scheduleReconnect();
    });
    ws.addEventListener("message", (event) => {
        try {
            const data = JSON.parse(event.data);
            handleSocketEvent(data);
        } catch (error) {
            console.warn("Ungueltige WS-Nachricht", error);
        }
    });
}

function scheduleReconnect() {
    if (state.reconnectTimer) return;
    state.reconnectTimer = setTimeout(() => {
        state.reconnectTimer = null;
        connectWebsocket();
    }, 3000);
}

function handleSocketEvent(event) {
    switch (event.type) {
        case "assistant_message":
            appendMessage({ role: "assistant", text: event.payload?.text, timestamp: event.timestamp });
            break;
        case "user_message":
            if (event.payload?.source === "web-ui") return;
            appendMessage({ role: "user", text: event.payload?.text, timestamp: event.timestamp });
            break;
        case "status":
            updateRuntimeStatus(event.payload);
            break;
        case "knowledge_progress":
            pushKnowledgeEntry(event);
            break;
        case "security_challenge":
            toggleSecurityOverlay(Boolean(event.payload?.active), event.payload);
            break;
        case "security_result":
            toggleSecurityOverlay(false);
            break;
        case "system_metrics":
            updateSystemMetrics(event.payload);
            break;
        case "context_update":
            renderContext(event.payload);
            break;
        case "model_download_progress":
            handleModelDownloadProgress(event.payload || {});
            break;
        case "crawler_event":
            handleCrawlerEvent(event.payload || {});
            break;
        default:
            break;
    }
}

function pushKnowledgeEntry(event) {
    const payload = event.payload;
    const text = typeof payload === "string" ? payload : payload?.message || JSON.stringify(payload);
    const timestamp = (event.timestamp || Date.now() / 1000) * 1000;
    state.knowledgeEntries.unshift({ text, ts: new Date(timestamp).toLocaleTimeString() });
    state.knowledgeEntries = state.knowledgeEntries.slice(0, 12);
    dom.knowledgeFeed.innerHTML = "";
    state.knowledgeEntries.forEach(entry => {
        const li = document.createElement("li");
        li.textContent = `[${entry.ts}] ${entry.text}`;
        dom.knowledgeFeed.appendChild(li);
    });
}

function toggleSecurityOverlay(show, payload) {
    dom.securityOverlay.classList.toggle("hidden", !show);
    if (show && payload) {
        const hint = payload.hint ? ` Hinweis: ${payload.hint}` : "";
        dom.securityMessage.textContent = `Passphrase benoetigt fuer "${payload.command}".${hint}`;
        dom.securityInput.value = "";
        dom.securityInput.focus();
    }
}

/* ---------------------------------------------------------------------- */
/* Crawler UI */
/* ---------------------------------------------------------------------- */
function initCrawlerUI() {
    if (!dom.crawlerPanel) return;
    dom.crawlerRefresh?.addEventListener("click", () => refreshCrawlerDashboard());
    dom.crawlerSyncNow?.addEventListener("click", () => handleCrawlerSync());
    dom.crawlerSyncBtn?.addEventListener("click", () => handleCrawlerSync());
    dom.crawlerRecentDocs?.addEventListener("click", () => loadCrawlerDocuments(true));
    dom.crawlerJobForm?.addEventListener("submit", handleCrawlerJobSubmit);
    dom.crawlerConfigForm?.addEventListener("submit", handleCrawlerConfigSubmit);
    dom.crawlerAutoSync?.addEventListener("change", handleCrawlerAutoSyncToggle);
    dom.crawlerControlPause?.addEventListener("click", () => handleCrawlerControl("pause"));
    dom.crawlerControlResume?.addEventListener("click", () => handleCrawlerControl("resume"));
    dom.crawlerSafeAllow?.addEventListener("click", () => updateCrawlerSafeMode("allow"));
    dom.crawlerSafeBlock?.addEventListener("click", () => updateCrawlerSafeMode("block"));
    dom.crawlerRunningTable?.addEventListener("click", handleCrawlerJobAction);
    dom.crawlerCompletedTable?.addEventListener("click", handleCrawlerJobAction);
    refreshCrawlerDashboard();
    loadCrawlerDocuments();
    if (state.crawler.refreshTimer) {
        clearInterval(state.crawler.refreshTimer);
    }
    state.crawler.refreshTimer = setInterval(() => {
        if (state.activeTab === "crawler") {
            refreshCrawlerDashboard({ silent: true, skipDocuments: true });
        }
    }, 25000);
}

async function refreshCrawlerDashboard(options = {}) {
    if (!dom.crawlerPanel) return;
    try {
        const payload = await apiFetch("/api/crawler/status");
        const data = payload?.crawler || payload?.data || payload;
        if (!data) {
            throw new Error("Keine Daten");
        }
        state.crawler.status = data;
        renderCrawlerStatus(data);
        renderCrawlerJobs(data);
        updateCrawlerConfigForms(data);
        updateCrawlerSecurity(data.security);
        if (!options.skipDocuments) {
            renderCrawlerDocuments(data.recent_documents || []);
        }
    } catch (error) {
        if (!options.silent) {
            showToast("Crawler-Status nicht erreichbar.", "error", { title: "Crawler" });
        }
    }
}

function renderCrawlerStatus(data = {}) {
    if (!dom.crawlerPanel) return;
    const connected = Boolean(data.connected);
    if (dom.crawlerConnectionLabel) {
        dom.crawlerConnectionLabel.textContent = connected ? "🟢 Verbunden" : "🔴 Nicht verbunden";
    }
    if (dom.crawlerWorkerCount) {
        const workerCount = data.health?.workers ?? data.health?.worker_count ?? "–";
        dom.crawlerWorkerCount.textContent = `Worker: ${workerCount}`;
    }
    if (dom.crawlerLastSync) {
        dom.crawlerLastSync.textContent = data.last_sync ? formatRelativeTime(data.last_sync) : "Keine Daten";
    }
    if (dom.crawlerDocTotal) {
        dom.crawlerDocTotal.textContent = formatNumber(data.documents_total);
    }
    if (dom.crawlerDoc24h) {
        dom.crawlerDoc24h.textContent = `24h: ${formatNumber(data.documents_24h)}`;
    }
    if (dom.crawlerDocSince) {
        dom.crawlerDocSince.textContent = `Seit Sync: ${formatNumber(data.documents_since_sync)}`;
    }
    if (dom.crawlerOpenJobs) {
        dom.crawlerOpenJobs.textContent = String((data.running_jobs || []).length + (data.jobs?.length || 0) - (data.completed_jobs || []).length);
    }
    if (dom.crawlerRunningCount) {
        dom.crawlerRunningCount.textContent = `Running: ${(data.running_jobs || []).length}`;
    }
    if (dom.crawlerCpuUsage) {
        const cpu = data.health?.cpu ?? data.health?.cpu_percent;
        dom.crawlerCpuUsage.textContent = cpu !== undefined ? `${cpu}%` : "–";
    }
    if (dom.crawlerStatusNote) {
        dom.crawlerStatusNote.textContent = connected ? "Dienst bereit" : "Keine Verbindung";
    }
    if (dom.crawlerAutoSync) {
        dom.crawlerAutoSync.checked = Boolean(data.auto_sync);
    }
    const summaryText = data.last_sync ? formatRelativeTime(data.last_sync) : "Nie synchronisiert";
    if (dom.crawlerSyncSummary) {
        dom.crawlerSyncSummary.textContent = summaryText;
    }
    if (dom.crawlerSyncSummaryCard) {
        dom.crawlerSyncSummaryCard.textContent = summaryText;
    }
    if (dom.crawlerSyncDocs) {
        dom.crawlerSyncDocs.textContent = formatNumber(data.documents_since_sync);
    }
    if (dom.crawlerSyncTotal) {
        dom.crawlerSyncTotal.textContent = formatNumber(data.documents_total);
    }
    if (dom.crawlerSyncTotalCard) {
        dom.crawlerSyncTotalCard.textContent = formatNumber(data.documents_total);
    }
}

function renderCrawlerJobs(data = {}) {
    state.crawler.jobCache = {};
    const running = data.running_jobs || [];
    const completed = data.completed_jobs || [];
    renderCrawlerJobTable(dom.crawlerRunningTable, running, true);
    renderCrawlerJobTable(dom.crawlerCompletedTable, completed, false);
}

function renderCrawlerJobTable(target, jobs, active) {
    if (!target) return;
    target.innerHTML = "";
    if (!jobs.length) {
        const row = document.createElement("tr");
        const colSpan = target.closest("table")?.querySelectorAll("th").length || 3;
        row.innerHTML = `<td colspan="${colSpan}" class="muted">${active ? "Keine laufenden Jobs" : "Keine abgeschlossenen Jobs"}</td>`;
        target.appendChild(row);
        return;
    }
    jobs.forEach((job) => {
        const tr = document.createElement("tr");
        const status = (job.status || "").toLowerCase();
        const processed = `${job.processed_pages ?? 0} / ${job.max_pages ?? 0}`;
        const id = job.job_id || job.id;
        if (id) {
            state.crawler.jobCache[id] = job;
        }
        const columns = [
            job.topic || "–",
            status,
            processed,
            job.max_pages ?? "–",
            job.max_depth ?? "–",
            job.created_at ? new Date(job.created_at).toLocaleTimeString() : "–",
        ];
        columns.forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
        });
        const actionTd = document.createElement("td");
        const detailButton = document.createElement("button");
        detailButton.type = "button";
        detailButton.dataset.action = "details";
        if (id) {
            detailButton.dataset.jobId = String(id);
        }
        detailButton.textContent = "Details";
        actionTd.appendChild(detailButton);
        tr.appendChild(actionTd);
        target.appendChild(tr);
    });
}

function renderCrawlerDocuments(list) {
    if (!dom.crawlerDocumentsList) return;
    dom.crawlerDocumentsList.innerHTML = "";
    if (!list || !list.length) {
        const li = document.createElement("li");
        li.className = "muted";
        li.textContent = "Keine Dokumente verfügbar";
        dom.crawlerDocumentsList.appendChild(li);
        return;
    }
    list.forEach((doc) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${doc.title || "Unbenannt"}</strong>
            <small>${doc.cached_at ? new Date(doc.cached_at).toLocaleString() : ""}</small>
            <p>${doc.snippet || ""}</p>`;
        dom.crawlerDocumentsList.appendChild(li);
    });
}

function handleCrawlerJobAction(event) {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const jobId = button.dataset.jobId;
    if (!jobId) return;
    const job = state.crawler.jobCache[jobId];
    if (!job) return;
    const links = Array.isArray(job.start_urls) ? job.start_urls.join(", ") : "";
    pushCrawlerAlert(
        `Job "${job.topic}" (${job.status}) – ${job.processed_pages}/${job.max_pages} Seiten. URLs: ${links}`,
        "info",
    );
}

async function handleCrawlerJobSubmit(event) {
    event.preventDefault();
    const topic = dom.crawlerJobTopic?.value.trim();
    const urlsValue = dom.crawlerJobUrls?.value || "";
    const startUrls = urlsValue
        .split(/\n|,/)
        .map((entry) => entry.trim())
        .filter(Boolean);
    if (!topic || !startUrls.length) {
        showToast("Topic und Start-URLs sind erforderlich.", "warning");
        return;
    }
    const profile = dom.crawlerJobProfile?.value || "standard";
    let maxPages = Number(dom.crawlerJobPages?.value) || 200;
    let maxDepth = Number(dom.crawlerJobDepth?.value) || 2;
    if (profile === "aggressive") {
        maxPages = Math.min(maxPages * 2, 1000);
    } else if (profile === "slow") {
        maxPages = Math.max(Math.round(maxPages * 0.5), 50);
    } else if (profile === "whitelist") {
        maxDepth = Math.min(maxDepth, 1);
    }
    try {
        await apiFetch("/api/crawler/jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic,
                start_urls: startUrls,
                max_pages: maxPages,
                max_depth: maxDepth,
            }),
        });
        if (dom.crawlerJobFeedback) dom.crawlerJobFeedback.textContent = "Job gestartet";
        dom.crawlerJobForm?.reset();
        refreshCrawlerDashboard({ skipDocuments: true });
        showToast(`Crawler-Job für "${topic}" gestartet.`, "success");
    } catch (error) {
        if (dom.crawlerJobFeedback) dom.crawlerJobFeedback.textContent = "Job konnte nicht gestartet werden";
    }
}

async function handleCrawlerSync() {
    try {
        const result = await apiFetch("/api/crawler/sync", { method: "POST" });
        refreshCrawlerDashboard();
        const imported = result?.result?.imported ?? result?.result?.documents ?? 0;
        showToast(`Synchronisation abgeschlossen (${imported} Dokumente).`, "success", { title: "Crawler" });
    } catch (error) {
        showToast("Synchronisation fehlgeschlagen.", "error", { title: "Crawler" });
    }
}

async function handleCrawlerControl(action) {
    try {
        await apiFetch("/api/crawler/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action }),
        });
        showToast(`Crawler ${action === "pause" ? "pausiert" : "fortgesetzt"}.`, "info");
    } catch (error) {
        showToast("Crawler-Steuerung fehlgeschlagen.", "error");
    }
}

async function loadCrawlerDocuments(onlyRecent = false) {
    const query = new URLSearchParams({ limit: "50" });
    if (onlyRecent) query.set("recent", "1");
    try {
        const payload = await apiFetch(`/api/crawler/documents?${query.toString()}`);
        const docs = payload?.documents || [];
        state.crawler.documents = docs;
        renderCrawlerDocuments(docs);
    } catch {
        // ignore
    }
}

function updateCrawlerConfigForms(data = {}) {
    const config = data.config || {};
    const client = data.client_settings || {};
    if (dom.crawlerDomains) {
        const domains = config.network?.allowed_domains || [];
        dom.crawlerDomains.value = domains.join("\n");
    }
    if (dom.crawlerRateLimit) {
        dom.crawlerRateLimit.value = config.network?.max_requests_per_minute ?? "";
    }
    if (dom.crawlerRobots) {
        dom.crawlerRobots.checked = Boolean(config.network?.respect_robots_txt ?? true);
    }
    if (dom.crawlerMaxWorkers) dom.crawlerMaxWorkers.value = config.max_workers ?? "";
    if (dom.crawlerMaxCpu) dom.crawlerMaxCpu.value = config.resource_limits?.max_cpu_percent ?? "";
    if (dom.crawlerMaxRam) dom.crawlerMaxRam.value = config.resource_limits?.max_memory_mb ?? "";
    if (dom.crawlerMaxPages) dom.crawlerMaxPages.value = config.max_pages_per_job ?? "";
    if (dom.crawlerMaxDepth) dom.crawlerMaxDepth.value = config.max_depth ?? "";
    if (dom.crawlerBaseUrl) dom.crawlerBaseUrl.value = client.base_url || "";
    if (dom.crawlerApiKey) dom.crawlerApiKey.value = client.api_key || "";
    if (dom.crawlerSyncInterval) dom.crawlerSyncInterval.value = client.sync_interval_sec ?? "";
    if (dom.crawlerAutoSync) dom.crawlerAutoSync.checked = Boolean(client.auto_sync ?? true);
}

async function handleCrawlerConfigSubmit(event) {
    event.preventDefault();
    const domains = (dom.crawlerDomains?.value || "")
        .split(/[\n,]/)
        .map((entry) => entry.trim())
        .filter(Boolean);
    const serviceConfig = {
        network: {
            allowed_domains: domains,
            max_requests_per_minute: Number(dom.crawlerRateLimit?.value) || undefined,
            respect_robots_txt: dom.crawlerRobots?.checked ?? true,
        },
        max_workers: Number(dom.crawlerMaxWorkers?.value) || undefined,
        max_pages_per_job: Number(dom.crawlerMaxPages?.value) || undefined,
        max_depth: Number(dom.crawlerMaxDepth?.value) || undefined,
        resource_limits: {
            max_cpu_percent: Number(dom.crawlerMaxCpu?.value) || undefined,
            max_memory_mb: Number(dom.crawlerMaxRam?.value) || undefined,
        },
    };
    const clientSettings = {
        base_url: dom.crawlerBaseUrl?.value || "",
        api_key: dom.crawlerApiKey?.value || "",
        sync_interval_sec: Number(dom.crawlerSyncInterval?.value) || 1800,
        auto_sync: dom.crawlerAutoSync?.checked ?? true,
    };
    try {
        await apiFetch("/api/crawler/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ service_config: serviceConfig, client_settings: clientSettings }),
        });
        showToast("Crawler-Konfiguration gespeichert.", "success");
        refreshCrawlerDashboard({ skipDocuments: true, silent: true });
    } catch (error) {
        showToast("Konfiguration konnte nicht gespeichert werden.", "error");
    }
}

function handleCrawlerAutoSyncToggle() {
    const enabled = dom.crawlerAutoSync?.checked;
    apiFetch("/api/crawler/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_settings: { auto_sync: Boolean(enabled) } }),
    }).then(() => {
        showToast(`Auto-Sync ${enabled ? "aktiviert" : "deaktiviert"}.`, "info");
    });
}

async function updateCrawlerSafeMode(mode) {
    try {
        const payload = await apiFetch("/api/crawler/security", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode }),
        });
        updateCrawlerSecurity(payload?.security);
        showToast(`Safe-Mode auf "${mode}" gesetzt.`, "info");
    } catch (error) {
        showToast("Security-Aktion fehlgeschlagen.", "error");
    }
}

function updateCrawlerSecurity(security = {}) {
    if (dom.crawlerSecurityRole) dom.crawlerSecurityRole.textContent = security.role || "–";
    if (dom.crawlerSecurityKey) dom.crawlerSecurityKey.textContent = security.api_key_registered ? "Ja" : "Nein";
    if (dom.crawlerSecurityDomain) dom.crawlerSecurityDomain.textContent = security.domain_whitelist ? "Aktiv" : "Inaktiv";
    if (dom.crawlerSecuritySafe) dom.crawlerSecuritySafe.textContent = security.safe_mode || "allow";
}

async function loadCrawlerDocumentsAndStatus() {
    await Promise.all([refreshCrawlerDashboard({ silent: true, skipDocuments: true }), loadCrawlerDocuments()]);
}

function pushCrawlerAlert(message, type = "info") {
    if (!dom.crawlerAlerts) return;
    state.crawler.alerts.unshift({ message, type, ts: new Date().toLocaleTimeString() });
    state.crawler.alerts = state.crawler.alerts.slice(0, 6);
    dom.crawlerAlerts.innerHTML = "";
    state.crawler.alerts.forEach((entry) => {
        const li = document.createElement("li");
        li.className = entry.type;
        li.innerHTML = `<strong>${entry.ts}</strong> – ${entry.message}`;
        dom.crawlerAlerts.appendChild(li);
    });
    showToast(message, type === "error" ? "error" : type === "success" ? "success" : "info", { title: "Crawler" });
}

function handleCrawlerEvent(payload) {
    if (!payload) return;
    switch (payload.type) {
        case "job_created":
            pushCrawlerAlert(`Job #${payload.job_id} gestartet (${payload.topic}).`, "success");
            refreshCrawlerDashboard({ silent: true });
            break;
        case "job_failed":
            pushCrawlerAlert(`Job konnte nicht gestartet werden (${payload.topic || "unbekannt"}).`, "error");
            break;
        case "sync_started":
            pushCrawlerAlert("Crawler-Sync gestartet.", "info");
            break;
        case "sync_completed":
            pushCrawlerAlert(`Sync abgeschlossen (${payload.result?.imported ?? 0} Dokumente).`, "success");
            refreshCrawlerDashboard({ silent: true });
            break;
        case "sync_failed":
            pushCrawlerAlert(`Sync fehlgeschlagen: ${payload.error || "Unbekannter Fehler"}.`, "error");
            break;
        case "worker_pause":
        case "worker_resume":
            pushCrawlerAlert(`Worker ${payload.type === "worker_pause" ? "pausiert" : "fortgesetzt"}.`, "info");
            break;
        case "safe_mode":
            pushCrawlerAlert(`Safe-Mode gewechselt zu ${payload.value}.`, "warning");
            break;
        default:
            break;
    }
}

async function submitCommand(text, metadata = {}) {
    dom.sendButton.disabled = true;
    try {
        const payload = await apiFetch("/api/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: text, metadata }),
        });
        return payload?.response;
    } finally {
        dom.sendButton.disabled = false;
    }
}

async function submitFeedback(score, message) {
    try {
        await apiFetch("/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ score, message }),
        });
        showToast("Feedback gespeichert.", "success", { title: "Feedback" });
    } catch (error) {
        showToast("Feedback konnte nicht gesendet werden.", "error", { title: "Feedback" });
        console.error(error);
    }
}

function updateSystemMetrics(payload) {
    if (!payload) return;
    const status = payload.status || {};
    const summary = payload.summary || {};
    const details = payload.details || {};
    dom.cpu.textContent = `${status.cpu ?? summary.cpu_usage_percent ?? "--"}%`;
    dom.ram.textContent = `${status.memory ?? summary.memory_percent ?? "--"}%`;
    dom.disk.textContent = `${status.disk ?? "--"}%`;
    dom.cpuFreq.textContent = summary.cpu_freq ? `${Math.round(summary.cpu_freq.current || 0)} MHz` : "";
    if (summary.ram && summary.ram.free) {
        dom.ramFree.textContent = `${(summary.ram.free / 1_073_741_824).toFixed(1)} GB frei`;
    } else {
        dom.ramFree.textContent = "";
    }
    if (summary.gpu_available) {
        dom.gpuLoad.textContent = `${Math.round(summary.avg_gpu_load || 0)}%`;
        const used = summary.total_memory_used || 0;
        const total = summary.total_memory_total || 0;
        dom.gpuMem.textContent = total ? `${(used / 1024).toFixed(0)}/${(total / 1024).toFixed(0)} MB` : "";
    } else {
        dom.gpuLoad.textContent = "--%";
        dom.gpuMem.textContent = "";
    }
    dom.uptime.textContent = status.uptime || details.system?.uptime || "--";
    dom.uptimeBoot.textContent = details.system?.boot_time ? `seit ${new Date(details.system.boot_time).toLocaleString()}` : "";
    renderNetwork(details.network);
    renderDisks(details.disks);
    dom.systemInfo.textContent = details.system ? JSON.stringify(details.system, null, 2) : "";
}

function renderNetwork(data = {}) {
    if (!dom.networkTable) return;
    dom.networkTable.innerHTML = "";
    const interfaces = data.interfaces || {};
    Object.entries(interfaces).forEach(([name, info]) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${name}</td>
            <td>${info.ipv4 || "--"}</td>
            <td>${info.speed || "--"} Mb/s</td>
            <td>${info.is_up ? "aktiv" : "down"}</td>
        `;
        dom.networkTable.appendChild(tr);
    });
}

function renderDisks(data = {}) {
    if (!dom.diskTable) return;
    dom.diskTable.innerHTML = "";
    const disks = data.disks || {};
    Object.entries(disks).forEach(([device, info]) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${device}</td>
            <td>${formatBytes(info.used)}</td>
            <td>${formatBytes(info.free)}</td>
            <td>${info.percent ?? "--"}%</td>
        `;
        dom.diskTable.appendChild(tr);
    });
}

function buildCommandHistory(entries = [], limit = 20) {
    const filtered = Array.isArray(entries)
        ? entries.filter((entry) => entry && entry.role === "user" && entry.text)
        : [];
    return filtered.slice(-limit).reverse();
}

function renderCommandHistory(history = []) {
    if (!dom.commandHistory) return;
    state.commandHistory = Array.isArray(history) ? [...history] : [];
    dom.commandHistory.innerHTML = "";
    if (!state.commandHistory.length) {
        const empty = document.createElement("li");
        empty.textContent = "Keine Eintraege";
        dom.commandHistory.appendChild(empty);
        return;
    }
    state.commandHistory.forEach((entry) => {
        const li = document.createElement("li");
        const textSpan = document.createElement("span");
        textSpan.className = "history-text";
        textSpan.textContent = truncateText(entry.text, 90);

        const timeSpan = document.createElement("span");
        timeSpan.className = "history-time";
        const timestamp = entry.timestamp ? new Date(entry.timestamp * 1000) : new Date();
        timeSpan.textContent = timestamp.toLocaleTimeString();

        const actions = document.createElement("div");
        actions.className = "history-actions";
        const replayBtn = document.createElement("button");
        replayBtn.type = "button";
        replayBtn.textContent = "Erneut";
        replayBtn.addEventListener("click", () => {
            const commandText = entry.text;
            if (!commandText) {
                return;
            }
            dom.input.value = "";
            dom.input.focus();
            appendMessage({ role: "user", text: commandText, timestamp: Date.now() / 1000 });
            submitCommand(commandText, { source: "web-ui" }).catch((error) => {
                if (error.status !== 401) {
                    showToast(error.message, "error");
                }
            });
        });
        actions.appendChild(replayBtn);

        li.appendChild(textSpan);
        li.appendChild(timeSpan);
        li.appendChild(actions);
        dom.commandHistory.appendChild(li);
    });
}

async function fetchTTSSettings() {
    try {
        const { settings } = await fetchJSON("/api/tts/settings");
        state.tts = settings || { stream_enabled: true };
        if (dom.ttsStreamToggle) {
            dom.ttsStreamToggle.checked = Boolean(state.tts.stream_enabled);
        }
    } catch (error) {
        console.warn("TTS-Status konnte nicht geladen werden", error);
    }
}

async function toggleTTSStream(event) {
    const enabled = Boolean(event.target.checked);
    try {
        const { settings } = await apiFetch("/api/tts/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stream_enabled: enabled }),
        });
        state.tts = settings || { stream_enabled: enabled };
        showToast(enabled ? "TTS-Ausgabe aktiviert." : "TTS-Ausgabe deaktiviert.", "success");
    } catch (error) {
        if (error.status !== 401) {
            showToast(error.message, "error");
        }
        if (dom.ttsStreamToggle) {
            dom.ttsStreamToggle.checked = Boolean(state.tts.stream_enabled);
        }
    }
}

async function fetchChatHistory(limit = 20) {
    try {
        const { history } = await fetchJSON(`/api/chat/history?limit=${limit}`);
        if (Array.isArray(history)) {
            const commands = buildCommandHistory(history, limit);
            if (commands.length) {
                renderCommandHistory(commands);
            }
        }
    } catch (error) {
        console.warn("Chat-Historie konnte nicht geladen werden", error);
    }
}

function getModelLabel(modelKey) {
    const info = state.models?.[modelKey];
    return (info && (info.display_name || info.name)) || modelKey || "Modell";
}

function handleModelDownloadProgress(payload) {
    const model = payload.model;
    if (!model) {
        return;
    }
    const status = payload.status || "in_progress";
    const total = Number(payload.total) || 0;
    const downloaded = Number(payload.downloaded) || 0;
    let percent = typeof payload.percent === "number" && !Number.isNaN(payload.percent) ? payload.percent : null;
    if ((percent === null || percent === undefined) && total > 0) {
        percent = Math.min(100, Math.round((downloaded / total) * 100));
    }
    if (percent !== null) {
        percent = Math.max(0, Math.min(100, Math.round(percent)));
    }
    const progressEntry = {
        status,
        downloaded,
        total,
        percent,
        message: payload.message || null,
        speed: Number(payload.speed) || null,
        eta: Number(payload.eta) || null,
        updated_at: Date.now(),
    };

    const label = getModelLabel(model);

    if (!state.modelDownloads) {
        state.modelDownloads = {};
    }
    if (status === "completed") {
        if (model in state.modelDownloads) {
            delete state.modelDownloads[model];
        }
        showToast(`${label}: Download abgeschlossen.`, "success");
        loadModels().catch(console.error);
    } else if (status === "error" || status === "failed") {
        if (model in state.modelDownloads) {
            delete state.modelDownloads[model];
        }
        showToast(payload.message || `${label}: Download fehlgeschlagen.`, "error");
    } else if (status === "already_exists") {
        if (model in state.modelDownloads) {
            delete state.modelDownloads[model];
        }
        showToast(`${label} ist bereits vorhanden.`, "success");
        loadModels().catch(console.error);
    } else {
        state.modelDownloads[model] = progressEntry;
    }

    renderModelOverview({ available: state.models || {}, current: state.selectedModel });
    renderModelProgress(state.selectedModel);
}

function formatModelProgressLabel(progress = {}) {
    const parts = [];
    const percent = progress.percent;
    const downloaded = progress.downloaded;
    const total = progress.total;
    const speed = progress.speed;
    const status = progress.status;
    const message = progress.message;

    if (percent !== null && percent !== undefined && !Number.isNaN(percent)) {
        parts.push(`${Math.max(0, Math.min(100, Math.round(percent)))}%`);
    }
    if (downloaded) {
        const downloadedText = formatBytes(downloaded);
        const totalText = total ? formatBytes(total) : null;
        if (totalText && totalText !== "--") {
            parts.push(`${downloadedText}/${totalText}`);
        } else {
            parts.push(downloadedText);
        }
    }
    if (speed) {
        parts.push(`${formatBytes(speed)}/s`);
    }
    if (progress.eta && (status === "in_progress" || status === "starting")) {
        const etaLabel = formatDuration(progress.eta);
        if (etaLabel) {
            parts.push(`ETA ${etaLabel}`);
        }
    }
    if ((status === "error" || status === "failed") && message) {
        parts.push(message);
    }
    if (!parts.length) {
        parts.push("Lade...");
    }
    return parts.join(" · ");
}

function renderModelProgress(modelKey) {
    if (!dom.modelProgressWrapper) {
        return;
    }
    const progress = modelKey ? state.modelDownloads?.[modelKey] : null;
    if (!progress) {
        dom.modelProgressWrapper.classList.add("hidden");
        if (dom.modelProgressBar) {
            dom.modelProgressBar.style.width = "0%";
        }
        if (dom.modelProgressLabel) {
            dom.modelProgressLabel.textContent = "";
        }
        return;
    }
    dom.modelProgressWrapper.classList.remove("hidden");
    const percent = progress.percent !== null && progress.percent !== undefined
        ? Math.max(0, Math.min(100, Math.round(progress.percent)))
        : progress.total
        ? Math.max(0, Math.min(100, Math.round((progress.downloaded / progress.total) * 100)))
        : 0;
    if (dom.modelProgressBar) {
        dom.modelProgressBar.style.width = `${percent}%`;
    }
    if (dom.modelProgressLabel) {
        dom.modelProgressLabel.textContent = formatModelProgressLabel(progress);
    }
}

function renderKnowledgeStats(stats = {}) {
    if (!dom.knowledgeStats) return;
    dom.knowledgeStats.innerHTML = "";
    const entries = Object.entries(stats || {});
    if (!entries.length) {
        const empty = document.createElement("p");
        empty.textContent = "Keine Daten verfuegbar.";
        dom.knowledgeStats.appendChild(empty);
        return;
    }
    entries.forEach(([key, value]) => {
        const dt = document.createElement("dt");
        dt.textContent = key;
        const dd = document.createElement("dd");
        dd.textContent = typeof value === "number" ? value.toString() : `${value ?? "--"}`;
        dom.knowledgeStats.append(dt, dd);
    });
}

function updateSpeechControls(speech = {}) {
    const normalized = Object.assign({}, speech || {});
    const pending = Boolean(normalized.pending);
    delete normalized.pending;
    state.speech = normalized;
    if (!dom.speechToggleBtn || !dom.speechControlStatus) return;
    const available = normalized.available === undefined ? true : Boolean(normalized.available);
    const enabled = available && (normalized.enabled === undefined ? true : Boolean(normalized.enabled));
    const listening = Boolean(normalized.listening) && enabled;
    dom.speechToggleBtn.textContent = listening ? "Hoeren stoppen" : "Hoeren starten";
    dom.speechToggleBtn.disabled = pending || !enabled;
    const statusText = !available ? "Nicht verfuegbar" : listening ? "Aktiv" : enabled ? "Bereit" : "Deaktiviert";
    dom.speechControlStatus.textContent = statusText;
    dom.speechControlStatus.classList.toggle("active", listening);
    if (dom.wakeWordToggle) {
        dom.wakeWordToggle.checked = Boolean(normalized.wake_word_enabled);
        dom.wakeWordToggle.disabled = pending || !enabled;
    }
    if (dom.speechModeLabel) {
        const mode = normalized.speech_mode || normalized.active_mode || null;
        dom.speechModeLabel.textContent = mode ? `Modus: ${mode}` : "";
    }
}

async function fetchSpeechStatus() {
    try {
        const { speech } = await fetchJSON("/api/speech/status");
        updateSpeechControls(speech);
    } catch (error) {
        console.warn("Sprachstatus konnte nicht geladen werden:", error);
    }
}

async function toggleListening() {
    if (!dom.speechToggleBtn) return;
    const listening = Boolean(state.speech?.listening);
    const base = state.speech || {};
    state.speech = Object.assign({}, base, { pending: true });
    updateSpeechControls(state.speech);
    const action = listening ? "stop" : "start";
    try {
        const payload = await apiFetch("/api/speech/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action }),
        });
        updateSpeechControls(payload?.speech || {});
    } catch (error) {
        if (error.status !== 401) {
            console.error(error);
        }
        await fetchSpeechStatus();
    } finally {
        const baseState = state.speech || {};
        state.speech = Object.assign({}, baseState, { pending: false });
        updateSpeechControls(state.speech);
    }
}

async function toggleWakeWord(event) {
    const enabled = Boolean(event.target.checked);
    try {
        const payload = await apiFetch("/api/speech/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "wake_word", enabled }),
        });
        updateSpeechControls(payload?.speech || {});
    } catch (error) {
        if (error.status !== 401) {
            console.error(error);
        }
        if (dom.wakeWordToggle) {
            dom.wakeWordToggle.checked = !enabled;
        }
    }
}

function formatBytes(value) {
    if (typeof value !== "number") return "--";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let idx = 0;
    let current = value;
    while (current >= 1024 && idx < units.length - 1) {
        current /= 1024;
        idx += 1;
    }
    return `${current.toFixed(1)} ${units[idx]}`;
}

async function loadSystemTab() {
    const { metrics } = await fetchJSON("/api/system/metrics");
    updateSystemMetrics(metrics);
    try {
        const { stats } = await fetchJSON("/api/knowledge/stats");
        renderKnowledgeStats(stats);
    } catch (error) {
        console.warn("Wissensdatenbank konnte nicht geladen werden:", error);
        renderKnowledgeStats({});
    }
}

async function loadModels() {
    const { models } = await fetchJSON("/api/models");
    const available = models.available || {};
    const previousSelection = state.selectedModel;
    state.models = available;
    const fallback = Object.keys(available)[0] || null;
    state.selectedModel = previousSelection && available[previousSelection] ? previousSelection : models.current || fallback;
    renderModelOverview(models);
    renderModelProgress(state.selectedModel);
}

function renderModelOverview(models = {}) {
    dom.modelList.innerHTML = "";
    const available = models.available || state.models || {};
    Object.entries(available).forEach(([key, info]) => {
        const li = document.createElement("li");
        li.dataset.model = key;
        if (key === state.selectedModel) {
            li.classList.add("active");
        }
        const title = document.createElement("strong");
        title.textContent = info.display_name || key;
        li.appendChild(title);

        if (info.description) {
            const description = document.createElement("p");
            description.textContent = info.description;
            li.appendChild(description);
        }

        const detailsLine = document.createElement("small");
        const params = info.parameters ? `${info.parameters}` : "--";
        const contextLen = info.context_length || "--";
        const format = info.format || "--";
        detailsLine.textContent = `${params} · Kontext ${contextLen} · Format ${format}`;
        li.appendChild(detailsLine);

        const tags = document.createElement("div");
        tags.className = "model-tags";
        const addTag = (text, css) => {
            const tag = document.createElement("span");
            tag.className = `tag ${css}`;
            tag.textContent = text;
            tags.appendChild(tag);
        };
        if (info.active) {
            addTag("Aktiv", "active");
        } else if (info.loaded) {
            addTag("Geladen", "loaded");
        }
        if (info.downloaded) {
            addTag("Lokal", "local");
        } else {
            addTag("Fehlt", "missing");
        }
        if (info.ready && !info.active) {
            addTag("Bereit", "ready");
        }
        if (info.use_case) {
            addTag(info.use_case, "use-case");
        }
        li.appendChild(tags);

        const meta = document.createElement("div");
        meta.className = "model-meta";
        const pathText = info.local_path ? info.local_path : "Keine lokale Datei";
        const sizeText = info.size_human || (info.size_gb ? `${info.size_gb} GB` : "--");
        const pathLabel = document.createElement("span");
        pathLabel.textContent = `Datei: ${pathText}`;
        const sizeLabel = document.createElement("span");
        sizeLabel.textContent = `Groesse: ${sizeText}`;
        meta.append(pathLabel, sizeLabel);
        li.appendChild(meta);

        const progressInfo = state.modelDownloads?.[key];
        if (progressInfo) {
            const progressWrapper = document.createElement("div");
            progressWrapper.className = "model-progress";
            const progressBar = document.createElement("div");
            progressBar.className = "model-progress-bar";
            const percent = progressInfo.percent !== null && progressInfo.percent !== undefined
                ? Math.max(0, Math.min(100, Math.round(progressInfo.percent)))
                : progressInfo.total
                ? Math.max(0, Math.min(100, Math.round((progressInfo.downloaded / progressInfo.total) * 100)))
                : 0;
            progressBar.style.width = `${percent}%`;
            progressWrapper.appendChild(progressBar);
            li.appendChild(progressWrapper);

            const label = document.createElement("span");
            label.className = "model-progress-label";
            label.textContent = formatModelProgressLabel(progressInfo);
            li.appendChild(label);
        }

        li.addEventListener("click", () => selectModel(key));
        dom.modelList.appendChild(li);
    });
    selectModel(state.selectedModel);
}

function selectModel(key) {
    if (!key) return;
    state.selectedModel = key;
    const info = state.models[key] || {};
    dom.currentModelLabel.textContent = info.display_name || key;
    dom.modelMetadata.textContent = JSON.stringify(info, null, 2);
    dom.modelList.querySelectorAll("li").forEach((li) => {
        li.classList.toggle("active", li.dataset.model === key);
    });
    renderModelProgress(key);
}

async function modelAction(action) {
    if (!state.selectedModel) return;
    const modelKey = state.selectedModel;
    const modelInfo = state.models[modelKey] || {};
    const label = modelInfo.display_name || modelKey;
    if (action === "download") {
        handleModelDownloadProgress({
            model: modelKey,
            status: "starting",
            downloaded: 0,
            total: Number(modelInfo.size_bytes) || 0,
            percent: 0,
        });
    }
    await apiFetch("/api/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, model: state.selectedModel }),
    });
    await loadModels();
    let message;
    if (action === "load") {
        message = `${label} wurde geladen.`;
    } else if (action === "unload") {
        message = `${label} wurde entladen.`;
    } else if (action === "download") {
        message = `${label} wurde zum Download angestossen.`;
    }
    if (message) {
        showToast(message, "success");
    }
}

async function loadTrainingStatus() {
    const [{ training }, commandsPayload] = await Promise.all([
        fetchJSON("/api/training"),
        fetchJSON("/api/commands").catch((error) => {
            console.warn("Befehle konnten nicht geladen werden:", error);
            return { commands: [] };
        }),
    ]);
    dom.trainingLog.textContent = training.long_term
        ? JSON.stringify(training.long_term, null, 2)
        : "Noch keine Trainingsdaten.";
    renderTopCommands(training.learning?.top_commands || []);
    dom.reinforcementInfo.textContent = JSON.stringify(training.reinforcement || {}, null, 2);
    renderCommandList(commandsPayload.commands || []);
}

function renderTopCommands(commands) {
    dom.topCommands.innerHTML = "";
    commands.forEach((entry) => {
        const li = document.createElement("li");
        li.textContent = `${entry.command} · ${entry.count}`;
        dom.topCommands.appendChild(li);
    });
}

function renderCommandList(commands = []) {
    if (!dom.commandsTable) return;
    dom.commandsTable.innerHTML = "";
    if (!commands.length) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="3">Keine benutzerdefinierten Befehle vorhanden.</td>';
        dom.commandsTable.appendChild(row);
        return;
    }
    commands.forEach((entry) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${entry.category || "custom"}</td>
            <td>${entry.pattern}</td>
            <td>${entry.response}</td>
        `;
        dom.commandsTable.appendChild(tr);
    });
}

async function loadCommands() {
    const { commands } = await fetchJSON("/api/commands");
    renderCommandList(commands || []);
}

async function submitCustomCommand(event) {
    event.preventDefault();
    const pattern = dom.customCommandPattern.value.trim();
    const response = dom.customCommandResponse.value.trim();
    if (!pattern || !response) {
        showToast("Bitte sowohl Muster als auch Antwort angeben.", "error");
        return;
    }
    await apiFetch("/api/commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pattern, response }),
    });
    dom.customCommandPattern.value = "";
    dom.customCommandResponse.value = "";
    await loadCommands();
    showToast(`Befehl "${pattern}" gespeichert.`, "success");
}

async function clearLogs() {
    await apiFetch("/api/logs/clear", { method: "POST" });
    await fetchLogs();
    showToast("Logs wurden geleert.", "success");
}

async function runTrainingCycle() {
    await fetchJSON("/api/training/run");
    await loadTrainingStatus();
}

async function loadSettings() {
    const { settings } = await fetchJSON("/api/settings");
    if (settings.speech) {
        dom.speechForm.elements.wake_word_enabled.checked = Boolean(settings.speech.wake_word_enabled);
        dom.speechForm.elements.min_command_words.value = settings.speech.min_command_words ?? 3;
        dom.speechForm.elements.tts_rate.value = settings.speech.tts_rate ?? 180;
    }
    if (settings.web_interface) {
        dom.webForm.elements.port.value = settings.web_interface.port ?? 5050;
        dom.webForm.elements.host.value = settings.web_interface.host ?? "0.0.0.0";
        dom.webForm.elements.token.value = settings.web_interface.token ?? "";
    }
    if (settings.core && dom.systemForm) {
        dom.systemForm.elements.debug_mode.checked = Boolean(settings.core.debug_mode);
        dom.systemForm.elements.auto_start.checked = Boolean(settings.core.auto_start);
    }
    await loadAudioDevices();
}

async function saveSettings(form, key) {
    const payload = {};
    payload[key] = collectFormValues(form);
    await apiFetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    showToast("Einstellungen gespeichert.", "success");
}

async function loadAudioDevices() {
    const data = await fetchJSON("/api/audio/devices");
    dom.audioDeviceSelect.innerHTML = "";
    data.devices.forEach((device) => {
        const option = document.createElement("option");
        option.value = device.index;
        option.textContent = `${device.name} (Index ${device.index})`;
        dom.audioDeviceSelect.appendChild(option);
    });
    if (data.selected?.index !== undefined) {
        dom.audioDeviceSelect.value = data.selected.index;
    }
}

async function saveAudioDevice(event) {
    if (event) {
        event.preventDefault();
    }
    const index = Number(dom.audioDeviceSelect.value);
    await apiFetch("/api/audio/devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index }),
    });
    showToast("Audio-Eingabegeraet aktualisiert.", "success");
}

async function measureAudioLevel() {
    dom.audioLevelLabel.textContent = "Pegel-Test laeuft...";
    try {
        const payload = await apiFetch("/api/audio/measure", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ duration: 1.5 }),
        });
        const level = typeof payload?.level === "number" ? payload.level : 0;
        const percent = Math.round(level * 100);
        dom.audioLevelLabel.textContent = `Pegel: ${percent}%`;
    } catch (error) {
        dom.audioLevelLabel.textContent =
            error.status === 401 ? "Token erforderlich" : error.message || "Fehler";
    }
}

function setupTabs() {
    const buttons = Array.from(document.querySelectorAll("[data-tab]"));
    const panels = Array.from(document.querySelectorAll("[data-panel]"));
    if (!buttons.length) {
        return;
    }

    const runTabHooks = (tabName) => {
        if (tabName === "chat") {
            fetchSpeechStatus().catch(() => {});
            fetchTTSSettings().catch(() => {});
            fetchChatHistory().catch(() => {});
            setTimeout(scrollChatToBottom, 0);
        } else if (tabName === "assistant") {
            fetchContext().catch(() => {});
        } else if (tabName === "system") {
            loadSystemTab().catch(console.error);
        } else if (tabName === "models") {
            loadModels().catch(console.error);
        } else if (tabName === "plugins") {
            fetchPlugins().catch(console.error);
        } else if (tabName === "memory") {
            loadMemory().catch(console.error);
        } else if (tabName === "training") {
            loadTrainingStatus().catch(console.error);
        } else if (tabName === "settings") {
            loadSettings().catch(console.error);
        } else if (tabName === "logs") {
            fetchLogs().catch(console.error);
        } else if (tabName === "crawler") {
            refreshCrawlerDashboard({ silent: true });
            loadCrawlerDocuments().catch(() => {});
        }
    };

    const focusButton = (element) => {
        if (element && typeof element.focus === "function") {
            try {
                element.focus({ preventScroll: true });
            } catch (error) {
                element.focus();
            }
        }
    };

    const activate = (target, { runHooks = true } = {}) => {
        const tabName = target.dataset.tab;
        buttons.forEach((btn) => {
            const isActive = btn === target;
            btn.classList.toggle("active", isActive);
            btn.setAttribute("aria-selected", String(isActive));
            btn.setAttribute("tabindex", isActive ? "0" : "-1");
        });
        panels.forEach((panel) => {
            const isActive = panel.dataset.panel === tabName;
            panel.classList.toggle("active", isActive);
            panel.toggleAttribute("hidden", !isActive);
            panel.setAttribute("tabindex", isActive ? "0" : "-1");
            if (isActive) {
                panel.removeAttribute("aria-hidden");
            } else {
                panel.setAttribute("aria-hidden", "true");
            }
        });
        state.activeTab = tabName;
        if (runHooks) {
            runTabHooks(tabName);
        }
    };

    buttons.forEach((btn, index) => {
        btn.addEventListener("click", () => {
            activate(btn);
            focusButton(btn);
        });
        btn.addEventListener("keydown", (event) => {
            if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                event.preventDefault();
                const offset = event.key === "ArrowRight" ? 1 : -1;
                const nextIndex = (index + offset + buttons.length) % buttons.length;
                const nextButton = buttons[nextIndex];
                activate(nextButton);
                focusButton(nextButton);
            }
        });
    });

    const initiallyActive = buttons.find((btn) => btn.classList.contains("active")) || buttons[0];
    if (initiallyActive) {
        activate(initiallyActive, { runHooks: false });
    }
}

function bindEvents() {
    dom.form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = dom.input.value.trim();
        if (!text) return;
        dom.input.value = "";
        appendMessage({ role: "user", text, timestamp: Date.now() / 1000 });
        try {
            await submitCommand(text, { source: "web-ui" });
        } catch (error) {
            if (error.status === 401) {
                return;
            }
            appendMessage({ role: "assistant", text: `Fehler: ${error.message}`, timestamp: Date.now() / 1000 });
        }
    });
    if (dom.clearLogs) {
        dom.clearLogs.addEventListener("click", () =>
            clearLogs().catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            })
        );
    }
    dom.refreshLogs.addEventListener("click", () => fetchLogs().catch(console.error));
    dom.speedtest.addEventListener("click", async () => {
        dom.speedtest.disabled = true;
        dom.speedtest.textContent = "Teste...";
        try {
            const { result } = await apiFetch("/api/system/speedtest", { method: "POST" });
            dom.systemInfo.textContent = JSON.stringify(result, null, 2);
        } catch (error) {
            dom.systemInfo.textContent = `Speedtest fehlgeschlagen: ${error.message}`;
        } finally {
            dom.speedtest.disabled = false;
            dom.speedtest.textContent = "Speedtest";
        }
    });
    if (dom.customCommandForm) {
        dom.customCommandForm.addEventListener("submit", (event) => {
            submitCustomCommand(event).catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            });
        });
    }
    if (dom.speechToggleBtn) {
        dom.speechToggleBtn.addEventListener("click", () => {
            toggleListening().catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            });
        });
    }
    if (dom.wakeWordToggle) {
        dom.wakeWordToggle.addEventListener("change", (event) => {
            toggleWakeWord(event).catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            });
        });
    }
    if (dom.refreshPlugins) {
        dom.refreshPlugins.addEventListener("click", () => fetchPlugins().catch(console.error));
    }
    if (dom.memorySearchForm) {
        dom.memorySearchForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const query = dom.memoryQuery ? dom.memoryQuery.value : "";
            loadMemory(query).catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            });
        });
    }
    dom.modelActions.forEach((btn) =>
        btn.addEventListener("click", () =>
            modelAction(btn.dataset.action).catch((error) => {
                if (error.status !== 401) {
                    console.error(error);
                }
            })
        )
    );
    dom.runTraining.addEventListener("click", () => runTrainingCycle().catch(console.error));
    dom.refreshAudioDevices.addEventListener("click", () => loadAudioDevices().catch(console.error));
    dom.measureAudio.addEventListener("click", () => measureAudioLevel().catch(console.error));
    dom.audioForm.addEventListener("submit", (event) => {
        event.preventDefault();
        saveAudioDevice(event).catch(console.error);
    });
    initCrawlerUI();
    dom.speechForm.addEventListener("submit", (event) => {
        event.preventDefault();
        saveSettings(dom.speechForm, "speech").catch(console.error);
    });
    dom.webForm.addEventListener("submit", (event) => {
        event.preventDefault();
        saveSettings(dom.webForm, "web_interface").catch(console.error);
    });
    if (dom.systemForm) {
        dom.systemForm.addEventListener("submit", (event) => {
            event.preventDefault();
            saveSettings(dom.systemForm, "core").catch(console.error);
        });
    }
    if (dom.ttsStreamToggle) {
        dom.ttsStreamToggle.addEventListener("change", (event) => toggleTTSStream(event));
    }
    if (dom.tokenToggle && dom.tokenInput) {
        dom.tokenToggle.addEventListener("click", () => {
            const isVisible = dom.tokenInput.type === "text";
            dom.tokenInput.type = isVisible ? "password" : "text";
            dom.tokenToggle.textContent = isVisible ? "Anzeigen" : "Verbergen";
            dom.tokenToggle.setAttribute("aria-label", isVisible ? "Token anzeigen" : "Token verbergen");
            dom.tokenToggle.setAttribute("title", isVisible ? "Token anzeigen" : "Token verbergen");
        });
    }
    const applyToken = (force = false) => {
        if (!dom.tokenInput) return;
        const current = (dom.tokenInput.value || "").trim();
        if (!force && current === state.lastAppliedToken) {
            return;
        }
        state.lastAppliedToken = current;
        persistToken();
        setTokenError("");
        connectWebsocket();
        fetchStatus().catch(console.error);
        fetchContext().catch(console.error);
        fetchLogs().catch(console.error);
    };
    const scheduleTokenSync = () => {
        clearTimeout(state.tokenSyncTimer);
        state.tokenSyncTimer = setTimeout(() => applyToken(), 200);
    };
    dom.tokenInput.addEventListener("input", scheduleTokenSync);
    dom.tokenInput.addEventListener("change", () => applyToken());
    dom.tokenInput.addEventListener("blur", () => applyToken());
    const savedToken = localStorage.getItem("jarvisWebToken");
    if (savedToken) {
        if (dom.tokenInput.value.trim() !== savedToken.trim()) {
            dom.tokenInput.value = savedToken;
        }
        applyToken(true);
    }
    dom.securityForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const passphrase = dom.securityInput.value.trim();
        if (!passphrase) return;
        try {
            await submitCommand(passphrase, { source: "web-ui", passphrase_only: true });
        } catch (error) {
            appendMessage({ role: "assistant", text: `Passphrase: ${error.message}`, timestamp: Date.now() / 1000 });
        }
    });
    dom.securityCancel.addEventListener("click", () => toggleSecurityOverlay(false));
}

async function init() {
    ensureAssistantView();
    setupTabs();
    bindEvents();
    await Promise.all([fetchStatus(), fetchContext(), fetchLogs()]);
    await Promise.allSettled([fetchSpeechStatus(), fetchPlugins(), loadMemory(), fetchTTSSettings(), fetchChatHistory()]);
    connectWebsocket();
    setInterval(() => fetchStatus().catch(() => {}), 20000);
    setInterval(() => {
        if (state.activeTab === "logs") {
            fetchLogs().catch(() => {});
        }
    }, 60000);
    setInterval(() => {
        fetchSpeechStatus().catch(() => {});
    }, 20000);
    setInterval(() => {
        if (state.activeTab === "memory") {
            loadMemory(state.memoryQuery).catch(() => {});
        }
    }, 45000);
}

init().catch((error) => console.error(error));
