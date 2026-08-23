const totalCyclesEl = document.getElementById("totalCycles");
const avgLengthEl = document.getElementById("avgLength");
const minLengthEl = document.getElementById("minLength");
const maxLengthEl = document.getElementById("maxLength");
const emptyChart = document.getElementById("emptyChart");
const cycleCanvas = document.getElementById("cycleChart");
const emptyTable = document.getElementById("emptyTable");
const tableScroll = document.getElementById("tableScroll");
const cycleTableBody = document.getElementById("cycleTableBody");
const exportBtn = document.getElementById("exportBtn");
const clearHistBtn = document.getElementById("clearHistoryBtn");
const addManualBtn = document.getElementById("addManualBtn");
const manualForm = document.getElementById("manualForm");
const saveManualBtn = document.getElementById("saveManualBtn");
const cancelManualBtn = document.getElementById("cancelManualBtn");
const calendarGrid = document.getElementById("calendarGrid");

let chartInstance = null;

function init() {
    const history = SiklikaStorage.getHistory();
    updateStats(history);
    updateTable(history);
    updateChart(history);
    renderCalendar(history);
}

function updateStats(history) {
    const lengths = history.map((h) => h.cycleLength).filter(Boolean);
    totalCyclesEl.textContent = history.length;
    if (lengths.length === 0) {
        avgLengthEl.textContent = "--";
        minLengthEl.textContent = "--";
        maxLengthEl.textContent = "--";
        return;
    }
    const avg = lengths.reduce((a, b) => a + b, 0) / lengths.length;
    avgLengthEl.textContent = avg.toFixed(1);
    minLengthEl.textContent = Math.min(...lengths);
    maxLengthEl.textContent = Math.max(...lengths);
}

function updateTable(history) {
    if (history.length === 0) {
        emptyTable.style.display = "block";
        tableScroll.style.display = "none";
        return;
    }
    emptyTable.style.display = "none";
    tableScroll.style.display = "block";

    cycleTableBody.innerHTML = "";
    history.forEach((entry, idx) => {
        const badgeClass =
            entry.label === "Stabil" ? "badge-stable"
                : entry.label === "Perlu Perhatian" ? "badge-warning"
                    : "badge-irregular";

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${formatDate(entry.savedAt)}</td>
            <td><strong>${entry.cycleLength || "--"}</strong></td>
            <td>${entry.predictedNext || "--"}</td>
            <td><span class="status-badge ${badgeClass}">${entry.label || "--"}</span></td>
            <td>${entry.confidence ? entry.confidence + "%" : "--"}</td>
            <td>
                <button class="btn btn-ghost btn-sm" onclick="deleteEntry(${entry.id})">Hapus</button>
            </td>`;
        cycleTableBody.appendChild(tr);
    });
}

function deleteEntry(id) {
    if (!confirm("Hapus entri ini?")) return;
    const updated = SiklikaStorage.removeEntry(id);
    updateStats(updated);
    updateTable(updated);
    updateChart(updated);
    renderCalendar(updated);
}

function updateChart(history) {
    const lengths = history.map((h) => h.cycleLength).filter(Boolean).reverse();

    if (lengths.length === 0) {
        emptyChart.style.display = "flex";
        cycleCanvas.style.display = "none";
        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
        return;
    }

    emptyChart.style.display = "none";
    cycleCanvas.style.display = "block";

    const avg = lengths.reduce((a, b) => a + b, 0) / lengths.length;
    const labels = lengths.map((_, i) => `Siklus ${i + 1}`);

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(cycleCanvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Panjang Siklus (hari)",
                    data: lengths,
                    borderColor: "#4A234A",
                    backgroundColor: "rgba(74,35,74,0.10)",
                    borderWidth: 2.5,
                    pointBackgroundColor: "#4A234A",
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: "Rata-rata",
                    data: Array(lengths.length).fill(avg),
                    borderColor: "#C49F5A",
                    borderDash: [6, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                },
                {
                    label: "Batas bawah normal (21)",
                    data: Array(lengths.length).fill(21),
                    borderColor: "rgba(91,173,124,0.4)",
                    borderDash: [4, 4],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                },
                {
                    label: "Batas atas normal (45)",
                    data: Array(lengths.length).fill(45),
                    borderColor: "rgba(91,173,124,0.4)",
                    borderDash: [4, 4],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#fff",
                    titleColor: "#2A182A",
                    bodyColor: "#6B5A6B",
                    borderColor: "#F3E8F3",
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} hari`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: "rgba(0,0,0,0.04)" },
                    ticks: { color: "#ABA8B6", font: { family: "Outfit", size: 11 } },
                },
                y: {
                    min: 14,
                    max: 62,
                    grid: { color: "rgba(0,0,0,0.04)" },
                    ticks: {
                        color: "#ABA8B6",
                        font: { family: "Outfit", size: 11 },
                        callback: (v) => `${v}h`,
                    },
                },
            },
            animation: { duration: 800, easing: "easeOutQuart" },
        },
    });
}

