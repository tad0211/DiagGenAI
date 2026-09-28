from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.repository import init_db
from app.database.seed_data import seed_database
from app.api.documents import router as doc_router
from app.api.services import router as services_router
from app.api.requests import router as requests_router
from app.api.tests import router as tests_router
from app.api.coverage import router as coverage_router
from app.api.automation import router as automation_router
from app.api.reports import router as reports_router
from app.api.traceability import router as traceability_router
from app.api.change_impact import router as change_impact_router
from app.api.simulator import router as simulator_router
from app.api.rag import router as rag_router
from app.rag.seed_vector_store import seed_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema, seed synthetic demo data, and initialize vector store
    init_db()
    seed_database()
    try:
        seed_vector_store()
    except Exception as e:
        print(f"[WARN] Vector store init: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered UDS Diagnostic Test Generation & Validation Assistant API",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(doc_router)
app.include_router(services_router)
app.include_router(requests_router)
app.include_router(tests_router)
app.include_router(coverage_router)
app.include_router(automation_router)
app.include_router(reports_router)
app.include_router(traceability_router)
app.include_router(change_impact_router)
app.include_router(simulator_router)
app.include_router(rag_router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": settings.SAFETY_BANNER,
        "simulation_mode": settings.SIMULATION_MODE,
        "db": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
    }

@app.get("/api/info", tags=["Health"])
def system_info():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "safety_banner": settings.SAFETY_BANNER,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "vector_db": "ChromaDB",
        "llm_provider": settings.LLM_PROVIDER,
        "graph_engine": settings.GRAPH_ENGINE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
