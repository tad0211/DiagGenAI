# DiagGenAI: Automotive Diagnostic Intelligence & Verification Platform

> **An End-to-End Engineering Workbench for ISO 14229-1 (UDS) Specification Ingestion, Deterministic Protocol Validation, Multi-Dimensional Test Synthesis, Stateful Mock ECU Simulation, and ASPICE Traceability.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-Apache_2.0-lightgrey.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-55_Passed-brightgreen.svg)](tests/)

---

## ⚠️ Mandatory Safety Notice & Simulation Scope

```
========================================================================================
SIMULATION ENVIRONMENT — NO PHYSICAL ECU CONNECTION
This platform is a software-defined automotive engineering workstation and simulator.
• DO NOT connect this application to a physical vehicle or production CAN bus.
• DO NOT transmit diagnostic requests to real electronic control units.
• DO NOT implement physical vehicle powertrain or chassis control.
• All AI-synthesized test cases require human engineering verification and sign-off.
========================================================================================
```

---

## Table of Contents

1. [Executive Summary & Motivation](#1-executive-summary--motivation)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Detailed Module Breakdown & How It Works](#3-detailed-module-breakdown--how-it-works)
   - [3.1 Knowledge Base & Vector Ingestion](#31-knowledge-base--vector-ingestion)
   - [3.2 RAG Knowledge Assistant & Semantic Grounding](#32-rag-knowledge-assistant--semantic-grounding)
   - [3.3 UDS Service Explorer & Protocol Definitions](#33-uds-service-explorer--protocol-definitions)
   - [3.4 Interactive Request Builder & Frame Assembler](#34-interactive-request-builder--frame-assembler)
   - [3.5 Deterministic Protocol Validation Engine](#35-deterministic-protocol-validation-engine)
   - [3.6 AI Test Generator & Human-in-the-Loop Review](#36-ai-test-generator--human-in-the-loop-review)
   - [3.7 Verification Coverage Analyzer & Gap Synthesis](#37-verification-coverage-analyzer--gap-synthesis)
   - [3.8 Stateful Mock ECU Simulator & Virtual CAN Bus](#38-stateful-mock-ecu-simulator--virtual-can-bus)
   - [3.9 Automated Test Suite Execution Runner](#39-automated-test-suite-execution-runner)
   - [3.10 Toolchain Automation Exporter (CAPL / Python / Robot)](#310-toolchain-automation-exporter-capl--python--robot)
   - [3.11 ASPICE Bidirectional Traceability Graph](#311-aspice-bidirectional-traceability-graph)
   - [3.12 Specification Change Impact & Test Suite Intelligence](#312-specification-change-impact--test-suite-intelligence)
   - [3.13 Governance, Audit Logging & Formal Reports](#313-governance-audit-logging--formal-reports)
4. [Technology Stack](#4-technology-stack)
5. [Directory Layout](#5-directory-layout)
6. [Database Schema & Data Model](#6-database-schema--data-model)
7. [REST API Reference](#7-rest-api-reference)
8. [Installation & Getting Started](#8-installation--getting-started)
   - [Local Setup](#local-setup)
   - [Docker Deployment](#docker-deployment)
   - [Running Automated Tests](#running-automated-tests)
9. [Verification & Test Results](#9-verification--test-results)

---

## 1. Executive Summary & Motivation

In automotive embedded software engineering, validating **Unified Diagnostic Services (ISO 14229-1)** for Electronic Control Units (ECUs) is a safety-critical, labour-intensive process. Diagnostic engineers spend weeks manually cross-referencing OEM customer diagnostic specifications (CDD/ODX files), writing verification test cases, building low-level CAN byte payloads, checking NRC (Negative Response Code) matrices, and mapping traceability for **ASPICE** compliance.

**DiagGenAI** eliminates these inefficiencies by introducing a software-defined, AI-assisted verification workbench that:
1. **Ingests & Indexes** natural language diagnostic specifications into ChromaDB using dense semantic embeddings.
2. **Retrieves Grounded Specifications** with explicit document, version, and section citations to prevent hallucinations.
3. **Deterministically Validates** diagnostic requests using strict rule-based protocol engines rather than non-deterministic LLM guessing.
4. **Synthesizes Multi-Dimensional Test Suites** across 6 critical dimensions: Positive Nominal, Negative Fault Handling, Boundary Limits, Session Preconditions, Security Access, and Invalid Payloads.
5. **Simulates a Real-Time Mock ECU** with session state machines, seed/key cryptography, environmental sensors, and fault injection over a virtual CAN-FD (`vcan0`) bus.
6. **Exports Production Toolchain Scripts** directly to Python (`python-can` + `pyUDS`), Vector CANoe CAPL (`.can`), and Robot Framework.
7. **Maintains Full ASPICE V-Model Traceability** from specification requirements down to test execution results.

---

## 2. End-to-End System Architecture

```
                                  +---------------------------------------+
                                  |    DIAGNOSTIC SPECIFICATION DOCS     |
                                  |  (ISO 14229-1, OEM BCM Spec v1.0/1.1) |
                                  +---------------------------------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        | Document Ingestion Engine |
                                        | Recursive Markdown Chunker|
                                        +---------------------------+
                                                      |
                                                      v
                                     +---------------------------------+
                                     | ChromaDB Dense Vector Store     |
                                     | (BGE / Sentence-Transformers)   |
                                     +---------------------------------+
                                                      |
                                           Semantic Similarity Search
                                                      |
                                                      v
+-----------------------+               +---------------------------+
|  STREAMLIT FRONTEND   | <===========> |     FASTAPI GATEWAY       |
|  (Light Workstation)  |   REST API    |  (Port :8000 / OpenAPI)   |
+-----------------------+               +---------------------------+
           |                                          |
           |             +----------------------------+----------------------------+
           |             |                            |                            |
           v             v                            v                            v
    +-------------+-------------+              +-------------+              +-------------+
    | Request     | AI Test     |              | Deterministic|              | Stateful    |
    | Builder &   | Synthesis   |              | Rule Engine |              | Mock ECU    |
    | Explorer    | Pipeline    |              | (ISO 14229) |              | (BCM Sim)   |
    +-------------+-------------+              +-------------+              +-------------+
                         |                            |                            |
                         v                            v                            v
               +--------------------------------------------------------------------------+
               |                       RELATIONAL REPOSITORY (SQLite)                     |
               | Documents | Requirements | Services | TestCases | TestResults | AuditLog |
               +--------------------------------------------------------------------------+
                                                      |
                         +----------------------------+----------------------------+
                         |                                                         |
                         v                                                         v
             +-----------------------+                                 +-----------------------+
             | NetworkX Graph Engine |                                 | Automation Exporter   |
             | ASPICE Traceability   |                                 | CAPL / PyUDS / Robot  |
             +-----------------------+                                 +-----------------------+
```

---

## 3. Detailed Module Breakdown & How It Works

### 3.1 Knowledge Base & Vector Ingestion
* **Location:** `app/rag/ingestion.py`, `frontend/knowledge_base.py`
* **Mechanism:**
  - Ingests raw diagnostic requirement documents (`.md`, `.txt`, `.pdf`).
  - Utilizes a recursive character text splitter with semantic overlap to preserve UDS service context, table structures, and DID parameter boundaries.
  - Generates dense vector embeddings using HuggingFace sentence-transformers (`BAAI/bge-small-en-v1.5` / `all-MiniLM-L6-v2`) and persists them into ChromaDB collections.
  - Automatically seeds baseline OEM Body Control Module (BCM) specifications (`v1.0.0` and `v1.1.0`) on initialization.

### 3.2 RAG Knowledge Assistant & Semantic Grounding
* **Location:** `app/rag/retrieval.py`, `app/rag/chains.py`, `frontend/rag_assistant.py`
* **Mechanism:**
  - Engineers query the system in natural language (e.g., *"What is the key algorithm for Security Access Level 1?"*).
  - Retrieves top-$k$ relevant document fragments via cosine similarity in ChromaDB.
  - Synthesizes answers strictly bound to retrieved evidence with document, version, and section citations.
  - **Deterministic Safety Fallback:** If the query is out of scope (e.g., *"How do I calibrate the panoramic sunroof motor?"* when only BCM specs are indexed), the pipeline detects insufficient semantic match and returns an authoritative `SAFETY NOTICE / GROUNDED FALLBACK` rather than hallucinating dangerous diagnostic instructions.

### 3.3 UDS Service Explorer & Protocol Definitions
* **Location:** `app/uds/models.py`, `app/api/services.py`, `frontend/uds_explorer.py`
* **Supported Core ISO 14229 Services:**
  1. `0x10 DiagnosticSessionControl`: Subfunctions `0x01` (Default), `0x02` (Programming), `0x03` (Extended).
  2. `0x11 ECUReset`: Subfunctions `0x01` (HardReset), `0x03` (SoftReset).
  3. `0x22 ReadDataByIdentifier`: DIDs `0xF190` (VIN), `0x0100` (Engine Speed), `0x0200` (Vehicle Speed), `0x0300` (Battery Voltage).
  4. `0x27 SecurityAccess`: Subfunctions `0x01` (RequestSeed), `0x02` (SendKey).
  5. `0x2E WriteDataByIdentifier`: DID `0x0105` (VariantCoding: Region, Lighting, Trailer).
  6. `0x31 RoutineControl`: Subfunctions `0x01` (StartRoutine), `0x03` (RequestRoutineResults), Routine ID `0x0201` (SelfTest).
* **Two-Column Workstation:** Displays services on the left and full technical specifications, subfunctions, parameters, positive response formats, and linked test cases on the right.

### 3.4 Interactive Request Builder & Frame Assembler
* **Location:** `app/uds/request_builder.py`, `frontend/request_builder.py`
* **Mechanism:**
  - Configures diagnostic service, subfunction, DIDs, and payload bytes.
  - Supports the **Suppress Positive Response Message Indication Bit (`0x80`)** (e.g., Subfunction `0x03` becomes `0x83`).
  - Prepares the complete hexadecimal request frame (e.g., `22 F1 90`).
  - Renders live sequence diagrams showing client-to-server UDS interactions.
  - Enables single-click promotion of assembled frames into formal test cases.

### 3.5 Deterministic Protocol Validation Engine
* **Location:** `app/uds/validator.py`, `app/uds/rules.py`, `frontend/validator.py`
* **Why Rule-Based?** In safety-critical automotive systems, LLMs cannot be trusted to validate bit-level protocol constraints. DiagGenAI implements a deterministic rule engine:
  - `RULE-001 Service Supported Check`: Verifies SID is configured for the target ECU.
  - `RULE-002 Subfunction Valid Check`: Validates subfunction ID against ISO 14229 specifications.
  - `RULE-003 Payload Length Boundary`: Ensures request length satisfies min/max DLC.
  - `RULE-004 Parameter Range Check`: Validates that DIDs and routine arguments fall within defined ranges.
  - `RULE-005 Session Precondition Check`: Rejects services requiring Extended/Programming sessions when in Default Session.
  - `RULE-006 Security Precondition Check`: Rejects protected DIDs (e.g., WriteData `0x2E`) if security access is Locked.
  - `RULE-007 Environmental Condition Check`: Locks out dangerous routines if simulated vehicle speed > 0 km/h.
* **Output:** Returns clear `VALID`, `REQUIRES REVIEW`, or `INVALID` verdicts with exact expected NRC codes (e.g., `0x12 SubFunctionNotSupported`, `0x22 ConditionsNotCorrect`, `0x33 SecurityAccessDenied`).

### 3.6 AI Test Generator & Human-in-the-Loop Review
* **Location:** `app/testing/generator.py`, `frontend/test_generator.py`
* **Workflow:**
  - **Step 1:** Engineer inputs requirement prompt or selects a standard template.
  - **Step 2:** Engineer selects desired test dimensions:
    - *Positive Nominal:* Tests valid parameters expecting positive responses.
    - *Negative NRC:* Tests invalid subfunctions, wrong lengths, or out-of-range DIDs expecting negative responses.
    - *Boundary & Range:* Tests boundary extremes for parameters.
    - *Session State:* Verifies execution behavior in incorrect session states.
    - *Security Challenge:* Verifies access control enforcement with invalid keys.
  - **Human Sign-Off Gate:** All synthesized tests are stored with `review_status = PENDING_REVIEW`. Test leads can inspect, edit parameters, and mark tests `APPROVED` or `REJECTED`. Only approved tests are included in production test runs.

### 3.7 Verification Coverage Analyzer & Gap Synthesis
* **Location:** `app/testing/coverage_analyzer.py`, `frontend/coverage.py`
* **Mechanism:**
  - Continuously calculates test coverage across **8 distinct dimensions**:
    1. Requirement Traceability Coverage
    2. UDS Service Coverage
    3. Subfunction Coverage
    4. Positive Path Coverage
    5. Negative (NRC) Robustness Coverage
    6. Session Precondition Coverage
    7. Security Access Coverage
    8. Boundary & Parameter Range Coverage
  - **Gap Detection:** Identifies unexercised scenarios (e.g., *Missing NRC 0x33 SecurityAccessDenied test for DID 0x0105*).
  - **Contextual Synthesis:** Single-click action automatically synthesizes missing test cases to close identified protocol gaps.

### 3.8 Stateful Mock ECU Simulator & Virtual CAN Bus
* **Location:** `app/uds/ecu_simulator.py`, `frontend/simulator.py`
* **Capabilities:**
  - **Diagnostic Session State Machine:** Default Session (resets security to Locked), Extended Diagnostic Session (activates P2/P2* timers), Programming Session.
  - **Security Access Engine:** Seed-key cryptographic challenge (`Key = Seed XOR 0x55AA55AA`). State transitions to `Unlocked` on valid key; sends NRC `0x35 InvalidKey` on mismatch.
  - **Environmental Sensors:** Adjustable vehicle speed slider (km/h) and battery voltage (V).
  - **Fault Injection:** Configurable simulation faults:
    - `TIMEOUT`: Simulates ECU P2 timer expiration (no response).
    - `NRC_22_CONDITIONS`: Enforces safety lockout when simulated speed > 0 km/h.
    - `GARBAGE_RESPONSE`: Simulates bus data corruption.
  - **Virtual CAN Bus Terminal:** Emulates a 500 kbps CAN-FD / ISO-TP channel (`vcan0`) displaying timestamped Tx (`0x7E0`) and Rx (`0x7E8`) frames with protocol interpretations.

### 3.9 Automated Test Suite Execution Runner
* **Location:** `app/testing/executor.py`, `frontend/simulator.py`
* **Execution Options:**
  - Single test execution against the stateful Mock ECU.
  - Batch test suite runner (filterable to Approved Only, Positive Only, Negative Only, or Full Suite).
  - **Automated Verdict & Difference Analysis:** Compares expected response hex against actual response hex with byte-level difference analysis and diagnostic root-cause explanation for failures.
  - Records execution history in the relational database.

### 3.10 Toolchain Automation Exporter (CAPL / Python / Robot)
* **Location:** `app/api/automation.py`, `frontend/automation.py`
* **Supported Export Formats:**
  - **Vector CANoe CAPL (`.can`):** Generates production `testcase` and `testfunction` procedures ready to load into Vector CANoe/vTESTstudio test modules.
  - **Python (`python-can` + `pyUDS` + `pytest`):** Generates standalone test scripts using standard ISO-TP sockets.
  - **Robot Framework (`.robot` / `.yaml`):** Generates keyword-driven automation scripts for CI/CD pipelines.
  - **Verification Matrix (`.csv`):** Exports full verification matrices for spreadsheet audits and engineering reviews.

### 3.11 ASPICE Bidirectional Traceability Graph
* **Location:** `app/graph/traceability_engine.py`, `frontend/traceability.py`
* **Graph Topology:**
  - Uses NetworkX (with Neo4j export compatibility) to model the complete V-Model lifecycle:
    $$\text{Document} \longrightarrow \text{Requirement} \longrightarrow \text{UDS Service} \longrightarrow \text{TestCase} \longrightarrow \text{TestResult}$$
  - **Lineage Queries:** Supports bidirectional traversal to inspect all upstream requirements or downstream execution results for any selected entity.
  - **Orphan & Gap Auditing:** Automatically flags requirements without linked test cases and orphan tests lacking requirement citations.

### 3.12 Specification Change Impact & Test Suite Intelligence
* **Location:** `app/analysis/change_impact.py`, `frontend/change_impact.py`
* **Capabilities:**
  - **Semantic Document Diffing:** Compares baseline specifications (`v1.0.0`) against revised specifications (`v1.1.0`) to detect:
    - *Added Features:* New subfunctions or DIDs.
    - *Removed Features:* Deprecated diagnostic services.
    - *Modified Parameters:* Changed baud rates, session prerequisites, or security access levels.
  - **Impact Propagation:** Uses the traceability graph to flag all affected test cases with `review_status = REQUIRES_RETEST`.
  - **Targeted Regression Suite:** Recommends the minimal regression subset to execute, saving testbench hours.
  - **Test Suite Intelligence:** Identifies duplicate frame signatures and optimizes test suite density.

### 3.13 Governance, Audit Logging & Formal Reports
* **Location:** `app/api/reports.py`, `frontend/human_review.py`, `frontend/reports.py`
* **Governance Features:**
  - **Immutable Audit Trail:** Logs every test creation, modification, review decision, and execution in the `AuditLog` table.
  - **Formal Engineering Reports:** Generates executive verification reports formatted in Markdown, standalone printable HTML, and JSON metrics for ASPICE audits and customer delivery.

---

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Streamlit 1.32+, Custom Enterprise CSS, Streamlit Components |
| **API Backend** | FastAPI, Uvicorn, Starlette, Pydantic v2 |
| **Vector DB & RAG** | ChromaDB, LangChain, HuggingFace Sentence-Transformers (`BGE` / `MiniLM`) |
| **Relational Database** | SQLite (development/local), PostgreSQL (production-ready via SQLAlchemy ORM) |
| **Graph & Traceability** | NetworkX, Neo4j Driver (optional cluster connection) |
| **Automotive Protocols** | ISO 14229-1 (UDS), ISO 15765-2 (ISO-TP), Vector CANoe CAPL, `python-can` |
| **Testing & Quality** | Pytest, Pytest-Asyncio, HTTPX, Coverage.py |
| **DevOps & Containers** | Docker, Docker Compose, Multi-stage builds |

---

## 5. Directory Layout

```
DiagGenAI/
├── app/
│   ├── main.py                     # FastAPI application lifespan & routing
│   ├── config.py                   # Pydantic environment configuration
│   ├── api/                        # REST API routers
│   │   ├── documents.py            # Spec upload and indexing
│   │   ├── rag.py                  # Semantic search and RAG queries
│   │   ├── services.py             # UDS services definitions & coverage
│   │   ├── requests.py             # Request builder and static validation
│   │   ├── tests.py                # Test generation, listing, review workflow
│   │   ├── coverage.py             # 8-dimension coverage analysis & gaps
│   │   ├── simulator.py            # Mock ECU state, transmission, test runner
│   │   ├── automation.py           # CAPL, Python, and Robot script export
│   │   ├── traceability.py         # Graph topology, lineage, and trace matrix
│   │   ├── change_impact.py        # Spec diff, impact analysis, suite intelligence
│   │   └── reports.py              # Markdown, HTML, and JSON reports
│   ├── database/                   # SQLAlchemy ORM, repository & seeder
│   │   ├── models.py               # Document, Service, TestCase, AuditLog models
│   │   ├── repository.py           # Data access repository layer
│   │   └── seed_data.py            # Baseline database seeder
│   ├── rag/                        # RAG & embedding pipeline
│   │   ├── ingestion.py            # Text chunking and embedding generation
│   │   ├── retrieval.py            # ChromaDB vector retrieval & formatting
│   │   ├── chains.py               # Grounded question-answering chain
│   │   └── seed_vector_store.py    # Auto-indexing of synthetic specs
│   ├── uds/                        # Deterministic ISO 14229 engine
│   │   ├── models.py               # Pydantic schemas for UDS frames & NRCs
│   │   ├── rules.py                # Deterministic validation rules catalog
│   │   ├── request_builder.py      # Frame constructor & sequence diagrams
│   │   ├── validator.py            # Protocol validation engine
│   │   └── ecu_simulator.py        # Stateful Mock BCM ECU simulation engine
│   ├── testing/                    # Test generation & execution
│   │   ├── generator.py            # Multi-dimensional test case generator
│   │   ├── coverage_analyzer.py    # Coverage matrix calculation & gap detection
│   │   └── executor.py             # Test execution runner against Mock ECU
│   ├── graph/                      # Traceability
│   │   └── traceability_engine.py  # NetworkX V-Model graph engine
│   └── analysis/                   # Change impact
│       └── change_impact.py        # Spec diff engine & test suite intelligence
├── frontend/                       # Enterprise Streamlit frontend
│   ├── dashboard.py                # Main navigation & Command Center
│   ├── ui_components.py            # Light-palette enterprise design system
│   ├── knowledge_base.py           # Document registry & upload interface
│   ├── rag_assistant.py            # Grounded technical Q&A assistant
│   ├── uds_explorer.py             # Two-column UDS specification browser
│   ├── request_builder.py          # Interactive frame assembler & preview
│   ├── validator.py                # Deterministic rule-based frame validator
│   ├── test_generator.py           # Two-stage test synthesis & review queue
│   ├── coverage.py                 # Multi-dimensional coverage & gap closing
│   ├── simulator.py                # Mock ECU instrument panel & test runner
│   ├── automation.py               # Toolchain script exporter
│   ├── traceability.py             # V-Model relationship diagram & lineage
│   ├── change_impact.py            # Specification diff & impact analysis
│   ├── human_review.py             # Sign-off queue & compliance audit trail
│   └── reports.py                  # Downloadable engineering validation reports
├── data/
│   ├── sample_specs/               # Synthetic OEM BCM specs (v1.0.0 and v1.1.0)
│   ├── chroma/                     # ChromaDB persistent vector database
│   └── diaggenai.db                # SQLite relational database
├── tests/                          # Automated Pytest suite (55 tests)
│   ├── test_phase1.py              # Health, seed data, core UDS endpoints
│   ├── test_phase2.py              # Ingestion, ChromaDB, RAG pipeline & fallbacks
│   ├── test_phase3.py              # Protocol rules, request builder, validation
│   ├── test_phase4.py              # Multi-dimensional test generator & review
│   ├── test_phase5.py              # Coverage metrics & gap closing synthesis
│   ├── test_phase6.py              # Mock ECU state transitions, seed/key, executor
│   ├── test_phase7.py              # Automation export (CAPL, Python, CSV, Robot)
│   ├── test_phase8.py              # Traceability graph, lineage, orphan detection
│   ├── test_phase9.py              # Change impact analysis & suite intelligence
│   └── test_phase10.py             # Formal validation reports (Markdown/HTML/JSON)
├── Dockerfile                      # Production Docker container image
├── docker-compose.yml              # Multi-service composition (App + Neo4j)
├── requirements.txt                # Python package dependencies
├── .env.example                    # Sample environment variables
└── README.md                       # Platform documentation
```

---

## 6. Database Schema & Data Model

DiagGenAI uses SQLAlchemy ORM to manage relational integrity across diagnostic entities:

```
+------------------------+          +-----------------------+
|  SpecificationDocument | 1      * |      Requirement      |
|------------------------+----------+-----------------------|
| id (PK)                |          | id (PK)               |
| name, version          |          | req_id (REQ-UDS-001)  |
| doc_type, file_path    |          | document_id (FK)      |
| upload_date, status    |          | title, text, section  |
+------------------------+          +-----------------------+
            |                                   |
            | 1                                 | 1
            |                                   |
            | *                                 | *
+------------------------+          +-----------------------+
|       UdsService       | 1      * |       TestCase        |
|------------------------+----------+-----------------------|
| id (PK)                |          | id (PK)               |
| service_id_hex (0x22)  |          | test_id (TC-UDS-001)  |
| name, standard_ref     |          | requirement_id (FK)   |
| session_prereq         |          | service_id_hex (FK)   |
| security_prereq        |          | request_hex           |
+------------------------+          | expected_response_hex |
            | 1                     | test_type, confidence |
            |                       | review_status         |
            | *                     +-----------------------+
+------------------------+                      | 1
|     UdsSubfunction     |                      |
|------------------------|                      | *
| id (PK), service_id    |          +-----------------------+
| subfunction_hex (0x01) |          |      TestResult       |
| name, session_prereq   |          |-----------------------|
| security_prereq        |          | id (PK)               |
+------------------------+          | test_id (FK)          |
                                    | outcome (PASS / FAIL) |
                                    | actual_response_hex   |
                                    | diff_analysis         |
                                    | execution_timestamp   |
                                    +-----------------------+
```

---

## 7. REST API Reference

The FastAPI backend exposes 30+ endpoints documenting the entire verification lifecycle (`http://localhost:8000/docs`):

| Domain | Method | Endpoint | Description |
|---|---|---|---|
| **Health & Info** | `GET` | `/api/health` | Service health status & simulation mode |
| | `GET` | `/api/info` | Platform version and active configuration |
| **Specifications** | `GET` | `/api/documents` | List indexed specification documents |
| | `POST` | `/api/documents/upload` | Upload and vectorize new specification |
| **RAG & Search** | `POST` | `/api/rag/query` | Grounded semantic query with citations |
| **UDS Services** | `GET` | `/api/services` | List all supported ISO 14229 services |
| | `GET` | `/api/services/{sid}/coverage` | Get live test coverage for a specific service |
| **Request Builder** | `POST` | `/api/requests/build` | Assemble diagnostic frame & parameters |
| | `POST` | `/api/requests/validate` | Deterministic protocol rule validation |
| | `GET` | `/api/requests/rules` | List configured deterministic rules |
| **Test Cases** | `POST` | `/api/tests/generate` | Synthesize multi-dimensional test suite |
| | `GET` | `/api/tests` | List test cases (filter by status, type, service) |
| | `GET` | `/api/tests/{tid}` | Get single test case details |
| | `PUT` | `/api/tests/{tid}` | Update test case parameters |
| | `POST` | `/api/tests/{tid}/review` | Human review sign-off (APPROVE / REJECT) |
| **Coverage** | `GET` | `/api/coverage` | Fetch 8-dimension coverage telemetry & gaps |
| | `POST` | `/api/coverage/analyze` | Re-analyze coverage across all services |
| | `POST` | `/api/coverage/generate-missing` | Synthesize test cases to close gaps |
| **Simulation** | `GET` | `/api/simulator/state` | Current Mock ECU state (session, security, speed) |
| | `POST` | `/api/simulator/send` | Transmit frame to Mock ECU with fault injection |
| | `POST` | `/api/simulator/environmental` | Update simulated vehicle speed and battery voltage |
| | `POST` | `/api/simulator/reset` | Reset Mock ECU to Default Session & Locked |
| | `POST` | `/api/simulator/execute-test` | Execute a single test case against Mock ECU |
| | `POST` | `/api/simulator/run-suite` | Execute full test suite and return verdicts |
| | `GET` | `/api/simulator/results` | List historical test execution records |
| **Automation** | `POST` | `/api/automation/generate` | Export single test script (CAPL / Python / Robot) |
| | `POST` | `/api/automation/generate-suite` | Export consolidated test suite archive |
| **Traceability** | `GET` | `/api/traceability/graph` | V-Model graph topology (nodes and edges) |
| | `GET` | `/api/traceability/lineage/{id}` | Bidirectional lineage traversal for entity |
| | `GET` | `/api/traceability/matrix` | Full requirements-to-results trace matrix |
| | `GET` | `/api/traceability/orphans` | Audit uncovered requirements and orphan tests |
| **Change Impact** | `POST` | `/api/change-impact/analyze` | Diff specification versions and identify affected tests |
| | `POST` | `/api/change-impact/apply-flags` | Flag impacted tests as `REQUIRES_RETEST` |
| | `GET` | `/api/change-impact/intelligence` | Test suite deduplication and optimization metrics |
| **Reports** | `GET` | `/api/reports/engineering` | Formal Markdown validation report |
| | `GET` | `/api/reports/html` | Standalone printable HTML validation report |
| | `GET` | `/api/reports/summary` | Raw JSON verification metrics summary |

---

## 8. Installation & Getting Started

### Local Setup

#### Prerequisites
* **Python 3.11** installed on your system.
* **Git** installed.

#### 1. Clone the Repository
```bash
git clone https://github.com/tad0211/DiagGenAI.git
cd DiagGenAI
```

#### 2. Create and Activate Virtual Environment
```bash
python3 -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
*(Optional) If using Google Gemini LLM for dynamic expansions, add your API key in `.env`. By default, the application runs fully offline with deterministic rules and local embeddings.*

#### 5. Initialize & Seed Demonstration Data
Populate the database with synthetic BCM specifications and baseline ISO 14229 test cases:
```bash
python -m app.database.seed_data
python -m app.rag.seed_vector_store
```

#### 6. Start the Backend API Server
In terminal window 1:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`

#### 7. Start the Streamlit Frontend Workstation
In terminal window 2:
```bash
streamlit run frontend/dashboard.py --server.port 8501
```
Open your browser and navigate to: `http://localhost:8501`

---

### Docker Deployment

To spin up the entire application stack (FastAPI + Streamlit + Neo4j) via Docker Compose:

```bash
docker-compose up --build -d
```

* **Frontend Workstation:** `http://localhost:8501`
* **FastAPI Swagger Docs:** `http://localhost:8000/docs`
* **Neo4j Graph Browser:** `http://localhost:7474` (User: `neo4j`, Password: `diaggenai_password`)

---

### Running Automated Tests

DiagGenAI includes a comprehensive automated test suite covering all 10 architectural phases:

```bash
pytest tests/ -v
```

To run with coverage reporting:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 9. Verification & Test Results

The platform has been validated against all 55 automated integration tests:

```
============================== test session starts ==============================
collected 55 items

tests/test_phase1.py::test_health_endpoint PASSED                         [  1%]
tests/test_phase1.py::test_info_endpoint PASSED                           [  3%]
tests/test_phase1.py::test_database_seeded_data PASSED                    [  5%]
tests/test_phase1.py::test_request_builder PASSED                         [  7%]
tests/test_phase1.py::test_deterministic_validator_valid PASSED           [  9%]
tests/test_phase1.py::test_deterministic_validator_unsupported_service PASSED [ 10%]
tests/test_phase1.py::test_deterministic_validator_session_prerequisite PASSED [ 12%]
tests/test_phase1.py::test_mock_ecu_simulation PASSED                     [ 14%]
tests/test_phase1.py::test_coverage_and_reports_endpoints PASSED          [ 16%]
tests/test_phase10.py::test_engineering_markdown_report_endpoint PASSED   [ 18%]
tests/test_phase10.py::test_engineering_html_report_endpoint PASSED       [ 20%]
tests/test_phase10.py::test_engineering_summary_endpoint PASSED           [ 21%]
tests/test_phase2.py::test_document_ingestion_chunking PASSED             [ 23%]
tests/test_phase2.py::test_embeddings_generation PASSED                   [ 25%]
tests/test_phase2.py::test_chroma_vector_store_retrieval PASSED           [ 27%]
tests/test_phase2.py::test_rag_pipeline_valid_query PASSED                [ 29%]
tests/test_phase2.py::test_rag_pipeline_insufficient_evidence PASSED      [ 30%]
tests/test_phase2.py::test_rag_query_endpoint PASSED                      [ 32%]
tests/test_phase2.py::test_rag_query_endpoint_missing_evidence PASSED     [ 34%]
tests/test_phase3.py::test_service_coverage_endpoint PASSED               [ 36%]
tests/test_phase3.py::test_validation_rules_registry_endpoint PASSED      [ 38%]
tests/test_phase3.py::test_request_builder_suppress_bit PASSED            [ 40%]
tests/test_phase3.py::test_validator_parameter_range_violation PASSED     [ 41%]
tests/test_phase3.py::test_validator_environmental_condition_violation PASSED [ 43%]
tests/test_phase3.py::test_validator_prerequisite_review PASSED           [ 45%]
tests/test_phase3.py::test_generate_test_from_request_builder PASSED      [ 47%]
tests/test_phase4.py::test_direct_generator_dimensions_and_fields PASSED  [ 49%]
tests/test_phase4.py::test_api_generate_tests_endpoint PASSED             [ 50%]
tests/test_phase4.py::test_api_list_tests_with_filters PASSED             [ 52%]
tests/test_phase4.py::test_api_get_single_test PASSED                     [ 54%]
tests/test_phase4.py::test_api_update_and_review_workflow PASSED          [ 56%]
tests/test_phase5.py::test_coverage_analyzer_metrics_calculation PASSED   [ 58%]
tests/test_phase5.py::test_gap_detection_structure PASSED                 [ 60%]
tests/test_phase5.py::test_generate_missing_tests_closes_gaps PASSED      [ 61%]
tests/test_phase5.py::test_api_get_coverage PASSED                        [ 63%]
tests/test_phase5.py::test_api_analyze_coverage PASSED                    [ 65%]
tests/test_phase5.py::test_api_generate_missing_tests PASSED              [ 67%]
tests/test_phase6.py::test_simulator_session_transitions PASSED           [ 69%]
tests/test_phase6.py::test_simulator_security_access_seed_key PASSED      [ 70%]
tests/test_phase6.py::test_simulator_write_did_protection PASSED          [ 72%]
tests/test_phase6.py::test_simulator_fault_injection PASSED               [ 74%]
tests/test_phase6.py::test_test_executor_single_and_suite PASSED          [ 76%]
tests/test_phase6.py::test_api_simulator_endpoints PASSED                 [ 78%]
tests/test_phase7.py::test_generate_single_python_template PASSED         [ 80%]
tests/test_phase7.py::test_generate_single_capl_template PASSED           [ 81%]
tests/test_phase7.py::test_generate_single_generic_and_csv_templates PASSED [ 83%]
tests/test_phase7.py::test_generate_suite_python_and_csv PASSED           [ 85%]
tests/test_phase8.py::test_traceability_engine_topology PASSED            [ 87%]
tests/test_phase8.py::test_traceability_engine_lineage PASSED             [ 89%]
tests/test_phase8.py::test_traceability_engine_orphans_and_matrix PASSED  [ 90%]
tests/test_phase8.py::test_api_traceability_endpoints PASSED              [ 92%]
tests/test_phase9.py::test_change_impact_engine_analysis PASSED           [ 94%]
tests/test_phase9.py::test_apply_impact_flags PASSED                      [ 96%]
tests/test_phase9.py::test_test_suite_intelligence PASSED                 [ 98%]
tests/test_phase9.py::test_api_change_impact_endpoints PASSED             [100%]

============================== 55 passed in 8.77s ==============================
```

---

## 10. Contributing & Author

Developed by **Tejas Dandwate** ([@tad0211](https://github.com/tad0211)).

For questions, feature proposals, or academic inquiries regarding software-defined automotive diagnostic verification, please open an issue in the GitHub repository.

---

## 11. License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
