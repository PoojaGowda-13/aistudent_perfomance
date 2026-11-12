"""
FastAPI application entry point — Student AI Platform.
Serves both the REST API and the static HTML frontend.
"""
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import get_settings
from app.database import init_db
from app.routers import auth, students, academic, agents, resume, admin
from app.observability.metrics import metrics_endpoint

settings = get_settings()
logger = structlog.get_logger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", app=settings.app_name, version=settings.app_version)
    await init_db()
    logger.info("database_initialized")
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Student Performance & Career Guidance System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(academic.router)
app.include_router(agents.router)
app.include_router(resume.router)
app.include_router(admin.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/metrics")
async def prometheus_metrics():
    return await metrics_endpoint()


# Serve the HTML frontend at the root
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
@app.get("/register", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/resume", response_class=HTMLResponse)
@app.get("/interview", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def serve_frontend():
    frontend_html = STATIC_DIR / "index.html"
    if frontend_html.exists():
        return FileResponse(frontend_html)
    return HTMLResponse("<h1>Frontend not found. See /docs for API.</h1>")
