from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.item_routes import router as item_router


app = FastAPI(
    title="MS Helena Tasks Manager",
    description="Backend FastAPI com Supabase estruturado em MCR e SRP"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(item_router)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "API rodando com Docker e conectada ao Supabase!"
    }