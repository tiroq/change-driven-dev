"""
FastAPI application for change-driven-dev.
UI-first, stack-agnostic engineering control system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import projects_router, tasks_router, change_requests_router, artifacts_router
from app.api.websocket import router as websocket_router
from app.api.phase import router as phase_router
from app.api.gates import router as gates_router

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
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
