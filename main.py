from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from routes.user import router as user_router
from routes.crop import router as crop_router
from routes.daily_log import router as log_router
from routes.task import router as task_router
from routes.recommendation import router as rec_router
from models.verification import VerificationCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(crop_router)
app.include_router(log_router)
app.include_router(task_router)
app.include_router(rec_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException %s %s", request.url, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_exception", "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error %s %s", request.url, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "server_error", "detail": "Internal server error"},
    )


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Agop API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
