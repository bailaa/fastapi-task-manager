import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import tasks, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app.requests")


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Добавляет заголовок X-Process-Time и пишет в лог метод, путь, статус и время."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method, request.url.path, response.status_code, elapsed * 1000,
        )
        return response


app = FastAPI(title="Менеджер задач", version="1.0.0")
app.add_middleware(ProcessTimeMiddleware)
app.include_router(users.router)
app.include_router(tasks.router)
