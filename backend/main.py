"""
SupplyGuard Enterprise Backend Application
FastAPI REST microservices for supply chain and inventory risk management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.routers import (
    auth,
    kpis,
    suppliers,
    materials,
    purchase_orders,
    risk,
    alerts,
    corrective_actions,
    etl
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production-ready REST API for Manufacturing Supply-Chain and Inventory Risk Platform.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React portal access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(kpis.router, prefix=settings.API_V1_STR)
app.include_router(suppliers.router, prefix=settings.API_V1_STR)
app.include_router(materials.router, prefix=settings.API_V1_STR)
app.include_router(purchase_orders.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(corrective_actions.router, prefix=settings.API_V1_STR)
app.include_router(etl.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "SupplyGuard API",
        "version": "1.0.0"
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "project": "SupplyGuard — Manufacturing Supply-Chain and Inventory Risk Platform",
        "docs": "/docs",
        "api_version": "v1"
    }
