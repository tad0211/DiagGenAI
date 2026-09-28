"""
ISO 14229-1 UDS Protocol Rules, Parameter Definitions, and Configurable Rule Registry.
"""

from typing import Dict, Any, List

# Standard UDS Services
STANDARD_SERVICES = {
    0x10: {"name": "DiagnosticSessionControl", "has_subfunc": True, "min_len": 2, "max_len": 2},
    0x11: {"name": "ECUReset", "has_subfunc": True, "min_len": 2, "max_len": 2},
    0x14: {"name": "ClearDiagnosticInformation", "has_subfunc": False, "min_len": 4, "max_len": 4},
    0x19: {"name": "ReadDTCInformation", "has_subfunc": True, "min_len": 2, "max_len": 5},
    0x22: {"name": "ReadDataByIdentifier", "has_subfunc": False, "min_len": 3, "max_len": 65},
    0x23: {"name": "ReadMemoryByAddress", "has_subfunc": False, "min_len": 4, "max_len": 16},
    0x27: {"name": "SecurityAccess", "has_subfunc": True, "min_len": 2, "max_len": 66},
    0x28: {"name": "CommunicationControl", "has_subfunc": True, "min_len": 3, "max_len": 3},
    0x2E: {"name": "WriteDataByIdentifier", "has_subfunc": False, "min_len": 4, "max_len": 256},
    0x31: {"name": "RoutineControl", "has_subfunc": True, "min_len": 4, "max_len": 256},
    0x34: {"name": "RequestDownload", "has_subfunc": False, "min_len": 4, "max_len": 256},
    0x36: {"name": "TransferData", "has_subfunc": False, "min_len": 3, "max_len": 4096},
    0x37: {"name": "RequestTransferExit", "has_subfunc": False, "min_len": 1, "max_len": 256},
    0x3E: {"name": "TesterPresent", "has_subfunc": True, "min_len": 2, "max_len": 2},
    0x85: {"name": "ControlDTCSetting", "has_subfunc": True, "min_len": 2, "max_len": 2},
}

# Standard Negative Response Codes (NRC)
STANDARD_NRCS = {
    0x10: "GeneralReject",
    0x11: "ServiceNotSupported",
    0x12: "SubFunctionNotSupported",
    0x13: "IncorrectMessageLengthOrInvalidFormat",
    0x14: "ResponseTooLong",
    0x21: "BusyRepeatRequest",
    0x22: "ConditionsNotCorrect",
    0x24: "RequestSequenceError",
    0x25: "NoResponseFromSubnetComponent",
    0x26: "FailurePreventsExecutionOfRequestedAction",
    0x31: "RequestOutOfRange",
    0x33: "SecurityAccessDenied",
    0x35: "InvalidKey",
    0x36: "ExceedNumberOfAttempts",
    0x37: "RequiredTimeDelayNotExpired",
    0x70: "UploadDownloadNotAccepted",
    0x71: "TransferDataSuspended",
    0x72: "GeneralProgrammingFailure",
    0x73: "WrongBlockSequenceCounter",
    0x78: "RequestCorrectlyReceived-ResponsePending",
    0x7E: "SubFunctionNotSupportedInActiveSession",
    0x7F: "ServiceNotSupportedInActiveSession",
}

