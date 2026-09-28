# DiagGenAI: AI-Powered UDS Diagnostic Test Generation & Validation Assistant

> **From Diagnostic Requirements to Validated UDS Test Cases and Automation Templates**

---

## 🚨 MANDATORY SAFETY / SCOPE NOTICE
```
SIMULATION MODE — NO REAL ECU CONNECTION
This application is an academic engineering assistant.
DO NOT connect to a real vehicle.
DO NOT transmit diagnostic messages to physical ECUs.
DO NOT implement real-world vehicle control.
All AI-generated outputs require human review and sign-off.
```

---

## 1. Project Overview & Architecture
**DiagGenAI** bridges the gap between automotive OEM/ECU diagnostic specifications (ISO 14229-1) and automated verification test suites (pyUDS, Vector CAPL, Robot Framework).

```
                    USER
                     |
                     v
             STREAMLIT FRONTEND
                     |
                     v
             FASTAPI BACKEND
                     |
                     v
               LANGCHAIN RAG
                     |
          +----------+----------+
          |                     |
          v                     v
      CHROMADB              APPROVED LLM
          ^
          |
    BGE / E5 EMBEDDINGS
```

In addition, the FastAPI backend communicates with:
- **SQLite / PostgreSQL:** Entity tables (documents, services, requirements, test cases, test results, reviews, audit logs).
- **Deterministic UDS Validator:** Protocol-level rule engine enforcing ISO 14229-1 syntax, session, security, and DID limits.
- **Mock ECU Simulator:** High-fidelity simulation of an automotive electronic control unit (BCM) supporting positive/negative responses, NRCs, and fault injection.
- **Traceability Graph:** NetworkX / Neo4j mapping from Requirements to Services, Scenarios, Tests, and Execution outcomes.

---

## 2. Mandatory Technology Stack
- **Frontend:** Streamlit
- **API & Services:** FastAPI, Uvicorn, Pydantic
- **Vector Database:** ChromaDB
- **Embeddings:** BGE / E5 / Sentence Transformers
- **RAG Orchestration:** LangChain
- **Structured Database:** SQLite (PostgreSQL migration-ready SQLAlchemy models)
- **Graph / Traceability:** NetworkX & Neo4j driver
- **Containerization:** Docker & Docker Compose

---

## 3. Directory Structure
```
DiagGenAI/
├── app/
│   ├── main.py                  # FastAPI Application & Lifespan
│   ├── config.py                # Pydantic Settings
│   ├── api/                     # REST API Routers
│   │   ├── documents.py
│   │   ├── services.py
│   │   ├── requests.py
│   │   ├── tests.py
│   │   ├── coverage.py
│   │   ├── automation.py
│   │   ├── reports.py
│   │   ├── traceability.py
│   │   ├── change_impact.py
│   │   └── simulator.py
│   ├── rag/                     # RAG & Embedding Pipeline
│   ├── uds/                     # ISO 14229-1 Protocol Rules & Validator
│   │   ├── models.py
│   │   ├── rules.py
│   │   ├── request_builder.py
│   │   └── validator.py
│   ├── testing/                 # Test Generation & Mock ECU
│   ├── traceability/            # Traceability Graph Engine
│   ├── change_impact/           # Spec Difference Analyzer
│   └── database/                # SQLAlchemy Models, Repository & Seeder
│       ├── models.py
│       ├── repository.py
│       └── seed_data.py
├── frontend/
│   ├── dashboard.py             # Streamlit Main Dashboard & Navigation
│   ├── knowledge_base.py
│   ├── uds_explorer.py
│   ├── request_builder.py
│   ├── validator.py
│   ├── simulator.py
│   ├── automation.py
│   ├── traceability.py
│   ├── change_impact.py
│   └── reports.py
├── data/
│   ├── sample_specs/            # Synthetic BCM Specs (v1.0, v1.1)
│   └── diaggenai.db             # SQLite Database
├── tests/
│   └── test_phase1.py           # Pytest Suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Quick Start & Execution

### Option A: Local Python Environment
1. Create and activate a virtual environment (Python 3.11):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Initialize and seed synthetic demonstration data:
   ```bash
   python -m app.database.seed_data
   ```
3. Run FastAPI Backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Run Streamlit Frontend:
   ```bash
   streamlit run frontend/dashboard.py --server.port 8501
   ```
5. Run Pytest Suite:
   ```bash
   pytest tests/ -v
   ```

### Option B: Docker Compose
```bash
docker-compose up --build
```
- Frontend: `http://localhost:8501`
- Backend API Docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`
