from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.database.connection import engine, Base

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.drift import router as drift_router
from backend.app.api.routes.monitor import router as monitor_router
from backend.app.api.routes.evaluation import router as evaluation_router

from backend.app.core.exceptions import global_exception_handler

# Create FastAPI app
app = FastAPI(
    title="Data Drift Monitoring System",
    description="Industry Level ML Drift Monitoring Backend",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Global exception handler
app.add_exception_handler(
    Exception,
    global_exception_handler,
)

# Include API routes
app.include_router(auth_router)
app.include_router(drift_router)
app.include_router(monitor_router)
app.include_router(evaluation_router)

# Root endpoint
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# Health endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }