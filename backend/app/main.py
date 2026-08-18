from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL
from app.tasks.routes import router as tasks_router
from app.habits.routes import router as habits_router
from app.finance.routes import router as finance_router

app = FastAPI(title="Helena Task Manager API — Beta")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router, prefix="/api")
app.include_router(habits_router, prefix="/api")
app.include_router(finance_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
