/**
 * Personal AI Assistant - Full Frontend
 * - Chat UI + Sidebar + Stats
 * - Browser STT (Web Speech API)
 * - Browser TTS (speechSynthesis)
 * - Reminders dashboard + popup + voice alerts
 */

// ======================= CONFIG =========================
const CONFIG = {
    API_BASE_URL: "http://localhost:5000",
    ENDPOINTS: {
        PROCESS: "/process",
        HISTORY: "/history",
        HEALTH: "/health",
        REMINDERS: "/reminders",
        REMINDERS_CLEAR: "/reminders/clear",
        TRIGGER_POPUP: "/trigger_popup"
    },
    TIMEOUTS: {
        DEFAULT: 10000
    },
    POLLING_INTERVAL: 5000,       // Reminders list refresh
    REMINDER_ALERT_INTERVAL: 4000 // Triggered-reminder polling
};

// ======================= STATE ==========================
const state = {
    isListening: false,
    isProcessing: false,
    apiConnected: false,
    conversationHistory: [],
    reminders: [],
    stats: {
        messageCount: 0,
        voiceCount: 0
    }
};

// ======================= DOM REFS =======================
const elements = {
    chatContainer: null,
    userInput: null,
    sendBtn: null,
    voiceBtn: null,
    voiceIcon: null,
    clearBtn: null,
    statusDot: null,
    statusText: null,
    loadingOverlay: null,
    loadingText: null,
    toast: null,
    inputHint: null,

    sidebar: null,
    sidebarToggle: null,
    sidebarClose: null,
    remindersList: null,
    messageCount: null,
    voiceCount: null
};

// ================== SPEECH (BROWSER) ====================
// STT: Web Speech API
const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;
let recognition = null;

// TTS: speechSynthesis
function speakText(text) {
    if (!("speechSynthesis" in window)) {
        console.warn("Browser TTS not supported");
        return;
    }
    if (!text || !text.trim()) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = "en-US"; // or "en-IN" if you prefer

    window.speechSynthesis.cancel(); // avoid overlapping voices
    window.speechSynthesis.speak(utterance);
}

function initSpeechRecognition() {
    if (!SpeechRecognition) return;
    recognition = new SpeechRecognition();
    recognition.lang = "en-US"; // change to "en-IN" if needed
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
}

// ================== INITIALIZATION ======================
document.addEventListener("DOMContentLoaded", () => {
    initializeElements();
    attachEventListeners();

    if (SpeechRecognition) {
        initSpeechRecognition();
    } else {
        console.warn("Web Speech API not supported in this browser.");
    }

    checkAPIHealth();
    startReminderPolling();
    startReminderAlertPolling();
    updateStats();
    rotateHints();

    if (elements.userInput) elements.userInput.focus();
});

// ================== DOM INITIALIZATION ==================
function initializeElements() {
    elements.chatContainer = document.getElementById("chatContainer");
    elements.userInput = document.getElementById("userInput");
    elements.sendBtn = document.getElementById("sendBtn");
    elements.voiceBtn = document.getElementById("voiceBtn");
    elements.voiceIcon = document.getElementById("voiceIcon");
    elements.clearBtn = document.getElementById("clearBtn");
    elements.statusDot = document.getElementById("statusDot");
    elements.statusText = document.getElementById("statusText");
    elements.loadingOverlay = document.getElementById("loadingOverlay");
    elements.loadingText = document.getElementById("loadingText");
    elements.toast = document.getElementById("toast");
    elements.inputHint = document.getElementById("inputHint");

    elements.sidebar = document.getElementById("sidebar");
    elements.sidebarToggle = document.getElementById("sidebarToggle");
    elements.sidebarClose = document.getElementById("sidebarClose");
    elements.remindersList = document.getElementById("remindersList");
    elements.messageCount = document.getElementById("messageCount");
    elements.voiceCount = document.getElementById("voiceCount");

    if (elements.inputHint) {
        elements.inputHint.style.transition = "opacity 0.3s ease";
    }
}

// ================== EVENT LISTENERS =====================
function attachEventListeners() {
    // Send button
    elements.sendBtn.addEventListener("click", handleSendMessage);

    // Enter key in input
    elements.userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !state.isProcessing) {
            handleSendMessage();
        }
    });

    // Voice button
    elements.voiceBtn.addEventListener("click", handleVoiceInput);

    // Clear conversation
    elements.clearBtn.addEventListener("click", handleClearConversation);

    // Sidebar toggle
    elements.sidebarToggle.addEventListener("click", () => {
        elements.sidebar.classList.toggle("active");
    });
    elements.sidebarClose.addEventListener("click", () => {
        elements.sidebar.classList.remove("active");
    });

    // Close sidebar when clicking outside (mobile)
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 1024) {
            if (
                !elements.sidebar.contains(e.target) &&
                !elements.sidebarToggle.contains(e.target) &&
                elements.sidebar.classList.contains("active")
            ) {
                elements.sidebar.classList.remove("active");
            }
        }
    });

    // Periodic health check
    setInterval(checkAPIHealth, 30000); // every 30s
}

