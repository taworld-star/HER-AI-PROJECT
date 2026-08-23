# Siklika 
**Asisten Prediksi Siklus & Edukasi Kesehatan Reproduksi Berbasis AI**

---

## Struktur Project

```
HER AI PROJECT/
├── Menstural_cyclelength.csv      # Dataset sumber
├── Siklika_PRD_v3.md              # Product Requirements Document
│
├── backend/
│   ├── train_cycle_model.py       # ML training pipeline
│   ├── recommendation_engine.py   # Stability assessor + symptom KB
│   ├── app.py                     # Flask REST API
│   └── model/                     # (auto-generated setelah training)
│       ├── siklika_model.pkl
│       ├── feature_cols.pkl
│       └── global_stats.pkl
│
└── frontend/
    ├── index.html                 # Landing Page
    ├── dashboard.html             # Prediksi Siklus
    ├── chatbot.html               # Chatbot Edukasi
    ├── riwayat.html               # Riwayat Siklus
    ├── style.css                  # Design System (semua halaman)
    ├── app.js                     # Shared utilities
    ├── dashboard.js               # Logika halaman prediksi
    ├── chatbot.js                 # Logika chatbot
    └── riwayat.js                 # Logika riwayat + chart
```

---

## Cara Menjalankan

### 1. Training Model (sudah pernah dijalankan)
```bash
python -X utf8 backend/train_cycle_model.py
```

### 2. Jalankan Backend API
```bash
python backend/app.py
```
Server akan berjalan di: **http://localhost:5000**

### 3. Buka Frontend
Buka file `frontend/index.html` langsung di browser, atau gunakan ekstensi Live Server di VS Code.

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/health` | Status server & info model |
| POST | `/api/predict` | Prediksi siklus berikutnya |
| POST | `/api/chat` | Chatbot edukasi (Gemini/KB fallback) |
| GET | `/api/symptoms` | Daftar topik yang didukung KB |

### Contoh Request `/api/predict`
```json
POST http://localhost:5000/api/predict
{
  "age": 23,
  "cycle_length": 28,
  "cycle_number": 5,
  "history": [27, 29, 28, 30]
}
```

### Contoh Response
```json
{
  "success": true,
  "prediction": {
    "label": "Stabil",
    "label_en": "Stable",
    "confidence_pct": 82,
    "predicted": 28.5,
    "lower_bound": 24.3,
    "upper_bound": 32.7,
    "message": "Estimasi siklus berikutnya (28 hari) konsisten ...",
    "consult": false
  },
  "disclaimer": "Estimasi ini dihasilkan dari model statistik..."
}
```

---

## Chatbot Gemini (Opsional)

Untuk mengaktifkan Gemini AI, set environment variable sebelum menjalankan server:
```bash
$env:GEMINI_API_KEY = "your-api-key-here"
python backend/app.py
```

Tanpa API key, chatbot otomatis menggunakan **Knowledge Base fallback** yang tetap memberikan informasi berguna untuk topik: kram, mood, telat, darah, keputihan.

---

## Evaluasi Model (Hasil Training)

| Metrik | Nilai |
|---|---|
| Model | Random Forest Regressor |
| CV-MAE (5-fold GroupKFold) | 3.10 hari |
| MAE hold-out (user baru) | ~2.54 hari |
| Baseline naif (prev=next) | ~2.92 hari |
| Feature terpenting | avg_hist (rata-rata historis personal) |

---

## Disclaimer
Siklika adalah alat informatif berbasis data, **bukan pengganti diagnosa medis**. Selalu konsultasikan kondisi kesehatan reproduksi ke tenaga medis profesional.
