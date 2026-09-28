import json
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, select, update, delete, desc, func
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import (
    Base, Document, Service, Subfunction, Parameter, Requirement,
    TestCase, TestResult, Review, Coverage, Traceability,
    SpecificationVersion, ChangeEvent, AuditLog, User
)

# Connect args specific to SQLite (check_same_thread=False for FastAPI/Streamlit multi-threading)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

# ==================== Repository Helpers ====================

class DiagRepository:
    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_session(self) -> Session:
        if self._db is not None:
            return self._db
        return SessionLocal()

    # --- Audit Log ---
    def log_audit(self, action: str, entity_type: str, entity_id: str, details: str = "", user: str = "diagnostic_engineer", db: Optional[Session] = None):
        session = db or self._get_session()
        should_close = db is None and self._db is None
        try:
            entry = AuditLog(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id),
                details=details,
                timestamp=datetime.datetime.utcnow()
            )
            session.add(entry)
            session.commit()
        finally:
            if should_close:
                session.close()

    def get_audit_logs(self, limit: int = 50) -> List[AuditLog]:
        session = self._get_session()
        try:
            return session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
        finally:
            if self._db is None:
                session.close()

    # --- Documents ---
    def get_documents(self, doc_type: Optional[str] = None) -> List[Document]:
        session = self._get_session()
        try:
            q = session.query(Document)
            if doc_type:
                q = q.filter(Document.doc_type == doc_type)
            return q.order_by(Document.id).all()
        finally:
            if self._db is None:
                session.close()

    def add_document(self, name: str, version: str, doc_type: str, file_path: str = "", metadata_dict: dict = None) -> Document:
        session = self._get_session()
        try:
            doc = Document(
                name=name,
                version=version,
                doc_type=doc_type,
                file_path=file_path,
                metadata_json=json.dumps(metadata_dict or {}),
                status="INDEXED"
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            self.log_audit("UPLOAD_DOC", "Document", str(doc.id), f"Uploaded {name} v{version}", db=session)
            return doc
        finally:
            if self._db is None:
                session.close()

    # --- Services & Subfunctions ---
    def get_services(self) -> List[Service]:
        session = self._get_session()
        try:
            from sqlalchemy.orm import selectinload
            return session.query(Service).options(
                selectinload(Service.subfunctions),
                selectinload(Service.parameters)
            ).order_by(Service.service_id_hex).all()
        finally:
            if self._db is None:
                session.close()

    def get_service_by_hex(self, service_hex: str) -> Optional[Service]:
        session = self._get_session()
        try:
            from sqlalchemy.orm import selectinload
            clean_hex = service_hex.strip().upper()
            if not clean_hex.startswith("0X"):
                clean_hex = "0X" + clean_hex
            return session.query(Service).options(
                selectinload(Service.subfunctions),
                selectinload(Service.parameters)
            ).filter(func.upper(Service.service_id_hex) == clean_hex).first()
        finally:
            if self._db is None:
                session.close()

    # --- Requirements ---
    def get_requirements(self) -> List[Requirement]:
        session = self._get_session()
        try:
            return session.query(Requirement).order_by(Requirement.req_id).all()
        finally:
            if self._db is None:
                session.close()

    # --- Test Cases ---
    def get_test_cases(self, review_status: Optional[str] = None, test_type: Optional[str] = None) -> List[TestCase]:
        session = self._get_session()
        try:
            q = session.query(TestCase)
            if review_status:
                q = q.filter(TestCase.review_status == review_status)
            if test_type:
                q = q.filter(TestCase.test_type == test_type)
            return q.order_by(TestCase.test_id).all()
        finally:
            if self._db is None:
                session.close()

    def get_test_case_by_id(self, test_id: str) -> Optional[TestCase]:
        session = self._get_session()
        try:
            return session.query(TestCase).filter(TestCase.test_id == test_id).first()
        finally:
            if self._db is None:
                session.close()

    def add_test_case(self, test_data: dict) -> TestCase:
        session = self._get_session()
        try:
            tc = TestCase(
                test_id=test_data.get("test_id"),
                objective=test_data.get("objective", ""),
                requirement_id=test_data.get("requirement_id"),
                service_id_hex=test_data.get("service_id_hex", ""),
                subfunction_hex=test_data.get("subfunction_hex"),
                preconditions=test_data.get("preconditions", "Default preconditions"),
                session=test_data.get("session", "DefaultSession"),
                security_state=test_data.get("security_state", "Locked"),
                request_hex=test_data.get("request_hex", ""),
                expected_response_hex=test_data.get("expected_response_hex", ""),
                pass_criteria=test_data.get("pass_criteria", "Positive response received"),
                fail_criteria=test_data.get("fail_criteria", "NRC or timeout"),
                test_type=test_data.get("test_type", "POSITIVE"),
                source_evidence=test_data.get("source_evidence", ""),
                generation_rationale=test_data.get("generation_rationale", ""),
                confidence=test_data.get("confidence", 0.95),
                review_status=test_data.get("review_status", "PENDING_REVIEW")
            )
            session.add(tc)
            session.commit()
            session.refresh(tc)
            self.log_audit("CREATE_TEST", "TestCase", tc.test_id, f"Created {tc.test_type} test for {tc.service_id_hex}", db=session)
            return tc
        finally:
            if self._db is None:
                session.close()

    def update_test_review(self, test_id: str, decision: str, reviewer: str, comment: str) -> Optional[TestCase]:
        session = self._get_session()
        try:
            tc = session.query(TestCase).filter(TestCase.test_id == test_id).first()
            if not tc:
                return None
            tc.review_status = decision
            rev = Review(
                test_case_id=tc.id,
                reviewer=reviewer,
                decision=decision,
                comment=comment,
                test_version=tc.version
            )
            session.add(rev)
            session.commit()
            session.refresh(tc)
            self.log_audit("REVIEW_TEST", "TestCase", tc.test_id, f"Review decision {decision} by {reviewer}", db=session)
            return tc
        finally:
            if self._db is None:
                session.close()

    def update_test_case(self, test_id: str, test_data: dict) -> Optional[TestCase]:
        session = self._get_session()
        try:
            tc = session.query(TestCase).filter(TestCase.test_id == test_id).first()
            if not tc:
                return None
            for key, val in test_data.items():
                if hasattr(tc, key) and key not in ["id", "test_id"]:
                    setattr(tc, key, val)
            tc.version = (tc.version or 1) + 1
            session.commit()
            session.refresh(tc)
            self.log_audit("UPDATE_TEST", "TestCase", tc.test_id, f"Updated test case version {tc.version}", db=session)
            return tc
        finally:
            if self._db is None:
                session.close()

    def delete_test_case(self, test_id: str) -> bool:
        session = self._get_session()
        try:
            tc = session.query(TestCase).filter(TestCase.test_id == test_id).first()
            if not tc:
                return False
            session.query(Review).filter(Review.test_case_id == tc.id).delete()
            session.query(TestResult).filter(TestResult.test_case_id == tc.id).delete()
            session.query(Traceability).filter(
                (Traceability.target_id == tc.test_id) | (Traceability.source_id == tc.test_id)
            ).delete()
            session.delete(tc)
            session.commit()
            self.log_audit("DELETE_TEST", "TestCase", test_id, f"Deleted test case {test_id}", db=session)
            return True
        finally:
            if self._db is None:
                session.close()

    # --- Test Results ---
    def record_test_result(self, result_data: dict) -> TestResult:
        session = self._get_session()
        try:
            tr = TestResult(
                test_case_id=result_data["test_case_id"],
                request_sent_hex=result_data["request_sent_hex"],
                expected_response_hex=result_data["expected_response_hex"],
                actual_response_hex=result_data["actual_response_hex"],
                outcome=result_data["outcome"],
                diff_analysis=result_data.get("diff_analysis", ""),
                explanation=result_data.get("explanation", "Potential explanation based on simulated behavior."),
                execution_mode="SIMULATION MODE — NO REAL ECU CONNECTION"
            )
            session.add(tr)
            session.commit()
            session.refresh(tr)
            self.log_audit("EXECUTE_TEST", "TestResult", str(tr.id), f"Result: {tr.outcome}", db=session)
            return tr
        finally:
            if self._db is None:
                session.close()

    def get_test_results(self, limit: int = 100) -> List[TestResult]:
        session = self._get_session()
        try:
            return session.query(TestResult).order_by(desc(TestResult.execution_timestamp)).limit(limit).all()
        finally:
            if self._db is None:
                session.close()

    # --- Coverage ---
    def get_latest_coverage(self) -> Optional[Coverage]:
        session = self._get_session()
        try:
            return session.query(Coverage).order_by(desc(Coverage.timestamp)).first()
        finally:
            if self._db is None:
                session.close()

    def save_coverage(self, metrics: dict) -> Coverage:
        session = self._get_session()
        try:
            cov = Coverage(
                req_coverage=metrics.get("req_coverage", 0.0),
                service_coverage=metrics.get("service_coverage", 0.0),
                subfunction_coverage=metrics.get("subfunction_coverage", 0.0),
                positive_coverage=metrics.get("positive_coverage", 0.0),
                negative_coverage=metrics.get("negative_coverage", 0.0),
                session_coverage=metrics.get("session_coverage", 0.0),
                security_coverage=metrics.get("security_coverage", 0.0),
                boundary_coverage=metrics.get("boundary_coverage", 0.0),
                gaps_json=json.dumps(metrics.get("gaps", []))
            )
            session.add(cov)
            session.commit()
            session.refresh(cov)
            return cov
        finally:
            if self._db is None:
                session.close()

    # --- Traceability Links ---
    def get_traceability_links(self) -> List[Traceability]:
        session = self._get_session()
        try:
            return session.query(Traceability).all()
        finally:
            if self._db is None:
                session.close()

    def add_traceability_link(self, source_type: str, source_id: str, target_type: str, target_id: str, relation: str = "TRACEABLE_TO"):
        session = self._get_session()
        try:
            link = Traceability(
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                relation_type=relation
            )
            session.add(link)
            session.commit()
        finally:
            if self._db is None:
                session.close()

    # --- Change Events ---
    def get_change_events(self) -> List[ChangeEvent]:
        session = self._get_session()
        try:
            return session.query(ChangeEvent).order_by(desc(ChangeEvent.detected_at)).all()
        finally:
            if self._db is None:
                session.close()

    # --- Metrics Summary for Dashboard ---
    def get_dashboard_summary(self) -> Dict[str, Any]:
        session = self._get_session()
        try:
            doc_count = session.query(func.count(Document.id)).scalar() or 0
            service_count = session.query(func.count(Service.id)).scalar() or 0
            param_count = session.query(func.count(Parameter.id)).scalar() or 0
            req_count = session.query(func.count(Requirement.id)).scalar() or 0
            test_count = session.query(func.count(TestCase.id)).scalar() or 0
            approved_tests = session.query(func.count(TestCase.id)).filter(TestCase.review_status == "APPROVED").scalar() or 0
            pending_tests = session.query(func.count(TestCase.id)).filter(TestCase.review_status == "PENDING_REVIEW").scalar() or 0
            rejected_tests = session.query(func.count(TestCase.id)).filter(TestCase.review_status == "REJECTED").scalar() or 0

            latest_cov = self.get_latest_coverage()
            results = session.query(TestResult).all()
            pass_count = sum(1 for r in results if r.outcome == "PASS")
            fail_count = sum(1 for r in results if r.outcome == "FAIL")

            return {
                "documents_indexed": doc_count,
                "uds_services": service_count,
                "parameters_count": param_count,
                "requirements_count": req_count,
                "total_tests": test_count,
                "approved_tests": approved_tests,
                "pending_tests": pending_tests,
                "rejected_tests": rejected_tests,
                "passed_tests": pass_count,
                "failed_tests": fail_count,
                "coverage": {
                    "req_coverage": latest_cov.req_coverage if latest_cov else 0.0,
                    "service_coverage": latest_cov.service_coverage if latest_cov else 0.0,
                    "subfunction_coverage": latest_cov.subfunction_coverage if latest_cov else 0.0,
                    "positive_coverage": latest_cov.positive_coverage if latest_cov else 0.0,
                    "negative_coverage": latest_cov.negative_coverage if latest_cov else 0.0,
                    "session_coverage": latest_cov.session_coverage if latest_cov else 0.0,
                    "security_coverage": latest_cov.security_coverage if latest_cov else 0.0,
                    "boundary_coverage": latest_cov.boundary_coverage if latest_cov else 0.0,
                },
                "safety_banner": settings.SAFETY_BANNER,
                "simulation_mode": settings.SIMULATION_MODE
            }
        finally:
            if self._db is None:
                session.close()
