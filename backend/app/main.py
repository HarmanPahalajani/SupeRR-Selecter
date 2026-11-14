from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.router import api_v1_router

app = FastAPI(
    title="SupeRR Intelligence API",
    description="Cricket Scouting, Auction Analytics & Squad Decision Platform",
    version="1.0.0"
)

# Configure CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.get("/")
def root():
    return {
        "product": "SupeRR Intelligence",
        "version": "1.0.0",
        "status": "Operational",
        "docs_url": "/docs",
        "api_prefix": "/api/v1"
    }
