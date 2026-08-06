from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config.database import db
from routes.item_routes import router as item_router

app = FastAPI(
    title="MS Helena Tasks Manager",
    description="Backend FastAPI com Supabase estruturado em MCR e SRP"
)

# Configuração de CORS para permitir requisições de qualquer origem (ideal para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(item_router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "API rodando com Docker e conectada ao Supabase!"}