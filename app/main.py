from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.routes import auth
from app.routes import evaluations
from app.routes import analytics


app = FastAPI(
    title="PaperMark AI API",
    version="1.0.0",
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.101:3000",
        "http://192.168.0.104:3000",
        "https://paper-mark-ai-frontend.vercel.app",
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
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

app.include_router(
    analytics.router
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message":
            "PaperMark AI API is running."
    }


@app.get("/health")
def health():

    return {
        "status":
            "ok"
    }