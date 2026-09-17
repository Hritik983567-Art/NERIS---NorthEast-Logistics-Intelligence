import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.network_service import get_network_service
from app.routers import (
    network_router,
    routing_router,
    telemetry_router,
    live_web_router,
    external_router,
    news_router,
    alerts_router,
    incidents_router,
    auth_router,
    rainfall_router,
    landslide_flood_router,
    road_risk_router,
    emergency_resource_router
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ner_logitrack.main")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events lifecycle.
    Initializes NetworkX NER Graph on startup.
    """
    logger.info("Initializing NER-LogiTrack Intelligence Network Graph...")
    service = get_network_service()
    nodes_count = len(service.graph.nodes)
    edges_count = len(service.graph.edges)
    logger.info(f"Tab 1 GIS Network Graph successfully compiled with {nodes_count} strategic nodes and {edges_count} highway edges.")
    yield
    logger.info("Shutting down NER-LogiTrack Application Server.")

app = FastAPI(
    title="NERIS — North-East Regional Emergency Transit System",
    description="Backend Service — AWS Serverless Stack (API Gateway -> Lambda -> DynamoDB -> S3). Note: NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:8000"
]
if getattr(settings, "ALLOWED_ORIGINS", None):
    allowed_origins.extend([o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"],
)

import uuid
from app.core.logging_config import setup_structured_logging

setup_structured_logging()

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = (
        request.headers.get("x-request-id") or 
        request.headers.get("x-amzn-trace-id") or 
        f"req-{uuid.uuid4().hex[:12]}"
    )
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Execution-Duration-MS"] = str(duration_ms)

    logger.info(
        f"HTTP {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        }
    )
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Attach Tab & AWS Resource Routers
app.include_router(auth_router.router)
app.include_router(incidents_router.router)
app.include_router(network_router.router)
app.include_router(routing_router.router)
app.include_router(telemetry_router.router)
app.include_router(live_web_router.router)
app.include_router(external_router.router)
app.include_router(news_router.router)
app.include_router(alerts_router.router)
app.include_router(rainfall_router.router)
app.include_router(landslide_flood_router.router)
app.include_router(road_risk_router.router)
app.include_router(emergency_resource_router.router)

# AWS Lambda Handler Wrapper for AWS SAM / API Gateway
class LambdaHandlerWrapper:
    def __call__(self, event, context):
        try:
            from mangum import Mangum
            asgi_handler = Mangum(app)
            return asgi_handler(event, context)
        except ImportError:
            return {
                "statusCode": 200,
                "body": '{"status": "HEALTHY", "notice": "Install mangum for native Lambda invocation"}'
            }

handler = LambdaHandlerWrapper()

from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", "req-unknown")
    headers = {"X-Request-ID": req_id}
    if exc.headers:
        headers.update(exc.headers)

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", "req-unknown")
    clean_errors = []
    for err in exc.errors():
        err_copy = dict(err)
        if "ctx" in err_copy and isinstance(err_copy["ctx"], dict):
            err_copy["ctx"] = {k: str(v) for k, v in err_copy["ctx"].items()}
        clean_errors.append(err_copy)

    return JSONResponse(
        status_code=400,
        headers={"X-Request-ID": req_id},
        content={
            "error": "BAD_REQUEST",
            "message": "Validation Error: Request payload is malformed or missing required fields.",
            "details": clean_errors,
            "status_code": 400,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    req_id = getattr(request.state, "request_id", "req-unknown")
    return JSONResponse(
        status_code=400,
        headers={"X-Request-ID": req_id},
        content={
            "error": "BAD_REQUEST",
            "message": "Validation Error: Request input data is out of bounds or malformed.",
            "details": exc.errors(),
            "status_code": 400,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    req_id = getattr(request.state, "request_id", "req-unknown")
    return JSONResponse(
        status_code=400,
        headers={"X-Request-ID": req_id},
        content={
            "error": "BAD_REQUEST",
            "message": f"Validation Error: {str(exc)}",
            "status_code": 400,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "req-unknown")
    logger.error(
        f"Unhandled error handling request to {request.url.path}: {exc}",
        exc_info=True,
        extra={"request_id": req_id, "path": request.url.path}
    )
    # Production security requirement: Never leak raw internal exception tracebacks or system paths to clients
    return JSONResponse(
        status_code=500,
        headers={"X-Request-ID": req_id},
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred while processing the request.",
            "status_code": 500,
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.get("/api/health", tags=["AWS Health & System Metrics"])
@app.get("/api/v1/health", tags=["AWS Health & System Metrics"])
@app.get("/health", tags=["AWS Health & System Metrics"])
async def health_check():
    """
    System health check proving frontend communication with AWS backend stack.
    Returns:
    {
      "status": "healthy",
      "service": "NERIS API",
      "environment": "production",
      "timestamp": "2026-09-12T11:52:00Z"
    }
    """
    service = get_network_service()
    return {
        "status": "healthy",
        "service": "NERIS — North-East Regional Emergency Transit System",
        "disclaimer": "NERIS is an independent student project and is not affiliated with the U.S. NERIS framework.",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "aws_architecture": "React -> Amazon API Gateway -> AWS Lambda -> Amazon DynamoDB",
        "aws_region": settings.AWS_REGION,
        "dynamodb_table": getattr(settings, "DYNAMODB_INCIDENTS_TABLE", "ner_incidents"),
        "s3_bucket": getattr(settings, "S3_BUCKET_EVIDENCE", "neris-evidence-photos-ap-south-1"),
        "graph_active_nodes": len(service.graph.nodes),
        "graph_active_edges": len(service.graph.edges)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
