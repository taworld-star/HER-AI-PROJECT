const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const typingIndicator = document.getElementById("typingIndicator");
const clearChatBtn = document.getElementById("clearChatBtn");

let isLoading = false;

const params = new URLSearchParams(window.location.search);
const prefillMsg = params.get("q");
if (prefillMsg) {
    chatInput.value = decodeURIComponent(prefillMsg);
    setTimeout(() => sendMessage(), 600);
}

document.querySelectorAll(".topic-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
        chatInput.value = btn.dataset.msg;
        sendMessage();
    });
});

sendBtn.addEventListener("click", sendMessage);

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
});

clearChatBtn.addEventListener("click", () => {
    chatMessages.querySelectorAll(".message:not(#welcomeMsg)").forEach((m) => m.remove());
});

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isLoading) return;

    isLoading = true;
    sendBtn.disabled = true;
    chatInput.value = "";
    chatInput.style.height = "auto";

    appendMessage("user", text);
    typingIndicator.style.display = "flex";
    scrollToBottom();

    try {
        const data = await SiklikaApi.post("/chat", { message: text });
        typingIndicator.style.display = "none";

        if (data.success) {
            appendMessage("bot", data.reply, data.mode);
        } else {
            appendError(data.error || "Terjadi kesalahan.");
        }
    } catch (err) {
        typingIndicator.style.display = "none";
        appendError(
            `Tidak dapat terhubung ke server. Pastikan backend Flask berjalan di <code>http://localhost:5000</code>`
        );
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        chatInput.focus();
        scrollToBottom();
    }
}

function appendMessage(role, text, mode) {
    const div = document.createElement("div");
    div.className = `message ${role === "bot" ? "bot-message" : "user-message"}`;
    const now = formatTime();

    if (role === "bot") {
        const sourceLabel = mode === "kb_fallback"
            ? '<span class="msg-source">Basis pengetahuan lokal</span>'
            : '<span class="msg-source">Gemini AI</span>';
        div.innerHTML = `
            <div class="msg-avatar"><img src="assets/logo-mark.png" alt="Sika" class="msg-avatar-img" /></div>
            <div>
                <div class="msg-bubble">${markdownToHtml(text)}${sourceLabel}</div>
                <span class="msg-time">${now}</span>
            </div>`;
    } else {
        div.innerHTML = `
            <div>
                <div class="msg-bubble">${escapeHtml(text)}</div>
                <span class="msg-time" style="text-align:right;display:block">${now}</span>
            </div>
            <div class="msg-avatar user-avatar">U</div>`;
    }

    chatMessages.appendChild(div);
    scrollToBottom();
}

function appendError(html) {
    const div = document.createElement("div");
    div.className = "message bot-message";
    div.innerHTML = `
            <div class="msg-avatar"><img src="assets/logo-mark.png" alt="" class="msg-avatar-img" /></div>
        <div>
            <div class="msg-bubble error-bubble">
                <p>${html}</p>
            </div>
        </div>`;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}
