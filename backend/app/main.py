from contextlib import asynccontextmanager
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings
from app.api.routes import router
from app.db.session import Base, engine
from app import models  # noqa: F401 - register SQLAlchemy metadata

class SensitiveRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits={}
    async def dispatch(self, request, call_next):
        sensitive=request.url.path.startswith(settings.api_prefix) and any(x in request.url.path for x in ["/inquiries", "/visits", "/uploads", "/login", "/newsletter", "/contact-messages"])
        if settings.rate_limit_enabled and sensitive:
            now=time.time(); key=request.client.host if request.client else "unknown"
            bucket=self.hits.setdefault(key,[]); bucket[:]=[t for t in bucket if now-t<60]
            if len(bucket)>=30: return JSONResponse(status_code=429,content={"detail":"Too many requests. Please try again shortly."})
            bucket.append(now)
        return await call_next(request)

@asynccontextmanager
async def lifespan(app:FastAPI):
    if settings.environment=="development": Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Indian real-estate marketplace API. Use the Authorize control to test authenticated endpoints with a Firebase ID token.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(SensitiveRateLimitMiddleware)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","X-Dev-User"])
app.include_router(router,prefix=settings.api_prefix)

@app.get("/")
def root(): return {"name":"Aashiyana API","docs":"/docs","health":settings.api_prefix+"/health"}

@app.exception_handler(Exception)
async def unhandled_exception(request,exc):
    # Do not leak SQL or secrets to clients. Production logs should capture traceback at the host.
    return JSONResponse(status_code=500,content={"detail":"An unexpected server error occurred"})
