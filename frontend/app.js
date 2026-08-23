const API_BASE = "http://localhost:5000/api";

const navbar = document.getElementById("navbar");
if (navbar) {
    window.addEventListener("scroll", () => {
        navbar.classList.toggle("scrolled", window.scrollY > 20);
    }, { passive: true });
}

const hamburger = document.getElementById("hamburger");
const navLinks = document.getElementById("navLinks");
if (hamburger && navLinks) {
    hamburger.addEventListener("click", () => {
        navLinks.classList.toggle("open");
    });
}

const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
        if (e.isIntersecting) {
            e.target.style.opacity = "1";
            e.target.style.transform = "translateY(0)";
            fadeObserver.unobserve(e.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll(".feature-card, .step-item, .stat-card").forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(24px)";
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    fadeObserver.observe(el);
});

const Storage = {
    HISTORY_KEY: "siklika_cycle_history",

    getHistory() {
        try {
            return JSON.parse(localStorage.getItem(this.HISTORY_KEY) || "[]");
        } catch {
            return [];
        }
    },

    saveHistory(data) {
        localStorage.setItem(this.HISTORY_KEY, JSON.stringify(data));
    },

    addEntry(entry) {
        const history = this.getHistory();
        history.unshift({ ...entry, id: Date.now(), savedAt: new Date().toISOString() });
        this.saveHistory(history);
        return history;
    },

    removeEntry(id) {
        const history = this.getHistory().filter((e) => e.id !== id);
        this.saveHistory(history);
        return history;
    },

    clearAll() {
        localStorage.removeItem(this.HISTORY_KEY);
    },
};

async function apiPost(endpoint, body) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
}

function markdownToHtml(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/^- (.+)$/gm, "<li>$1</li>")
        .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
        .replace(/\n\n/g, "</p><p>")
        .replace(/^(?!<)(.+)$/gm, (_, g) => (g ? `<p>${g}</p>` : ""))
        .replace(/^---$/gm, "<hr>")
        .trim();
}

function formatTime(iso) {
    const d = iso ? new Date(iso) : new Date();
    return d.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(iso) {
    const d = iso ? new Date(iso) : new Date();
    return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

window.SiklikaStorage = Storage;
window.SiklikaApi = { post: apiPost };
window.markdownToHtml = markdownToHtml;
window.formatTime = formatTime;
window.formatDate = formatDate;
