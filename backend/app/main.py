from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok"}


# Auth
from app.auth.router import router as auth_router
app.include_router(auth_router)

# Business domains
from app.routers.work_order import router as wo_router
from app.routers.shipment import router as shipment_router
from app.routers.inventory import router as inventory_router
from app.routers.production import router as production_router
from app.routers.reconciliation import router as recon_router
from app.routers.conversation import router as conv_router
from app.routers.alert import router as alert_router

app.include_router(wo_router)
app.include_router(shipment_router)
app.include_router(inventory_router)
app.include_router(production_router)
app.include_router(recon_router)
app.include_router(conv_router)
app.include_router(alert_router)