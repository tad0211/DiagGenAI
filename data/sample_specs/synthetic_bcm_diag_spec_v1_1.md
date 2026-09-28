# SYNTHETIC DEMONSTRATION DATA — NOT AN OEM SPECIFICATION
# Body Control Module (BCM) Diagnostic Specification
# Version: 1.1.0
# Date: 2026-03-20
# Classification: Synthetic Academic Demo - Simulation Only

## Section 1: Overview and Scope
This document specifies the synthetic diagnostic implementation for the demonstration Body Control Module (BCM-Demo-ECU) Release 1.1.
NOTICE: This is synthetic demonstration data created exclusively for academic prototyping of the DiagGenAI assistant. Do NOT transmit any messages in this document to a real vehicle or physical electronic control unit.

## Section 2: Supported Diagnostic Sessions (Service 0x10)
Service 0x10 DiagnosticSessionControl is supported with the following subfunctions:
- Subfunction 0x01: DefaultSession. Available in all sessions. Positive response: 0x50 0x01 0x00 0x32 0x01 0xF4.
- Subfunction 0x02: ProgrammingSession. Precondition: Vehicle speed = 0 km/h, Security access level 1 unlocked. Positive response: 0x50 0x02 0x00 0x32 0x01 0xF4.
- Subfunction 0x03: ExtendedDiagnosticSession. Precondition: DefaultSession active. Positive response: 0x50 0x03 0x00 0x32 0x01 0xF4.
- Subfunction 0x04: SafetySystemDiagnosticSession (ADDED IN V1.1). Precondition: Extended session + Security Level 2. Positive response: 0x50 0x04 0x00 0x32 0x01 0xF4.

## Section 3: ECU Reset (Service 0x11)
Service 0x11 ECUReset:
- Subfunction 0x01: HardReset. Allowed in DefaultSession and ExtendedDiagnosticSession. Positive response: 0x51 0x01.
[REMOVED IN V1.1: Subfunction 0x03 SoftReset has been deprecated and removed. Requesting 0x03 will now yield NRC 0x12 SubFunctionNotSupported].

## Section 4: Read Data By Identifier (Service 0x22)
Service 0x22 ReadDataByIdentifier allows reading the following synthetic Data Identifiers:
- DID 0xF190 (VIN): 17 bytes ASCII.
- DID 0x0100 (Simulated Engine Speed): 2 bytes UINT16 (0 to 16000).
- DID 0x0200 (Simulated Vehicle Speed): 2 bytes UINT16 (0 to 25000).
- DID 0x0300 (Simulated Battery Voltage): 2 bytes UINT16 (8000 to 18000).
- DID 0x0400 (Simulated Odometer Reading - ADDED IN V1.1): Length: 4 bytes UINT32, resolution 0.1 km/bit. Range: 0 to 9999999 (0x00000000 to 0x0098967F). Precondition: DefaultSession, ExtendedDiagnosticSession. Expected Positive Response: 0x62 0x04 0x00 0x00 0x01 0x86 0xA0 (100,000.0 km).

## Section 5: Security Access (Service 0x27)
Service 0x27 SecurityAccess:
- Subfunction 0x01 (RequestSeed - Level 1): Returns 4 bytes seed.
- Subfunction 0x02 (SendKey - Level 1): Key algorithm updated in V1.1: Seed XOR 0x33CC33CC (CHANGED ALGORITHM).
- Subfunction 0x03 (RequestSeed - Level 2 - ADDED IN V1.1): Request seed for Safety system security. Precondition: ExtendedDiagnosticSession. Positive response: 0x67 0x03 [4 bytes Seed].
- Subfunction 0x04 (SendKey - Level 2 - ADDED IN V1.1): Key = Seed XOR 0x77DD77DD.

## Section 6: Write Data By Identifier (Service 0x2E)
Service 0x2E WriteDataByIdentifier:
- DID 0x0105 (Variant Coding): MODIFIED IN V1.1: Length expanded from 4 bytes to 5 bytes.
  Byte 1: Region (0x01..0x04)
  Byte 2: Lighting (0x00..0x02)
  Byte 3: TrailerMode (0x00..0x01)
  Byte 4: TelematicsFlag (0x00=Off, 0x01=On - NEW PARAMETER)
  Byte 5: Checksum
  Preconditions: ExtendedDiagnosticSession AND Security Access Level 1 Unlocked.
  Expected Positive Response: 0x6E 0x01 0x05.

## Section 7: Routine Control (Service 0x31)
Service 0x31 RoutineControl:
- Routine ID 0x0201 (SelfTestRoutine):
  - Subfunction 0x01 (StartRoutine): Preconditions CHANGED IN V1.1: Now REQUIRES Security Access Level 1 Unlocked in addition to ExtendedDiagnosticSession. (If called when locked, returns NRC 0x33 SecurityAccessDenied).
  - Subfunction 0x03 (RequestRoutineResults): Expected Positive Response: 0x71 0x03 0x02 0x01 0x00 0x00.
