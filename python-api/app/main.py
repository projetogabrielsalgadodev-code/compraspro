import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import configuracoes, importacoes, ofertas, produtos


app = FastAPI(title="Compras PRO API", version="0.2.0")

# CORS: restringir origens em produção, abrir em development
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0", "engine": "agno"}


app.include_router(ofertas.router, prefix="/api/ofertas", tags=["ofertas"])
app.include_router(produtos.router, prefix="/api/produtos", tags=["produtos"])
app.include_router(importacoes.router, prefix="/api/importacoes", tags=["importacoes"])
app.include_router(configuracoes.router, prefix="/api/configuracoes", tags=["configuracoes"])
