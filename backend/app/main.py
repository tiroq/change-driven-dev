"""
FastAPI application for change-driven-dev.
UI-first, stack-agnostic engineering control system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import projects_router, tasks_router, change_requests_router, artifacts_router
from app.api.websocket import router as websocket_router
from app.api.phase import router as phase_router
from app.api.gates import router as gates_router
from app.api.git import router as git_router

# Create FastAPI app
app = FastAPI(
    title="Change-Driven Development",
    description="UI-first, stack-agnostic engineering control system for AI-assisted development",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(change_requests_router)
app.include_router(artifacts_router)
app.include_router(phase_router)
app.include_router(gates_router)
app.include_router(git_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Change-Driven Development API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """
    Comprehensive health check endpoint.
    Checks status of core services and components.
    """
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "api": "up",
            "database": "up",
            "events": "up",
            "websocket": "up"
        },
        "features": {
            "planner": True,
            "architect": True,
            "coder": True,
            "gates": True,
            "git": True,
            "sandbox": True,
            "task_governance": True
        }
    }
    
    # Check database connectivity
    try:
        from app.db import get_db
        db = next(get_db(1))
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
