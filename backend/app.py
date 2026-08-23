import os
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib

from recommendation_engine import assess_stability, build_chatbot_context, SYMPTOM_KB

app = Flask(__name__)
CORS(app, origins="*")

MODEL_DIR = Path(__file__).resolve().parent / "model"
model = joblib.load(MODEL_DIR / "siklika_model.pkl")
feat_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
global_stats = joblib.load(MODEL_DIR / "global_stats.pkl")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        print(f"Gemini unavailable: {e}")


def build_feature_vector(data: dict) -> tuple[np.ndarray, float, float]:
    history = [float(h) for h in data.get("history", [])]
    cl = float(data["cycle_length"])
    age = float(data.get("age", 25))
    cn = float(data.get("cycle_number", len(history) + 1))

    all_prev = history
    n = len(all_prev)

    lag1 = all_prev[-1] if n >= 1 else cl
    lag2 = all_prev[-2] if n >= 2 else lag1
    lag3 = all_prev[-3] if n >= 3 else lag2

    prev = all_prev if all_prev else [cl]
    mean_all = float(np.mean(prev))
    std_all = float(np.std(prev)) if len(prev) > 1 else 0.0
    mean3 = float(np.mean(prev[-3:])) if len(prev) >= 3 else float(np.mean(prev))
    mean6 = float(np.mean(prev[-6:])) if len(prev) >= 6 else float(np.mean(prev))
    trend = lag1 - lag2
    dev_from_mean = cl - mean_all
    cv_personal = std_all / mean_all if mean_all > 0 else 0.0

    feat_map = {
        "age": age,
        "cycle_number": cn,
        "cycle_length": cl,
        "lag1": lag1,
        "lag2": lag2,
        "lag3": lag3,
        "mean_all": mean_all,
        "std_all": std_all,
        "mean3": mean3,
        "mean6": mean6,
        "trend": trend,
        "dev_from_mean": dev_from_mean,
        "cv_personal": cv_personal,
        "n_recorded": n,
    }

    X = np.array([[feat_map[f] for f in feat_cols]])
    return X, mean_all, std_all


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "gemini": gemini_model is not None,
        "features": feat_cols,
        "global_avg_cycle": round(global_stats["mean"], 1),
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        for field in ["age", "cycle_length"]:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        X, user_avg, user_std = build_feature_vector(data)
        pred = float(np.clip(model.predict(X)[0], 15, 60))

        result = assess_stability(pred, user_avg, user_std)

        return jsonify({
            "success": True,
            "prediction": result,
            "disclaimer": (
                "Estimasi ini dihasilkan dari model statistik berbasis riwayat siklus, "
                "bukan diagnosis medis. Konsultasikan keluhan ke tenaga medis."
            ),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Message is empty"}), 400

        symptom_kw = next(
            (kw for kw in SYMPTOM_KB if kw in message.lower()), None
        )
        context = build_chatbot_context(symptom_kw)

        if gemini_model:
            response = gemini_model.generate_content(f"{context}\n\nPertanyaan: {message}")
            reply = response.text
            mode = "gemini"
        else:
            from recommendation_engine import get_symptom_info
            info = get_symptom_info(symptom_kw or message)
            if info:
                tips = "\n".join(f"- {t}" for t in info["tips"])
                flags = "\n".join(f"- {f}" for f in info["red_flags"])
                reply = (
                    f"**{info['title']}**\n\n"
                    f"{info['info']}\n\n"
                    f"**Tips awal:**\n{tips}\n\n"
                    f"**Segera ke tenaga medis jika:**\n{flags}\n\n"
                    "_Informasi ini bersifat edukatif, bukan pengganti konsultasi medis._"
                )
            else:
                reply = (
                    "Terima kasih sudah bertanya. Coba ketik kata kunci seperti: "
                    "kram, mood, telat, darah, atau keputihan. "
                    "Untuk keluhan serius, konsultasikan langsung ke tenaga medis."
                )
            mode = "kb_fallback"

        return jsonify({"success": True, "reply": reply, "mode": mode})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/symptoms", methods=["GET"])
def symptoms():
    return jsonify({
        "keywords": list(SYMPTOM_KB.keys()),
        "topics": {k: v["title"] for k, v in SYMPTOM_KB.items()},
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