# Configurable Deterministic Validation Rules Registry
VALIDATION_RULES_REGISTRY = {
    "RULE_HEX_FORMAT": {
        "name": "Hexadecimal Syntax Validation",
        "description": "Validates that the frame string is composed of valid two-digit hexadecimal tokens.",
        "standard_ref": "ISO 14229-1 Frame Syntax",
        "default_severity": "ERROR"
    },
    "RULE_SID_ISO_SUPPORT": {
        "name": "Service Identifier Support",
        "description": "Verifies that the requested service byte exists in ISO 14229-1 and is configured on the target ECU.",
        "standard_ref": "ISO 14229-1 Table 1 (UDS Services)",
        "default_severity": "ERROR"
    },
    "RULE_SUBFUNC_REQUIRED": {
        "name": "Subfunction Parameter Presence",
        "description": "Ensures that services requiring a subfunction parameter supply at least 2 bytes in the payload.",
        "standard_ref": "ISO 14229-1 Section 7.3.2",
        "default_severity": "ERROR"
    },
    "RULE_SUBFUNC_SUPPORT": {
        "name": "Subfunction Value Validity",
        "description": "Checks that the requested subfunction (ignoring suppress bit 0x80) is supported by the target ECU.",
        "standard_ref": "ISO 14229-1 & ECU Diagnostic Spec",
        "default_severity": "ERROR"
    },
    "RULE_PAYLOAD_LENGTH": {
        "name": "Message Length Verification",
        "description": "Verifies that frame length conforms strictly to minimum and maximum payload byte constraints.",
        "standard_ref": "ISO 14229-1 Service Syntax",
        "default_severity": "ERROR"
    },
    "RULE_DID_SUPPORT": {
        "name": "Data Identifier (DID) Validity",
        "description": "Validates that 2-byte DIDs queried via 0x22 or written via 0x2E are defined in the specification.",
        "standard_ref": "ISO 14229-1 Section 11 & Spec",
        "default_severity": "ERROR"
    },
    "RULE_PARAM_RANGE": {
        "name": "Parameter Boundary & Value Range",
        "description": "Enforces valid engineering ranges for structured parameters and payload bytes.",
        "standard_ref": "Synthetic BCM Spec Section 6",
        "default_severity": "ERROR"
    },
    "RULE_SESSION_PREREQUISITE": {
        "name": "Diagnostic Session Prerequisite",
        "description": "Verifies that the target ECU session meets the prerequisite (Default vs Extended vs Programming).",
        "standard_ref": "ISO 14229-1 Section 9",
        "default_severity": "WARNING"
    },
    "RULE_SECURITY_PREREQUISITE": {
        "name": "Security Access Prerequisite",
        "description": "Verifies that the security access level (e.g. Level 1 Unlocked) is satisfied before protected execution.",
        "standard_ref": "ISO 14229-1 Section 10",
        "default_severity": "WARNING"
    }
}

# Known DID Specifications for BCM ECU
DID_REGISTRY = {
    "0XF190": {"name": "VIN (Vehicle Identification Number)", "length": 17, "type": "ASCII", "read_sessions": ["DefaultSession", "ExtendedDiagnosticSession"], "write_security": "Level1Unlocked"},
    "0X0100": {"name": "Simulated Engine Speed", "length": 2, "type": "UINT16", "scaling": "0.25 rpm/bit", "min": 0, "max": 16000, "unit": "RPM"},
    "0X0200": {"name": "Simulated Vehicle Speed", "length": 2, "type": "UINT16", "scaling": "0.01 km/h/bit", "min": 0, "max": 25000, "unit": "km/h"},
    "0X0300": {"name": "Simulated Battery Voltage", "length": 2, "type": "UINT16", "scaling": "0.001 V/bit", "min": 8000, "max": 18000, "unit": "mV"},
    "0X0105": {"name": "Variant Coding", "length": 4, "type": "HEX", "write_security": "Level1Unlocked", "write_session": "ExtendedDiagnosticSession"}
}

def clean_hex_string(hex_str: str) -> str:
    """Normalize hex string by removing 0x, spaces, commas, and converting to uppercase."""
    if not hex_str:
        return ""
    cleaned = hex_str.replace("0x", "").replace("0X", "").replace(" ", "").replace(",", "").replace(":", "")
    return cleaned.upper()

def hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes with error handling."""
    clean = clean_hex_string(hex_str)
    if len(clean) % 2 != 0:
        clean = "0" + clean
    return bytes.fromhex(clean)

def format_hex_bytes(b: bytes) -> str:
    """Format bytes as space-separated uppercase hex tokens (e.g. '22 F1 90')."""
    return " ".join(f"{x:02X}" for x in b)
