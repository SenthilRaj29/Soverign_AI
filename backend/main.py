import os
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.llm_router import router as llm_router
from app.api.workbench_router import router as workbench_router
from app.auth.router import router as auth_router
from app.api.admin_router import router as admin_router
from app.db.database import check_database_connection

app = FastAPI(
    title="Sovereign On-Premise Agentic AI Workbench API",
    description="Offline-first, Privacy-Preserving Agentic AI API powered by Gemma 4 & PostgreSQL",
    version="1.0.0"
)

# Enable CORS with configurable frontend origin
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = [frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(llm_router)
app.include_router(workbench_router)

@app.get("/health")
async def root_health():
    db_connected = await check_database_connection()
    return {
        "status": "online" if db_connected else "degraded",
        "system": "Sovereign On-Premise Agentic AI Workbench",
        "database": "healthy" if db_connected else "unavailable",
        "sovereignty": {
            "external_network_allowed": os.getenv("EXTERNAL_NETWORK_ENABLED", "false").lower() == "true",
            "cloud_calls": 0
        }
    }

@app.get("/api/health/database")
async def database_health_check():
    """
    Dedicated safe PostgreSQL database connectivity check.
    Returns HTTP 200 with status healthy if connected, or HTTP 503 if connection fails.
    Never exposes database credentials or raw SQL connection exceptions.
    """
    is_healthy = await check_database_connection()
    if is_healthy:
        return {
            "status": "healthy",
            "database": "postgresql"
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "postgresql",
                "detail": "Database connection temporarily unavailable"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
