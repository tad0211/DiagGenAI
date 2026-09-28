# SYNTHETIC DEMONSTRATION DATA — NOT AN OEM SPECIFICATION
# Body Control Module (BCM) Diagnostic Specification
# Version: 1.0.0
# Date: 2026-01-15
# Classification: Synthetic Academic Demo - Simulation Only

## Section 1: Overview and Scope
This document specifies the synthetic diagnostic implementation for the demonstration Body Control Module (BCM-Demo-ECU).
NOTICE: This is synthetic demonstration data created exclusively for academic prototyping of the DiagGenAI assistant. Do NOT transmit any messages in this document to a real vehicle or physical electronic control unit.

## Section 2: Supported Diagnostic Sessions (Service 0x10)
Service 0x10 DiagnosticSessionControl is supported with the following subfunctions:
- Subfunction 0x01: DefaultSession (Standard operating session). No security prerequisite. Available in all sessions. Positive response: 0x50 0x01 0x00 0x32 0x01 0xF4 (P2=50ms, P2*=5000ms).
- Subfunction 0x02: ProgrammingSession. Precondition: Vehicle speed = 0 km/h, Security access level 1 unlocked. Positive response: 0x50 0x02 0x00 0x32 0x01 0xF4.
- Subfunction 0x03: ExtendedDiagnosticSession. Precondition: DefaultSession active. No security prerequisite. Positive response: 0x50 0x03 0x00 0x32 0x01 0xF4.

NRC Handling for 0x10:
- NRC 0x12 (SubFunctionNotSupported): Sent if subfunction is not 0x01, 0x02, or 0x03.
- NRC 0x13 (IncorrectMessageLengthOrInvalidFormat): Sent if request payload length is not exactly 2 bytes (SID + Subfunction).
- NRC 0x22 (ConditionsNotCorrect): Sent if transition to ProgrammingSession is requested while vehicle speed > 0.

## Section 3: ECU Reset (Service 0x11)
Service 0x11 ECUReset supports the following subfunctions:
- Subfunction 0x01: HardReset. Allowed in DefaultSession and ExtendedDiagnosticSession. Positive response: 0x51 0x01.
- Subfunction 0x03: SoftReset. Allowed in DefaultSession and ExtendedDiagnosticSession. Positive response: 0x51 0x03.

NRC Handling for 0x11:
- NRC 0x12 (SubFunctionNotSupported): Sent if subfunction is not 0x01 or 0x03.
- NRC 0x13 (IncorrectMessageLengthOrInvalidFormat): Sent if request payload length != 2 bytes.

## Section 4: Read Data By Identifier (Service 0x22)
Service 0x22 ReadDataByIdentifier allows reading the following synthetic Data Identifiers (DIDs):
- DID 0xF190 (VIN - Vehicle Identification Number): Length: 17 bytes (ASCII). Allowed in: DefaultSession, ExtendedDiagnosticSession. Security: None. Expected Positive Response: 0x62 0xF1 0x90 [17 bytes ASCII "DEMOVIN1234567890"].
- DID 0x0100 (Simulated Engine Speed): Length: 2 bytes (UINT16, resolution 0.25 RPM/bit). Range: 0 to 16000 (0x0000 to 0x3E80). Allowed in: DefaultSession, ExtendedDiagnosticSession. Security: None. Expected Positive Response: 0x62 0x01 0x00 0x0F 0xA0 (4000 RPM demo).
- DID 0x0200 (Simulated Vehicle Speed): Length: 2 bytes (UINT16, resolution 0.01 km/h/bit). Range: 0 to 25000 (0x0000 to 0x61A8). Allowed in: DefaultSession, ExtendedDiagnosticSession. Security: None. Expected Positive Response: 0x62 0x02 0x00 0x00 0x00 (0 km/h).
- DID 0x0300 (Simulated Battery Voltage): Length: 2 bytes (UINT16, resolution 0.001 V/bit). Range: 8000 to 18000 (0x1F40 to 0x4650, representing 8.000V - 18.000V). Allowed in: DefaultSession, ExtendedDiagnosticSession. Security: None. Expected Positive Response: 0x62 0x03 0x00 0x30 0xD4 (12.500 V).

