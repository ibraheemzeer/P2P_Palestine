"""
P2P Palestine - Main FastAPI Application
Escrow-based Crypto/Fiat Exchange Platform
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import async_engine, get_db, Base, init_db
from app.core.config import get_settings
from app.routes import auth, orders, transactions

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Secure P2P platform for trading USDT against local fiat (USD, ILS, JOD)",
    version="2.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS.split(",") if settings.ALLOWED_HOSTS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    await init_db()


@app.get("/")
async def root():
    """Root endpoint - Health check."""
    return {
        "message": "Welcome to P2P Palestine",
        "status": "running",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint with database connectivity verification."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": settings.APP_NAME
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# Include routers with API versioning prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
