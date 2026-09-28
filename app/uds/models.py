from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class DiagnosticSession(str, Enum):
    DEFAULT = "DefaultSession"
    PROGRAMMING = "ProgrammingSession"
    EXTENDED = "ExtendedDiagnosticSession"
    SAFETY = "SafetySystemDiagnosticSession"

class SecurityState(str, Enum):
    LOCKED = "Locked"
    LEVEL_1_UNLOCKED = "Level1Unlocked"
    LEVEL_2_UNLOCKED = "Level2Unlocked"

class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    REQUIRES_REVIEW = "REQUIRES REVIEW"

class ValidationIssue(BaseModel):
    rule: str
    reason: str
    suggested_correction: str
    source_evidence: str
    severity: str = "ERROR" # ERROR, WARNING, INFO

class ValidationResult(BaseModel):
    status: ValidationStatus
    request_hex: str
    service_id_hex: str
    subfunction_hex: Optional[str] = None
    issues: List[ValidationIssue] = []
    expected_response_hex: Optional[str] = None
    expected_nrc: Optional[str] = None
    source_evidence: str = "ISO 14229-1 / Synthetic Spec"

class UDSRequestBuildInput(BaseModel):
    service_id_hex: str = Field(..., description="e.g. 0x22 or 22")
    subfunction_hex: Optional[str] = Field(None, description="e.g. 0x01 or 01")
    did_hex: Optional[str] = Field(None, description="Data Identifier e.g. 0xF190")
    parameters_hex: Optional[str] = Field(None, description="Additional hex payload bytes")
    session: str = "DefaultSession"
    security_state: str = "Locked"

class UDSRequestBuildOutput(BaseModel):
    request_hex: str
    formatted_bytes: List[str]
    preconditions: str
    expected_response: str
    source_evidence: str
    explanation: str
