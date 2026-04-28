🧠 HireWise AI — Resume Analyzer & Interview Assistant

A full-stack AI/ML project that analyzes resumes, scores candidates, matches them with job descriptions, and provides AI-based interview practice.

---

Features

- Resume parsing (PDF, DOCX, TXT) using pdfplumber and python-docx  
- NLP-based skill and experience extraction  
- ML-based resume scoring using XGBoost and Random Forest  
- Semantic job description matching using Sentence-BERT  
- AI-generated interview questions (Claude API with fallback)  
- Voice input using Web Speech API  
- SHAP-based model explainability  
- Multi-role comparison of resumes  
- Session storage using MongoDB  

---

Architecture

hirewise/
- backend/ (FastAPI)
  - routers/ (API endpoints)
  - services/ (ML + NLP logic)
  - ml/ (training pipeline and saved models)
- frontend/ (React)
- docker-compose.yml

---

Tech Stack

- Backend: FastAPI, Python  
- Frontend: React.js  
- Database: MongoDB  
- ML/NLP: XGBoost, Random Forest, Sentence-BERT, SHAP  
- APIs: Claude (optional)  

---

Setup (Local)

Backend

cd backend  
python -m venv venv  
venv\Scripts\activate  
pip install -r requirements.txt  

Run training:

python ml/train.py  

Start backend:

python -m uvicorn main:app --reload  

---

Frontend

cd frontend  
npm install  
npm start  

---

Docker (optional)

docker-compose up --build  

---

ML Pipeline

- Synthetic dataset generation (~1200 samples)  
- Feature engineering (skills, experience, etc.)  
- Model training:
  - Random Forest  
  - XGBoost  
- Model selection using cross-validation (F1 score)  
- SHAP used for explainability  

---

API Endpoints

- POST /api/resume/analyze  
- POST /api/match  
- POST /api/interview/questions  
- POST /api/interview/evaluate  
- POST /api/compare  
- GET /api/analytics  

Docs: http://localhost:8000/docs  

---

Notes

- Works without external API keys (Claude is optional)  
- First run may download embedding model (~90MB)  
- MongoDB must be running locally or via Atlas  

---

Project Highlights

- Built complete ML pipeline with evaluation metrics (Accuracy, F1, Precision, Recall)  
- Implemented semantic matching using embeddings  
- Designed scalable backend with FastAPI  
- Integrated explainable AI using SHAP  
- Developed interactive frontend with real-time analysis  

---

Author

Vishnu
