const form = document.getElementById("predictionForm");
const addHistBtn = document.getElementById("addHistBtn");
const removeHistBtn = document.getElementById("removeHistBtn");
const histContainer = document.getElementById("historyContainer");
const submitBtn = document.getElementById("submitBtn");
const btnText = document.getElementById("btnText");
const btnLoader = document.getElementById("btnLoader");

const emptyState = document.getElementById("emptyState");
const resultCard = document.getElementById("resultCard");
const errorCard = document.getElementById("errorCard");

const resultEmoji = document.getElementById("resultEmoji");
const resultDays = document.getElementById("resultDays");
const stabilityBadge = document.getElementById("stabilityBadge");
const stabilityLabel = document.getElementById("stabilityLabel");
const confidencePct = document.getElementById("confidencePct");
const confidenceFill = document.getElementById("confidenceFill");
const lowerBound = document.getElementById("lowerBound");
const centerPred = document.getElementById("centerPred");
const upperBound = document.getElementById("upperBound");
const resultMessage = document.getElementById("resultMessage");
const consultCta = document.getElementById("consultCta");
const timelineTrack = document.getElementById("timelineTrack");

let histCount = 1;
let lastResult = null;

addHistBtn.addEventListener("click", () => {
    if (histCount >= 6) return;
    histCount++;
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
        <span class="hist-label">Siklus ke-${histCount}</span>
        <div class="input-wrapper compact">
            <input type="number" class="hist-input" min="15" max="60" placeholder="hari" />
            <span class="input-icon">Hari</span>
        </div>`;
    histContainer.appendChild(item);
    removeHistBtn.style.display = "inline-flex";
    if (histCount >= 6) addHistBtn.disabled = true;
});

removeHistBtn.addEventListener("click", () => {
    if (histCount <= 1) return;
    histContainer.removeChild(histContainer.lastElementChild);
    histCount--;
    addHistBtn.disabled = false;
    if (histCount <= 1) removeHistBtn.style.display = "none";
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const age = parseInt(document.getElementById("age").value);
    const cycleLength = parseInt(document.getElementById("current_cycle").value);
    const histInputs = [...document.querySelectorAll(".hist-input")]
        .map((i) => parseInt(i.value))
        .filter((v) => !isNaN(v) && v >= 15 && v <= 60);

    if (!age || age < 10 || age > 60) {
        alert("Masukkan usia yang valid (10-60 tahun)");
        return;
    }
    if (!cycleLength || cycleLength < 15 || cycleLength > 60) {
        alert("Panjang siklus harus antara 15-60 hari");
        return;
    }

    setLoading(true);
    hideAllResults();

    try {
        const data = await SiklikaApi.post("/predict", {
            age,
            cycle_length: cycleLength,
            cycle_number: histInputs.length + 1,
            history: histInputs,
        });

        if (data.success) {
            lastResult = { ...data.prediction, age, cycleLength, histInputs };
            showResult(data.prediction);
        } else {
            showError(data.error || "Terjadi kesalahan");
        }
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
});

function setLoading(on) {
    submitBtn.disabled = on;
    btnText.style.display = on ? "none" : "flex";
    btnLoader.style.display = on ? "flex" : "none";
}

function hideAllResults() {
    emptyState.style.display = "none";
    resultCard.style.display = "none";
    errorCard.style.display = "none";
}

function showResult(pred) {
    hideAllResults();

    resultDays.textContent = `${pred.predicted} hari`;

    const emojiMap = {
        Stabil: "✓",
        "Berpotensi Tidak Teratur": "~",
        "Perlu Perhatian": "!",
    };
    resultEmoji.textContent = emojiMap[pred.label] || "~";

    stabilityLabel.textContent = pred.label;
    stabilityBadge.className = "stability-badge";
    if (pred.label === "Stabil") stabilityBadge.classList.add("stable");
    else if (pred.label === "Berpotensi Tidak Teratur") stabilityBadge.classList.add("irregular");
    else stabilityBadge.classList.add("warning");

    confidencePct.textContent = `${pred.confidence_pct}%`;
    confidenceFill.style.width = "0%";
    setTimeout(() => { confidenceFill.style.width = `${pred.confidence_pct}%`; }, 50);

    lowerBound.textContent = `${pred.lower_bound} hari`;
    centerPred.textContent = `${pred.predicted} hari`;
    upperBound.textContent = `${pred.upper_bound} hari`;

    buildTimeline(pred.predicted, pred.lower_bound, pred.upper_bound);

    resultMessage.textContent = pred.message;
    consultCta.style.display = pred.consult ? "flex" : "none";

    resultCard.style.display = "flex";
}

function buildTimeline(pred, lower, upper) {
    timelineTrack.innerHTML = "";
    const MIN = 15;
    const MAX = 60;
    const toPercent = (v) => ((v - MIN) / (MAX - MIN)) * 100;

    const normalZone = document.createElement("div");
    const nLeft = toPercent(21);
    const nWidth = toPercent(45) - nLeft;
    normalZone.style.cssText = `
        position: absolute; left: ${nLeft}%; width: ${nWidth}%;
        height: 100%; background: rgba(91,173,124,0.15);
        border-left: 2px solid rgba(91,173,124,0.4);
        border-right: 2px solid rgba(91,173,124,0.4);
    `;
    timelineTrack.appendChild(normalZone);

    const rangeBand = document.createElement("div");
    const rLeft = toPercent(lower);
    const rWidth = toPercent(upper) - rLeft;
    rangeBand.style.cssText = `
        position: absolute; left: ${rLeft}%; width: ${rWidth}%;
        height: 100%; background: rgba(123,159,212,0.25); border-radius: 4px;
    `;
    timelineTrack.appendChild(rangeBand);

    const marker = document.createElement("div");
    marker.style.cssText = `
        position: absolute; left: ${toPercent(pred)}%;
        top: -4px; bottom: -4px; width: 4px;
        background: linear-gradient(to bottom, var(--clr-primary), var(--clr-rose));
        border-radius: 2px; transform: translateX(-50%);
        box-shadow: 0 0 8px rgba(212,132,154,0.5);
    `;
    timelineTrack.appendChild(marker);
}

function showError(msg) {
    document.getElementById("errorMsg").innerHTML =
        `${msg}<br><small>Pastikan backend Flask berjalan di <code>http://localhost:5000</code></small>`;
    errorCard.style.display = "flex";
}

function retryPrediction() {
    hideAllResults();
    emptyState.style.display = "flex";
}

function saveToHistory() {
    if (!lastResult) return;
    SiklikaStorage.addEntry({
        cycleLength: lastResult.cycleLength,
        predictedNext: lastResult.predicted,
        label: lastResult.label,
        confidence: lastResult.confidence_pct,
        lower: lastResult.lower_bound,
        upper: lastResult.upper_bound,
    });
    const btn = document.querySelector('[onclick="saveToHistory()"]');
    btn.textContent = "Tersimpan";
    btn.disabled = true;
    setTimeout(() => {
        btn.textContent = "Simpan ke Riwayat";
        btn.disabled = false;
    }, 2000);
}

function askChatbot() {
    if (!lastResult) {
        window.location.href = "chatbot.html";
        return;
    }
    const msg = encodeURIComponent(
        `Prediksi siklus berikutnya saya ${lastResult.predicted} hari (${lastResult.label}). ` +
        `Apakah ini normal dan apa yang perlu saya perhatikan?`
    );
    window.location.href = `chatbot.html?q=${msg}`;
}
