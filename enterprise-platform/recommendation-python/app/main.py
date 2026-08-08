"""ECP recommendation-python — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="recommendation-python", version="1.5.0", description="Recommendation Engine (Python + scikit-learn)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"service": "recommendation-python", "status": "healthy", "version": "1.5.0"}
