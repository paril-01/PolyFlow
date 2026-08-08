"""ECP pricing-python — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="pricing-python", version="1.5.0", description="Dynamic Pricing Engine (Python FastAPI + ML)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"service": "pricing-python", "status": "healthy", "version": "1.5.0"}