// ================== API HEALTH ==========================
async function checkAPIHealth() {
    try {
        const response = await fetch(
            `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.HEALTH}`
        );

        if (response.ok) {
            const data = await response.json();
            updateConnectionStatus(true, "Connected");

            const micStatus =
                (data.components && data.components.microphone) || data.microphone;
            if (micStatus === "not detected") {
                showToast(
                    "⚠️ Microphone not detected on server. Backend voice may not work.",
                    "warning"
                );
            }
        } else {
            updateConnectionStatus(false, "Connection Error");
        }
    } catch (error) {
        console.error("Health check failed:", error);
        updateConnectionStatus(false, "Disconnected");
        showToast(
            "❌ Cannot connect to server. Make sure the backend is running on port 5000.",
            "error"
        );
    }
}

function updateConnectionStatus(connected, statusText) {
    state.apiConnected = connected;
    elements.statusText.textContent = statusText;

    if (connected) {
        elements.statusDot.classList.remove("disconnected");
    } else {
        elements.statusDot.classList.add("disconnected");
    }
}

// ================== TEXT MESSAGE FLOW ===================
async function handleSendMessage() {
    const message = elements.userInput.value.trim();

    if (!message) {
        showToast("⚠️ Please enter a message", "warning");
        return;
    }

    if (!state.apiConnected) {
        showToast("❌ Not connected to server", "error");
        return;
    }

    if (state.isProcessing) return;

    elements.userInput.value = "";
    addMessageToChat(message, "user");
    removeWelcomeMessage();

    state.stats.messageCount++;
    updateStats();

    await processCommand(message);
}

async function processCommand(command) {
    state.isProcessing = true;
    showLoading("🤔 Processing...");

    try {
        const response = await fetch(
            `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PROCESS}`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command })
            }
        );

        hideLoading();

        const data = await response.json();

        if (data.success) {
            addMessageToChat(data.response, "assistant");

            state.conversationHistory.push({
                user: command,
                assistant: data.response,
                timestamp: new Date().toISOString()
            });

            if (command.toLowerCase().includes("remind")) {
                setTimeout(fetchReminders, 1000);
            }
        } else {
            addMessageToChat(
                "Sorry, I encountered an error processing your request.",
                "assistant",
                true
            );
            showToast("❌ " + (data.error || "Processing failed"), "error");
        }
    } catch (error) {
        console.error("Command processing error:", error);
        hideLoading();
        addMessageToChat(
            "Sorry, I could not connect to the server. Please check if the backend is running.",
            "assistant",
            true
        );
        showToast("❌ Connection error", "error");
    } finally {
        state.isProcessing = false;
    }
}

// ================== VOICE INPUT FLOW ====================
async function handleVoiceInput() {
    if (!SpeechRecognition) {
        showToast(
            "❌ Voice input not supported in this browser. Use Chrome or Edge desktop.",
            "error"
        );
        return;
    }

    if (!state.apiConnected) {
        showToast("❌ Not connected to server", "error");
        return;
    }

    if (state.isListening) {
        showToast("⚠️ Already listening...", "warning");
        return;
    }

    if (!recognition) initSpeechRecognition();

    state.isListening = true;
    updateVoiceButton(true);
    showLoading("🎤 Listening... Speak now");

    recognition.onresult = async (event) => {
        hideLoading();

        const transcript = event.results[0][0].transcript.trim();
        console.log("🎙 Recognized:", transcript);

        if (!transcript) {
            showToast("⚠️ No speech detected. Please try again.", "warning");
            return;
        }

        removeWelcomeMessage();
        addMessageToChat(transcript, "user");

        state.stats.messageCount++;
        state.stats.voiceCount++;
        updateStats();

        await processCommand(transcript);

        const last =
            state.conversationHistory[state.conversationHistory.length - 1];
        if (last && last.assistant) {
            speakText(last.assistant);
        }
    };

    recognition.onerror = (event) => {
        hideLoading();
        console.warn("STT error:", event.error);
        if (event.error === "no-speech") {
            showToast("⚠️ No speech detected. Please try again.", "warning");
        } else if (event.error === "audio-capture") {
            showToast(
                "⚠️ No microphone available or access denied.",
                "warning"
            );
        } else {
            showToast("❌ Voice recognition error: " + event.error, "error");
        }
    };

    recognition.onend = () => {
        state.isListening = false;
        updateVoiceButton(false);
        if (elements.loadingOverlay.classList.contains("show")) {
            hideLoading();
        }
    };

    try {
        recognition.start();
    } catch (err) {
        hideLoading();
        state.isListening = false;
        updateVoiceButton(false);
        console.error("Recognition start failed:", err);
        showToast("❌ Could not start voice recognition", "error");
    }
}

