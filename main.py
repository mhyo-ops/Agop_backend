from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from models.user import User
from models.crop import Crop
from models.daily_log import DailyLog
from models.recommendation import Recommendation
from models.task import Task
from routes.user import router as user_router
from routes.crop import router as crop_router
from routes.daily_log import router as log_router
from routes.task import router as task_router
from routes.recommendation import router as rec_router

Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root():
    return {"message": "Agop API is running"}
