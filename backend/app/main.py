import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.core.response import JSONResponse
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware


# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


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
        default_response_class=JSONResponse,
    )

    # Middleware order: outermost first
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
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
from app.routers.user import router as user_router
from app.routers.agent import router as agent_router
from app.routers.llm_config import router as llm_config_router

app.include_router(wo_router)
app.include_router(shipment_router)
app.include_router(inventory_router)
app.include_router(production_router)
app.include_router(recon_router)
app.include_router(conv_router)
app.include_router(alert_router)
app.include_router(user_router)
app.include_router(agent_router)
app.include_router(llm_config_router)

# File upload
from app.routers.upload import router as upload_router
app.include_router(upload_router)

# Static files for uploaded media
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")