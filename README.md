# 🧠 HireWise AI — Smart Resume Analyzer & Interview Coach

> An end-to-end AI/ML powered hiring assistant: semantic resume matching, ML scoring, SHAP explainability, AI mock interviews with voice, and multi-role comparison.

---

## ✨ Features

| Feature | Technology |
|---------|-----------|
| 📄 Resume parsing (PDF/DOCX/TXT) | pdfplumber, python-docx |
| 🔬 NLP skill + experience extraction | Custom NER, regex patterns |
| 🤖 ML resume scoring | XGBoost + Random Forest + SHAP |
| 📊 Semantic JD matching | Sentence-BERT (all-MiniLM-L6-v2) |
| 💬 AI interview questions | Claude API (fallback: rule-based) |
| 🎤 Voice input | Web Speech API |
| 📈 SHAP explainability | SHAP TreeExplainer |
| ⚖️ Multi-role comparison | Cosine similarity + skill diff |
| 🗃️ Session persistence | MongoDB (Motor async) |

---

## 🏗️ Architecture

```
hirewise/
├── backend/             # FastAPI Python backend
│   ├── main.py          # App entry point
│   ├── database.py      # MongoDB connection
│   ├── routers/         # API route handlers
│   │   ├── resume.py    # POST /api/resume/analyze
│   │   ├── match.py     # POST /api/match/
│   │   ├── interview.py # POST /api/interview/questions + evaluate
│   │   ├── compare.py   # POST /api/compare/
│   │   └── analytics.py # GET /api/analytics/*
│   ├── services/        # AI/ML logic
│   │   ├── parser.py    # Text extraction
│   │   ├── nlp_extractor.py  # Skill/exp/edu NER
│   │   ├── embedder.py  # Sentence-BERT
│   │   ├── scorer.py    # XGBoost + SHAP
│   │   ├── match_service.py  # JD matching
│   │   ├── question_gen.py   # Claude API
│   │   └── answer_eval.py    # Answer scoring
│   ├── ml/
│   │   ├── train.py     # Full ML training pipeline
│   │   └── model_artifacts/  # Saved models
│   └── models/schemas.py     # Pydantic models
├── frontend/            # React app
│   └── src/
│       ├── pages/       # Upload, Dashboard, Interview, Compare, Analytics
│       ├── utils/api.js # Axios API client
│       └── App.js       # Router + sidebar
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start (Local — Recommended)

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB 6+ (running locally or use Atlas free tier)

---

### Step 1 — Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and add your API key
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY (optional — fallback works without it)
```

### Step 2 — Train the ML Model

```bash
# From backend/ directory (venv active)
python ml/train.py
```

Expected output:
```
==================================================
  HireWise ML Training Pipeline
==================================================
[1/5] Generating synthetic dataset (1200 samples)...
[2/5] Train/Test split: 960 / 240
[3/5] Training models...
      RandomForest  — CV F1: 0.9234 ± 0.0112
      XGBoost       — CV F1: 0.9387 ± 0.0098
[4/5] Best model: XGBoost (CV F1=0.9387)
[5/5] Saving artifacts...
  Accuracy : 93.75%
  F1 Score : 93.87%
```

### Step 3 — Start Backend

```bash
# MongoDB must be running on localhost:27017
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: http://localhost:8000/docs

### Step 4 — Start Frontend

```bash
cd frontend
npm install
npm start
```

App opens at: http://localhost:3000

---

## 🐳 Docker Compose (One Command)

```bash
# From root hirewise/ directory
cp backend/.env.example backend/.env
# Edit .env and add ANTHROPIC_API_KEY if you have one

docker-compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- MongoDB: localhost:27017

---

## 🌐 Using Without API Key

All features work WITHOUT an Anthropic API key:
- ✅ Resume parsing and NLP extraction
- ✅ ML scoring (XGBoost/RF)
- ✅ SHAP explainability
- ✅ JD semantic matching
- ✅ AI interview questions (rule-based fallback)
- ✅ Answer evaluation (embedding similarity)
- ✅ Voice input (browser-native)
- ✅ Multi-role comparison

The Claude API key only enhances question quality. All other AI features use local models.

---

## 📊 ML Pipeline Details

### Synthetic Dataset (ml/train.py)
- 1,200 synthetic resume samples
- Label-conditional generation (Weak/Average/Strong)
- 10 engineered features per sample
- Saved to `model_artifacts/training_data.csv`

### Models Trained
- **Random Forest**: 200 trees, balanced class weights
- **XGBoost**: 200 rounds, subsample=0.8
- Best model selected by 5-fold CV F1

### Switching to Real Data (Kaggle)
1. Download: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
2. Place CSV at `ml/kaggle_resumes.csv`
3. Modify `ml/train.py` to load from CSV instead of synthetic generator
4. Re-run `python ml/train.py`

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resume/analyze` | Upload & analyze resume (multipart) |
| GET  | `/api/resume/session/{id}` | Get session data |
| POST | `/api/match/` | Match resume to job description |
| POST | `/api/interview/questions` | Generate interview questions |
| POST | `/api/interview/evaluate` | Evaluate an answer |
| GET  | `/api/interview/history/{id}` | Get interview history |
| POST | `/api/compare/` | Compare resume against multiple JDs |
| GET  | `/api/analytics/model-metrics` | ML model performance metrics |
| GET  | `/api/analytics/sessions/stats` | Platform usage stats |

Full interactive docs: http://localhost:8000/docs

---

## 🎤 Voice Interview

Voice mode uses the browser's native Web Speech API:
1. Click **🎤 Voice Input** on the interview page
2. Speak your answer clearly
3. Click **⏹ Stop Recording** when done
4. Transcript is added to your text answer
5. Works best in Chrome/Edge

---

## 📈 SHAP Explainability

After training, every resume score includes:
- Feature-level impact scores (positive/negative)
- Visual bar chart on Dashboard
- Natural language feedback derived from feature values

---

## 🛠 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: pdfplumber` | Run `pip install -r requirements.txt` |
| `Model not found` | Run `python ml/train.py` |
| MongoDB connection refused | Start MongoDB: `mongod` or use Docker |
| Voice not working | Use Chrome browser |
| CORS error | Backend must be on port 8000; check proxy in package.json |
| Sentence-transformers slow first run | It downloads ~90MB model on first use |

---

## 🤝 Sharing With Classmates

1. Share the zip / GitHub repo
2. They only need: Python 3.10+, Node 18+, MongoDB running
3. Run `python ml/train.py` once to train the model
4. Start backend + frontend — done!

No API key required for full functionality.

---

## 🏆 Placement Highlights

- **ML pipeline**: XGBoost + Random Forest with 5-fold CV, SHAP
- **NLP**: Named entity recognition, semantic embeddings (BERT)
- **System design**: FastAPI async, MongoDB, Docker, REST API
- **Frontend**: React with Recharts data viz, voice I/O
- **Metrics**: Accuracy, F1, Precision, Recall — all displayed in Analytics