NRC Handling for 0x22:
- NRC 0x13 (IncorrectMessageLengthOrInvalidFormat): Sent if request length is less than 3 bytes or not a multiple of 2 after SID.
- NRC 0x31 (RequestOutOfRange): Sent if DID requested is not supported by the ECU.

## Section 5: Security Access (Service 0x27)
Service 0x27 SecurityAccess manages unlock access for diagnostic routines and parameter writing:
- Subfunction 0x01 (RequestSeed - Level 1): Request seed for diagnostic engineer security level. Precondition: ExtendedDiagnosticSession. Positive response: 0x67 0x01 [4 bytes Seed: 0x3A 0x7B 0x1C 0x9F]. If already unlocked, returns seed with all zeros: 0x67 0x01 0x00 0x00 0x00 0x00.
- Subfunction 0x02 (SendKey - Level 1): Send computed key for Level 1. Payload: 4 bytes key. Key algorithm for demo: Seed XOR 0x55AA55AA. Positive response: 0x67 0x02.

NRC Handling for 0x27:
- NRC 0x12 (SubFunctionNotSupported): Sent if subfunction is not 0x01 or 0x02.
- NRC 0x13 (IncorrectMessageLengthOrInvalidFormat): Sent if length is incorrect (e.g. 0x02 SendKey without 4 key bytes).
- NRC 0x24 (RequestSequenceError): Sent if 0x02 SendKey is sent before 0x01 RequestSeed.
- NRC 0x35 (InvalidKey): Sent if key verification fails.
- NRC 0x36 (ExceedNumberOfAttempts): Sent after 3 consecutive invalid keys. Lock delay: 10 seconds.
- NRC 0x7E (SubFunctionNotSupportedInActiveSession): Sent if 0x27 is called in DefaultSession.

## Section 6: Write Data By Identifier (Service 0x2E)
Service 0x2E WriteDataByIdentifier allows writing configuration parameters:
- DID 0x0105 (Variant Coding): Length: 4 bytes. Preconditions: ExtendedDiagnosticSession active AND Security Access Level 1 Unlocked. Parameter range: Byte 1 (Region: 0x01=NA, 0x02=EU, 0x03=ASIA), Byte 2 (Lighting: 0x00=Halogen, 0x01=LED), Byte 3 (TrailerMode: 0x00=Disabled, 0x01=Enabled), Byte 4 (Checksum). Expected Positive Response: 0x6E 0x01 0x05.

NRC Handling for 0x2E:
- NRC 0x13 (IncorrectMessageLengthOrInvalidFormat): Sent if payload length != 7 bytes (SID + 2 bytes DID + 4 bytes Data).
- NRC 0x31 (RequestOutOfRange): Sent if DID is unsupported or data parameters exceed defined ranges.
- NRC 0x33 (SecurityAccessDenied): Sent if Security Access Level 1 is locked.
- NRC 0x7F (ServiceNotSupportedInActiveSession): Sent if called in DefaultSession.

## Section 7: Routine Control (Service 0x31)
Service 0x31 RoutineControl allows starting, stopping, and requesting results of diagnostic routines:
- Routine ID 0x0201 (SelfTestRoutine):
  - Subfunction 0x01 (StartRoutine): Preconditions: ExtendedDiagnosticSession AND Vehicle Speed = 0 km/h. Expected Positive Response: 0x71 0x01 0x02 0x01 0x00 (Routine started, status running).
  - Subfunction 0x03 (RequestRoutineResults): Expected Positive Response: 0x71 0x03 0x02 0x01 0x00 0x00 (Routine completed, result OK).

NRC Handling for 0x31:
- NRC 0x12 (SubFunctionNotSupported): If subfunction != 0x01 or 0x03.
- NRC 0x22 (ConditionsNotCorrect): If vehicle speed > 0 when starting routine.
- NRC 0x31 (RequestOutOfRange): If Routine ID != 0x0201.
- NRC 0x7E (SubFunctionNotSupportedInActiveSession): If called in DefaultSession.