function renderCalendar(history) {
    calendarGrid.innerHTML = "";
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const monthLabel = document.getElementById("calMonthLabel");
    if (monthLabel) {
        monthLabel.textContent = now.toLocaleDateString("id-ID", { month: "long", year: "numeric" });
    }

    const days = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
    days.forEach((d) => {
        const h = document.createElement("div");
        h.className = "cal-day-header";
        h.textContent = d;
        calendarGrid.appendChild(h);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();

    const dateDates = new Set(
        history
            .filter((h) => h.savedAt)
            .map((h) => new Date(h.savedAt).getDate())
    );

    const offset = firstDay === 0 ? 6 : firstDay - 1;
    for (let i = 0; i < offset; i++) {
        const empty = document.createElement("div");
        empty.className = "cal-day empty";
        calendarGrid.appendChild(empty);
    }

    for (let d = 1; d <= totalDays; d++) {
        const cell = document.createElement("div");
        cell.textContent = d;
        cell.className = "cal-day";
        if (d === now.getDate()) cell.classList.add("today");
        if (dateDates.has(d)) cell.classList.add("has-data");
        calendarGrid.appendChild(cell);
    }
}

exportBtn.addEventListener("click", () => {
    const history = SiklikaStorage.getHistory();
    if (history.length === 0) {
        alert("Tidak ada data untuk diekspor.");
        return;
    }

    const headers = ["No", "Tanggal", "Panjang Siklus (hari)", "Prediksi Berikutnya", "Status", "Keyakinan (%)"];
    const rows = history.map((e, i) => [
        i + 1,
        formatDate(e.savedAt),
        e.cycleLength || "",
        e.predictedNext || "",
        e.label || "",
        e.confidence || "",
    ]);

    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `siklika_riwayat_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
});

clearHistBtn.addEventListener("click", () => {
    if (!confirm("Hapus semua riwayat? Tindakan ini tidak dapat dibatalkan.")) return;
    SiklikaStorage.clearAll();
    init();
});

addManualBtn.addEventListener("click", () => {
    manualForm.style.display = manualForm.style.display === "none" ? "block" : "none";
    document.getElementById("manualDate").valueAsDate = new Date();
});

cancelManualBtn.addEventListener("click", () => {
    manualForm.style.display = "none";
});

saveManualBtn.addEventListener("click", () => {
    const len = parseInt(document.getElementById("manualLength").value);
    const date = document.getElementById("manualDate").value;
    const note = document.getElementById("manualNote").value;

    if (!len || len < 15 || len > 60) {
        alert("Panjang siklus harus antara 15-60 hari");
        return;
    }
    if (!date) {
        alert("Pilih tanggal");
        return;
    }

    SiklikaStorage.addEntry({
        cycleLength: len,
        predictedNext: null,
        label: null,
        confidence: null,
        savedAt: new Date(date).toISOString(),
        note,
        manual: true,
    });

    manualForm.style.display = "none";
    document.getElementById("manualLength").value = "";
    document.getElementById("manualNote").value = "";
    init();
});

init();
