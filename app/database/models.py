import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0")
    # STANDARD, OEM, ECU, PROJECT
    doc_type = Column(String(50), nullable=False, default="ECU")
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="INDEXED")
    file_path = Column(String(512), nullable=True)
    source_page = Column(Integer, default=1)
    section = Column(String(255), default="General")
    metadata_json = Column(Text, default="{}")

    requirements = relationship("Requirement", back_populates="document", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    service_id_hex = Column(String(10), unique=True, nullable=False, index=True) # e.g. "0x22"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    standard_ref = Column(String(100), default="ISO 14229-1")
    session_prereq = Column(String(100), default="DefaultSession")
    security_prereq = Column(String(100), default="None")
    positive_response_sid_hex = Column(String(10), nullable=True) # e.g. "0x62"

    subfunctions = relationship("Subfunction", back_populates="service", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="service", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="service", cascade="all, delete-orphan")


class Subfunction(Base):
    __tablename__ = "subfunctions"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    subfunction_hex = Column(String(10), nullable=False) # e.g. "0x01"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    session_prereq = Column(String(100), default="DefaultSession")
    security_prereq = Column(String(100), default="None")
    suppress_pos_rsp_supported = Column(Boolean, default=True)

    service = relationship("Service", back_populates="subfunctions")
    __table_args__ = (UniqueConstraint("service_id", "subfunction_hex", name="uq_service_subfunction"),)


class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    param_name = Column(String(255), nullable=False)
    byte_position = Column(Integer, default=1)
    length_bytes = Column(Integer, default=1)
    data_type = Column(String(50), default="HEX") # HEX, ASCII, INT, UINT16, etc.
    min_value = Column(String(100), nullable=True)
    max_value = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True)
    did_hex = Column(String(10), nullable=True) # If parameter is DID e.g. "0xF190"

    service = relationship("Service", back_populates="parameters")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    req_id = Column(String(100), unique=True, nullable=False, index=True) # e.g. "REQ-UDS-001"
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="Functional") # Functional, Security, Timing, Session
    verification_method = Column(String(100), default="Test")
    source_doc = Column(String(255), default="Synthetic ECU Spec")
    source_section = Column(String(100), default="Section 1.0")

    document = relationship("Document", back_populates="requirements")
    service = relationship("Service", back_populates="requirements")
    test_cases = relationship("TestCase", back_populates="requirement")


class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(100), unique=True, nullable=False, index=True) # e.g. "TC-UDS-001"
    objective = Column(Text, nullable=False)
    requirement_id = Column(String(100), ForeignKey("requirements.req_id", ondelete="SET NULL"), nullable=True)
    service_id_hex = Column(String(10), nullable=False) # "0x22"
    subfunction_hex = Column(String(10), nullable=True)  # "0x01" or None
    preconditions = Column(Text, default="ECU powered, Default Session")
    session = Column(String(100), default="DefaultSession") # DefaultSession, ExtendedDiagnosticSession, ProgrammingSession
    security_state = Column(String(100), default="Locked") # Locked, Level1Unlocked
    request_hex = Column(String(255), nullable=False) # e.g. "22 F1 90"
    expected_response_hex = Column(String(255), nullable=False) # e.g. "62 F1 90 ..." or "7F 22 31"
    pass_criteria = Column(Text, default="ECU responds with positive response matching expected data pattern")
    fail_criteria = Column(Text, default="NRC received or timeout")
    # POSITIVE, NEGATIVE, BOUNDARY, SESSION, SECURITY, INVALID_PARAM
    test_type = Column(String(50), default="POSITIVE")
    source_evidence = Column(Text, default="Synthetic Spec v1.0 Section 3.2")
    generation_rationale = Column(Text, nullable=True)
    confidence = Column(Float, default=0.95)
    # PENDING_REVIEW, APPROVED, REJECTED, EDITED
    review_status = Column(String(50), default="PENDING_REVIEW")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    requirement = relationship("Requirement", back_populates="test_cases")
    results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="test_case", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    execution_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    request_sent_hex = Column(String(255), nullable=False)
    expected_response_hex = Column(String(255), nullable=False)
    actual_response_hex = Column(String(255), nullable=False)
    # PASS, FAIL, ERROR
    outcome = Column(String(20), nullable=False)
    diff_analysis = Column(Text, nullable=True)
    explanation = Column(Text, default="Potential explanation based on simulated behavior.")
    execution_mode = Column(String(50), default="SIMULATION MODE — NO REAL ECU CONNECTION")

    test_case = relationship("TestCase", back_populates="results")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    reviewer = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    decision = Column(String(50), nullable=False) # APPROVED, REJECTED, EDITED
    comment = Column(Text, nullable=True)
    test_version = Column(Integer, default=1)

    test_case = relationship("TestCase", back_populates="reviews")


class Coverage(Base):
    __tablename__ = "coverage"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    req_coverage = Column(Float, default=0.0)
    service_coverage = Column(Float, default=0.0)
    subfunction_coverage = Column(Float, default=0.0)
    positive_coverage = Column(Float, default=0.0)
    negative_coverage = Column(Float, default=0.0)
    session_coverage = Column(Float, default=0.0)
    security_coverage = Column(Float, default=0.0)
    boundary_coverage = Column(Float, default=0.0)
    gaps_json = Column(Text, default="[]")


class Traceability(Base):
    __tablename__ = "traceability"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False) # Requirement, Service, TestScenario, TestCase, AutomationTemplate
    source_id = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=False)
    relation_type = Column(String(50), default="VERIFIED_BY")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class SpecificationVersion(Base):
    __tablename__ = "specification_versions"

    id = Column(Integer, primary_key=True, index=True)
    spec_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    file_path = Column(String(512), nullable=True)
    active = Column(Boolean, default=True)


class ChangeEvent(Base):
    __tablename__ = "change_events"

    id = Column(Integer, primary_key=True, index=True)
    spec_v1 = Column(String(50), nullable=False)
    spec_v2 = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False) # ADDED_SERVICE, REMOVED_SERVICE, MODIFIED_PARAM, CHANGED_PREREQ
    target_entity = Column(String(100), nullable=False)
    change_description = Column(Text, nullable=False)
    affected_tests_json = Column(Text, default="[]")
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = Column(String(100), default="automotive_engineer")
    action = Column(String(100), nullable=False) # e.g. "APPROVE_TEST", "VALIDATE_REQUEST", "SIMULATE_TEST"
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="Diagnostic_Engineer") # Diagnostic_Engineer, Reviewer, Admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
