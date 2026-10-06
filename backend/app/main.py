"""Fresh API composition: register released vertical slices only."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api import bootstrap, catalog, guide, cart, orders, navigation, activity
from app.mercury.router import router as mercury_router
from app.human.router import router as human_router
from app.core.config import get_settings
from app.core.database import engine, init_db
from app.core.errors import AppError


def create_app(database_engine=None) -> FastAPI:
    bind = database_engine if database_engine is not None else engine

    @asynccontextmanager
    async def lifespan(_app):
        init_db(bind)
        from app.services.guide_run_service import recover_interrupted_runs, open_run_lifecycle, shutdown_runs
        recover_interrupted_runs(bind)
        open_run_lifecycle(bind)
        from app.services.memory_background import MemoryWorker
        memory_worker = MemoryWorker(bind)
        memory_worker.start()
        try:
            yield
        finally:
            try:
                memory_worker.stop()
            finally:
                shutdown_runs(bind)

    app = FastAPI(title='Ceres2 API', version='0.1.0', lifespan=lifespan)
    app.include_router(bootstrap.router)
    app.include_router(catalog.router)
    app.include_router(guide.router)
    app.include_router(navigation.router)
    app.include_router(activity.router)
    app.include_router(mercury_router)
    app.include_router(human_router)
    app.include_router(cart.router)
    app.include_router(orders.router)
    images = get_settings().root_dir / 'data/images'
    if images.is_dir():
        app.mount('/media/images', StaticFiles(directory=images), name='product_images')

    @app.exception_handler(AppError)
    async def application_error(_request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return app


app = create_app()
