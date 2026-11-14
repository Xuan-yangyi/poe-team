from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
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

from app.auth.router import router as auth_router
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


from app.core.deps import get_current_user

# Placeholder work-orders route (will be replaced in Phase 2)
@app.get("/work-orders")
async def work_orders_placeholder(user: dict = Depends(get_current_user)):
    return {"code": 0, "message": "success", "data": []}
