import numpy as np


STABILITY_THRESHOLDS = {
    "slight_deviation": 5.0,
    "large_deviation": 10.0,
    "normal_min": 21,
    "normal_max": 45,
}

SYMPTOM_KB = {
    "kram": {
        "title": "Nyeri / Kram Haid (Dismenore)",
        "info": (
            "Kram menstruasi terjadi akibat kontraksi rahim saat mendorong lapisan dinding rahim keluar. "
            "Intensitas bisa ringan hingga berat tergantung individu."
        ),
        "tips": [
            "Kompres hangat di perut bagian bawah selama 15-20 menit.",
            "Olahraga ringan seperti jalan kaki atau peregangan dapat membantu.",
            "Hindari kafein berlebihan dan pastikan hidrasi cukup.",
            "Obat antiinflamasi non-steroid (ibuprofen/mefenamat) bisa membantu, konsultasikan ke apoteker.",
        ],
        "red_flags": [
            "Nyeri sangat hebat hingga tidak dapat beraktivitas.",
            "Nyeri muncul di luar periode menstruasi.",
            "Disertai demam tinggi.",
        ],
    },
    "mood": {
        "title": "Perubahan Mood / PMS",
        "info": (
            "Perubahan mood menjelang haid disebabkan oleh fluktuasi hormon estrogen dan progesteron. "
            "Wajar terjadi 1-2 minggu sebelum menstruasi."
        ),
        "tips": [
            "Tidur teratur 7-9 jam per malam.",
            "Kurangi gula dan makanan olahan.",
            "Olahraga ringan membantu produksi endorfin.",
            "Journaling atau berbicara dengan orang terpercaya.",
        ],
        "red_flags": [
            "Gejala mood sangat mengganggu hingga tidak bisa beraktivitas (PMDD).",
            "Berlangsung lebih dari 2 minggu.",
            "Muncul pikiran untuk menyakiti diri sendiri.",
        ],
    },
    "telat": {
        "title": "Siklus Telat",
        "info": (
            "Siklus di atas 35 hari bisa disebabkan oleh stres, perubahan berat badan, "
            "pola tidur buruk, atau kondisi seperti PCOS dan gangguan tiroid."
        ),
        "tips": [
            "Catat tanggal siklus secara rutin untuk mendeteksi pola lebih awal.",
            "Evaluasi tingkat stres dan kualitas tidur.",
            "Hindari perubahan berat badan yang terlalu drastis.",
        ],
        "red_flags": [
            "Telat lebih dari 45 hari tanpa kehamilan yang dikonfirmasi.",
            "Tidak teratur lebih dari 3 bulan berturut-turut.",
            "Disertai tumbuh bulu berlebihan, jerawat parah, atau kenaikan berat badan signifikan.",
        ],
    },
    "darah": {
        "title": "Perdarahan Berat",
        "info": (
            "Volume normal menstruasi adalah 30-80 mL per siklus. "
            "Dianggap berat jika harus mengganti pembalut setiap 1-2 jam."
        ),
        "tips": [
            "Catat durasi dan volume perdarahan di log siklus.",
            "Istirahat cukup dan konsumsi makanan kaya zat besi.",
            "Hindari aspirin karena dapat memperparah perdarahan.",
        ],
        "red_flags": [
            "Mengganti pembalut setiap jam atau kurang selama lebih dari 2 jam.",
            "Menstruasi berlangsung lebih dari 7 hari.",
            "Gumpalan darah berdiameter lebih dari 2,5 cm.",
            "Disertai pusing hebat atau sesak napas.",
        ],
    },
    "keputihan": {
        "title": "Keputihan",
        "info": (
            "Keputihan normal berwarna bening atau putih susu, tidak berbau menyengat. "
            "Volume meningkat saat fase ovulasi."
        ),
        "tips": [
            "Bersihkan area intim dengan air bersih, hindari sabun berparfum.",
            "Kenakan pakaian dalam katun yang menyerap keringat.",
            "Ganti pakaian dalam secara teratur.",
        ],
        "red_flags": [
            "Warna kuning, hijau, atau abu-abu dengan bau tidak sedap.",
            "Disertai rasa gatal, perih, atau bengkak.",
            "Tekstur seperti keju cottage (indikasi infeksi jamur).",
        ],
    },
}


def assess_stability(predicted: float, user_avg: float, user_std: float) -> dict:
    margin = max(user_std * 1.5, 2.5)
    lower = max(15.0, predicted - margin)
    upper = min(60.0, predicted + margin)
    range_days = upper - lower
    confidence = max(40, min(95, int(100 - range_days * 2.2)))

    deviation = abs(predicted - user_avg) if user_avg else 0
    in_normal = STABILITY_THRESHOLDS["normal_min"] <= predicted <= STABILITY_THRESHOLDS["normal_max"]

    if deviation > STABILITY_THRESHOLDS["large_deviation"] or not in_normal:
        label = "Perlu Perhatian"
        message = (
            f"Estimasi {predicted:.0f} hari menyimpang jauh dari rata-rata pribadimu "
            f"({user_avg:.0f} hari) atau di luar rentang umum 21-45 hari. "
            "Disarankan untuk memantau dan berkonsultasi ke tenaga medis."
        )
        consult = True
    elif deviation > STABILITY_THRESHOLDS["slight_deviation"]:
        label = "Berpotensi Tidak Teratur"
        message = (
            f"Estimasi {predicted:.0f} hari sedikit berbeda dari rata-rata pribadimu "
            f"({user_avg:.0f} hari). Masih dalam batas wajar, pantau siklus berikutnya."
        )
        consult = False
    else:
        label = "Stabil"
        message = (
            f"Estimasi {predicted:.0f} hari konsisten dengan pola siklus pribadimu. "
            "Siklus terlihat teratur."
        )
        consult = False

    return {
        "label": label,
        "confidence_pct": confidence,
        "lower_bound": round(lower, 1),
        "upper_bound": round(upper, 1),
        "predicted": round(predicted, 1),
        "message": message,
        "consult": consult,
    }


def get_symptom_info(keyword: str) -> dict | None:
    kw = keyword.lower()
    for key, data in SYMPTOM_KB.items():
        if key in kw or kw in key:
            return data
    return None


def build_chatbot_context(symptom_keyword: str | None = None) -> str:
    context = (
        "Kamu adalah asisten edukasi kesehatan reproduksi Siklika. "
        "Tugasmu memberikan informasi edukatif seputar siklus menstruasi dan kesehatan reproduksi, "
        "bukan diagnosis medis. Selalu anjurkan konsultasi ke tenaga medis untuk gejala serius. "
        "Gunakan bahasa yang hangat, suportif, dan mudah dipahami remaja. "
        "Jangan merekomendasikan obat resep secara spesifik."
    )

    if symptom_keyword:
        info = get_symptom_info(symptom_keyword)
        if info:
            tips_text = "\n".join(f"- {t}" for t in info["tips"])
            flags_text = "\n".join(f"- {f}" for f in info["red_flags"])
            context += (
                f"\n\nInformasi terstruktur: {info['title']}\n"
                f"{info['info']}\n\n"
                f"Tips:\n{tips_text}\n\n"
                f"Tanda bahaya:\n{flags_text}"
            )

    return context
