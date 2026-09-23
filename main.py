from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth
from app.routes import evaluations


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="PaperMark AI Backend",
    description="Backend API for PaperMark AI assignment evaluation.",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================
#
# Frontend is currently running on:
# http://192.168.0.104:3000
#
# Backend is running on:
# http://192.168.0.104:8000
#
# allow_credentials=True is REQUIRED because
# authentication uses the papermark_token cookie.
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.0.104:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTES
# =========================================================

app.include_router(
    auth.router
)

app.include_router(
    evaluations.router
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "PaperMark AI Backend is running.",
        "status": "ok",
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }