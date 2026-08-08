"""ECP inventory-python — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="inventory-python", version="1.5.0", description="Inventory Management (Python FastAPI)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"service": "inventory-python", "status": "healthy", "version": "1.5.0"}