// ================== CHAT RENDERING ======================
function addMessageToChat(message, sender, isError = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    if (isError) messageDiv.classList.add("error");

    const avatar = sender === "user" ? "👤" : "🤖";
    const senderName = sender === "user" ? "You" : "Assistant";

    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <span>${senderName}</span>
        </div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;

    elements.chatContainer.appendChild(messageDiv);
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

function removeWelcomeMessage() {
    const welcomeMsg = elements.chatContainer.querySelector(".welcome-message");
    if (welcomeMsg) {
        welcomeMsg.style.opacity = "0";
        welcomeMsg.style.transform = "scale(0.95)";
        setTimeout(() => welcomeMsg.remove(), 300);
    }
}

// ================== CLEAR CONVERSATION ==================
async function handleClearConversation() {
    if (!confirm("Are you sure you want to clear the conversation?")) return;

    try {
        const response = await fetch(
            `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.HISTORY}`,
            { method: "DELETE" }
        );

        if (response.ok) {
            state.conversationHistory = [];
            state.stats.messageCount = 0;
            state.stats.voiceCount = 0;
            updateStats();

            elements.chatContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">✨</div>
                    <h2>Welcome to Your AI Assistant!</h2>
                    <p class="welcome-subtitle">I'm here to help you with various tasks</p>
                    
                    <div class="capabilities-grid">
                        <div class="capability-card">
                            <div class="capability-icon">⏰</div>
                            <h4>Time & Date</h4>
                            <p>Get current time and date instantly</p>
                        </div>
                        <div class="capability-card">
                            <div class="capability-icon">🧮</div>
                            <h4>Mathematics</h4>
                            <p>Solve calculations and equations</p>
                        </div>
                        <div class="capability-card">
                            <div class="capability-icon">🔍</div>
                            <h4>Web Search</h4>
                            <p>Search for information online</p>
                        </div>
                        <div class="capability-card">
                            <div class="capability-icon">📝</div>
                            <h4>Reminders</h4>
                            <p>Set and manage your reminders</p>
                        </div>
                    </div>
                    
                    <div class="example-queries">
                        <p class="example-title">Try asking:</p>
                        <div class="example-chips">
                            <span class="chip" onclick="sendQuickCommand('What time is it?')">What time is it?</span>
                            <span class="chip" onclick="sendQuickCommand('Calculate 15 times 8')">Calculate 15 times 8</span>
                            <span class="chip" onclick="sendQuickCommand('Search for AI news')">Search for AI news</span>
                            <span class="chip" onclick="sendQuickCommand('Remind me to exercise in 30 minutes')">Set a reminder</span>
                        </div>
                    </div>
                </div>
            `;

            showToast("✅ Conversation cleared", "success");
        } else {
            showToast("❌ Failed to clear conversation", "error");
        }
    } catch (error) {
        console.error("Clear conversation error:", error);
        showToast("❌ Error clearing conversation", "error");
    }
}

function sendQuickCommand(command) {
    elements.userInput.value = command;
    handleSendMessage();
}
window.sendQuickCommand = sendQuickCommand;

// ================== UI HELPERS =========================
function updateVoiceButton(listening) {
    if (listening) {
        elements.voiceBtn.classList.add("listening");
        elements.voiceIcon.textContent = "🔴";
        elements.voiceBtn.title = "Listening...";
    } else {
        elements.voiceBtn.classList.remove("listening");
        elements.voiceIcon.textContent = "🎤";
        elements.voiceBtn.title = "Voice input";
    }
}

function showLoading(text = "Processing...") {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.classList.add("show");
}

function hideLoading() {
    elements.loadingOverlay.classList.remove("show");
}

function showToast(message, type = "info") {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`;

    setTimeout(() => {
        elements.toast.classList.add("show");
    }, 10);

    setTimeout(() => {
        elements.toast.classList.remove("show");
    }, 4000);
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ================== REMINDERS (SIDEBAR) =================
async function fetchReminders() {
    if (!state.apiConnected) return;

    try {
        const response = await fetch(
            `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.REMINDERS}`
        );

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                state.reminders = data.reminders || [];
                updateRemindersUI();
            }
        }
    } catch (error) {
        console.error("Error fetching reminders:", error);
    }
}

function updateRemindersUI() {
    if (!elements.remindersList) return;

    if (!state.reminders.length) {
        elements.remindersList.innerHTML =
            '<p class="empty-state">No active reminders</p>';
        return;
    }

    elements.remindersList.innerHTML = state.reminders
        .map(
            (r) => `
        <div class="reminder-item">
            <div class="reminder-header">
                <span class="reminder-time">${r.time}</span>
                <button class="reminder-delete" onclick="deleteReminder(${r.id})" title="Delete reminder">
                    ✕
                </button>
            </div>
            <div class="reminder-text">${escapeHtml(r.text)}</div>
        </div>
    `
        )
        .join("");
}

async function deleteReminder(reminderId) {
    try {
        const response = await fetch(
            `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.REMINDERS}/${reminderId}`,
            { method: "DELETE" }
        );

        if (response.ok) {
            showToast("✅ Reminder deleted", "success");
            fetchReminders();
        } else {
            showToast("❌ Failed to delete reminder", "error");
        }
    } catch (error) {
        console.error("Error deleting reminder:", error);
        showToast("❌ Error deleting reminder", "error");
    }
}
window.deleteReminder = deleteReminder;

function startReminderPolling() {
    fetchReminders();
    setInterval(fetchReminders, CONFIG.POLLING_INTERVAL);
}

// ============ REMINDER POPUP + VOICE ALERTS =============
function startReminderAlertPolling() {
    setInterval(checkReminderAlerts, CONFIG.REMINDER_ALERT_INTERVAL);
}

async function checkReminderAlerts() {
    try {
        const res = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.TRIGGER_POPUP}`);
        const data = await res.json();

        if (data.success && data.message) {
            console.log("Reminder Popup Triggered:", data);

            showReminderPopup(data.message);
            speakText(`Reminder: ${data.message}`);
            showToast(`⏰ ${data.message}`, "warning");
        }

    } catch (err) {
        console.error("Popup polling error:", err);
    }
}



function showReminderPopup(message) {
    const popup = document.createElement("div");
    popup.textContent = `⏰ Reminder: ${message}`;

    popup.style.position = "fixed";
    popup.style.right = "24px";
    popup.style.bottom = "24px";
    popup.style.padding = "12px 18px";
    popup.style.background = "#f97316";
    popup.style.color = "#ffffff";
    popup.style.borderRadius = "12px";
    popup.style.fontSize = "0.95rem";
    popup.style.fontWeight = "600";
    popup.style.boxShadow = "0 12px 30px rgba(15,23,42,0.45)";
    popup.style.zIndex = "9999";
    popup.style.transition = "opacity 0.3s ease, transform 0.3s ease";

    document.body.appendChild(popup);

    setTimeout(() => {
        popup.style.opacity = "0";
        popup.style.transform = "translateY(8px)";
        setTimeout(() => popup.remove(), 300);
    }, 5000);
}

// ================== STATS & HINTS =======================
function updateStats() {
    if (elements.messageCount)
        elements.messageCount.textContent = state.stats.messageCount;
    if (elements.voiceCount)
        elements.voiceCount.textContent = state.stats.voiceCount;
}

function rotateHints() {
    const hints = [
        "💡 Tip: Press Enter to send, or use voice for hands-free interaction",
        '💡 Try: "What time is it?" or "Calculate 25 times 4"',
        '💡 Search: "Tell me about artificial intelligence"',
        '💡 Reminder: "Remind me to call John at 3 PM"',
        "💡 Voice: Click the microphone and speak naturally",
        '💡 Math: "What is 144 divided by 12?"'
    ];

    let currentIndex = 0;

    setInterval(() => {
        currentIndex = (currentIndex + 1) % hints.length;
        if (elements.inputHint) {
            elements.inputHint.style.opacity = "0";
            setTimeout(() => {
                elements.inputHint.textContent = hints[currentIndex];
                elements.inputHint.style.opacity = "1";
            }, 300);
        }
    }, 8000);
}

// ================== LOG ===============================
console.log("✅ Personal AI Assistant frontend initialized");
console.log("🔌 Connecting to:", CONFIG.API_BASE_URL);
