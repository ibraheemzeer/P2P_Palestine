"""
P2P Palestine - Main FastAPI Application
Escrow-based Crypto/Fiat Exchange Platform
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import async_engine, get_db, Base, init_db
from app.core.config import get_settings
from app.core.rate_limiter import limiter
from app.routes import auth, orders, transactions, admin

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Secure P2P platform for trading USDT against local fiat (USD, ILS, JOD)",
    version="2.0.0",
    debug=settings.DEBUG
)

# Add Rate Limiter to app state
app.state.limiter = limiter


# Custom exception handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "message": "Rate limit exceeded. Please try again later.",
            "limit": str(exc.limit.limit)
        }
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
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


# Include routers with API versioning
app.include_router(auth.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
