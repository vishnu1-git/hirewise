from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import resume, match, interview, compare, analytics

app = FastAPI(
    title="HireWise AI API",
    description="Smart Interview & Resume Analyzer — AI/ML Powered Hiring Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router,    prefix="/api/resume",    tags=["Resume"])
app.include_router(match.router,     prefix="/api/match",     tags=["Match"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(compare.router,   prefix="/api/compare",   tags=["Compare"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "HireWise AI API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
