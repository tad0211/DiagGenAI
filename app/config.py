import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Safety
    SIMULATION_MODE: bool = True
    SAFETY_BANNER: str = "SIMULATION MODE — NO REAL ECU CONNECTION"

    # App
    APP_NAME: str = "DiagGenAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    BACKEND_API_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'diaggenai.db'}"

    # Vector DB & Embeddings
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "data" / "chroma")
    CHROMA_COLLECTION_NAME: str = "uds_diagnostic_specs"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # mock, openai, local_vllm
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    LOCAL_LLM_API_BASE: str = "http://localhost:8000/v1"

    # Graph
    GRAPH_ENGINE: str = "networkx"  # networkx or neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "diaggenai_secret"

    # Security
    SECRET_KEY: str = "diaggenai-insecure-dev-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

settings = Settings()
