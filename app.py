from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import init_db
from api.routes import router as api_router

# Create FastAPI app
app = FastAPI(
    title="SmarTest API",
    description="AI Question Generation and Evaluation System for Artificial Intelligence Course",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
def startup_event():
    """Initialize database on application startup."""
    init_db()
    print("=" * 60)
    print("✓ Database initialized successfully")
    print("✓ SmarTest API is ready")
    print("=" * 60)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("📖 Alternative Docs: http://localhost:8000/redoc")
    print("=" * 60)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "message": "SmarTest API is running!",
        "status": "success",
        "version": "1.0.0",
        "documentation": "/docs",
        "alternative_docs": "/redoc"
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SmarTest Backend"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
