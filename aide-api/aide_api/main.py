"""AIDE API - Main FastAPI Application

REST API server for AIDE Platform providing access to:
- News articles
- KDI policy documents
- Credit rating research reports
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aide_api.config import settings
from aide_api.routers import news, kdi, ratings

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news.router)
app.include_router(kdi.router)
app.include_router(ratings.router)


@app.get("/")
def root():
    """API root endpoint

    Returns basic API information and available endpoints.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "news": "/news",
            "kdi": "/kdi",
            "ratings": "/ratings"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint

    Returns API health status.
    """
    return {
        "status": "healthy",
        "version": settings.api_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "aide_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
