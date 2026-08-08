"""ECP ai-service-python — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ai-service-python", version="1.5.0", description="AI/NLP Service (Python + Transformers + FAISS)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"service": "ai-service-python", "status": "healthy", "version": "1.5.0"}
