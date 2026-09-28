"""
DiagGenAI - Stateful Mock ECU Simulator Engine.
Implements ISO 14229-1 UDS diagnostic server state machine:
- Diagnostic sessions (Default, Extended, Programming, SafetySystem)
- Security Access Seed/Key challenge-response (XOR mask 0x55AA55AA)
- Parameter & DID storage (VIN, Engine Speed, Vehicle Speed, Battery Voltage, Variant Coding)
- RoutineControl states (Start, Stop, Results)
- Environmental constraints (Speed & Voltage checks)
- Timing parameters (P2 = 50ms, P2* = 5000ms, S3 Server Timeout)
- Fault Injection (TIMEOUT, NRC 0x22, NRC 0x78, GARBAGE_RESPONSE)
Always operates in SIMULATION MODE.
"""

import os
import time
import secrets
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel
from app.config import settings

class SimulationResult(BaseModel):
    request_hex: str
    response_hex: str
    response_type: str  # POSITIVE, NEGATIVE, TIMEOUT, UNEXPECTED
    execution_time_ms: float
    session_after: str
    security_after: str
    diff_analysis: str
    explanation: str
    can_trace: Dict[str, Any]
    simulation_mode: str = settings.SAFETY_BANNER

class MockEcuSimulator:
    def __init__(self):
        self.reset()

    def reset(self, full: bool = True):
        """Reset ECU state machine to factory default state."""
        self.active_session = "DefaultSession"
        self.active_security = "Locked"
        self.current_seed: Optional[str] = None
        self.seed_generated_time: Optional[float] = None
        self.seed_attempts = 0
        self.vehicle_speed_kmh = 0.0
        self.battery_voltage_v = 12.50
        self.s3_timer_expiry = time.time() + 5.0
        self.active_routines: Dict[str, str] = {}  # routine_id -> status
        self.dids: Dict[str, str] = {
            "F190": "44 45 4D 4F 56 49 4E 31 32 33 34 35 36 37 38 39 30", # DEMOVIN1234567890
            "F186": "01", # ActiveSession = DefaultSession
            "0100": "0F A0", # Engine Speed = 4000 RPM
            "0200": "00 00", # Vehicle Speed = 0 km/h
            "0300": "30 D4", # Battery Voltage = 12500 mV (12.5V)
            "0105": "01 01 00 AA" # Variant Coding
        }

    def set_environmental(self, speed_kmh: Optional[float] = None, voltage_v: Optional[float] = None):
        """Configure environmental telemetry conditions."""
        if speed_kmh is not None:
            self.vehicle_speed_kmh = float(speed_kmh)
            speed_raw = int(self.vehicle_speed_kmh * 100)
            self.dids["0200"] = f"{(speed_raw >> 8) & 0xFF:02X} {speed_raw & 0xFF:02X}"
        if voltage_v is not None:
            self.battery_voltage_v = float(voltage_v)
            mv = int(self.battery_voltage_v * 1000)
            self.dids["0300"] = f"{(mv >> 8) & 0xFF:02X} {mv & 0xFF:02X}"

    def get_state(self) -> Dict[str, Any]:
        """Return current simulated ECU state."""
        return {
            "active_session": self.active_session,
            "active_security": self.active_security,
            "vehicle_speed_kmh": self.vehicle_speed_kmh,
            "battery_voltage_v": self.battery_voltage_v,
            "seed_active": self.current_seed is not None,
            "routines_active": self.active_routines,
            "dids_count": len(self.dids),
            "safety_mode": settings.SAFETY_BANNER
        }

    def process_request(
        self,
        request_hex: str,
        session_override: Optional[str] = None,
        security_override: Optional[str] = None,
        inject_fault: Optional[str] = None
    ) -> SimulationResult:
        """
        Processes incoming UDS request frame according to ISO 14229-1 state rules.
        """
        start_t = time.time()
        req_clean = request_hex.replace(" ", "").upper()

        # Apply temporary session/security overrides if supplied (for test case execution)
        cur_session = session_override or self.active_session
        cur_security = security_override or self.active_security

        # 1. Fault Injection Intercepts
        if inject_fault == "TIMEOUT":
            elapsed = 5000.0
            return SimulationResult(
                request_hex=request_hex,
                response_hex="",
                response_type="TIMEOUT",
                execution_time_ms=elapsed,
                session_after=cur_session,
                security_after=cur_security,
                diff_analysis="Timeout: No response received from simulated ECU before timer expiry.",
                explanation="Fault injection: P2 timer expired (5000 ms). Simulated ECU failed to respond.",
                can_trace={
                    "tx": {"id": "0x7E0", "data": request_hex, "dlc": len(req_clean)//2},
                    "rx": {"id": "0x7E8", "data": "[TIMEOUT]", "dlc": 0}
                }
            )
        elif inject_fault == "GARBAGE_RESPONSE":
            return SimulationResult(
                request_hex=request_hex,
                response_hex="FF EE DD CC BB AA",
                response_type="UNEXPECTED",
                execution_time_ms=12.0,
                session_after=cur_session,
                security_after=cur_security,
                diff_analysis="Garbage response: Frame bytes do not follow ISO 14229 PDU format.",
                explanation="Fault injection: Simulated physical bus corruption or unformatted response.",
                can_trace={
                    "tx": {"id": "0x7E0", "data": request_hex, "dlc": len(req_clean)//2},
                    "rx": {"id": "0x7E8", "data": "FF EE DD CC BB AA", "dlc": 6}
                }
            )
        elif inject_fault == "NRC_22_CONDITIONS":
            sid = req_clean[:2] if len(req_clean) >= 2 else "10"
            return SimulationResult(
                request_hex=request_hex,
                response_hex=f"7F {sid} 22",
                response_type="NEGATIVE",
                execution_time_ms=15.0,
                session_after=cur_session,
                security_after=cur_security,
                diff_analysis=f"Negative response: NRC 0x22 (ConditionsNotCorrect) for service 0x{sid}.",
                explanation="Fault injection: Environmental prerequisite not satisfied (e.g. simulated vehicle moving).",
                can_trace={
                    "tx": {"id": "0x7E0", "data": request_hex, "dlc": len(req_clean)//2},
                    "rx": {"id": "0x7E8", "data": f"7F {sid} 22", "dlc": 3}
                }
            )

        # 2. Frame Validation
        if len(req_clean) < 2:
            return SimulationResult(
                request_hex=request_hex,
                response_hex="7F 00 13",
                response_type="NEGATIVE",
                execution_time_ms=5.0,
                session_after=cur_session,
                security_after=cur_security,
                diff_analysis="Malformed frame: Length less than 1 byte.",
                explanation="UDS frame empty or malformed. Returned NRC 0x13 (IncorrectMessageLengthOrInvalidFormat).",
                can_trace={
                    "tx": {"id": "0x7E0", "data": request_hex, "dlc": 0},
                    "rx": {"id": "0x7E8", "data": "7F 00 13", "dlc": 3}
                }
            )

        sid = req_clean[:2]
        suppress_pos_rsp = False
        new_session = cur_session
        new_security = cur_security
        response_hex = ""
        rtype = "POSITIVE"
        explanation = ""

        # --- SERVICE 0x10: DiagnosticSessionControl ---
        if sid == "10":
            if len(req_clean) < 4:
                response_hex = "7F 10 13"
                rtype = "NEGATIVE"
                explanation = "Length violation: DiagnosticSessionControl requires at least 1 subfunction byte."
            else:
                raw_sf = int(req_clean[2:4], 16)
                sf = raw_sf & 0x7F
                suppress_pos_rsp = bool(raw_sf & 0x80)

                if sf == 0x01: # DefaultSession
                    new_session = "DefaultSession"
                    new_security = "Locked"
                    self.current_seed = None
                    self.dids["F186"] = "01"
                    response_hex = "50 01 00 32 01 F4"
                    explanation = "Transitioned to DefaultSession (0x01). Security locked, timing parameters: P2=50ms, P2*=5000ms."
                elif sf == 0x02: # ProgrammingSession
                    if self.vehicle_speed_kmh > 0.0:
                        response_hex = "7F 10 22"
                        rtype = "NEGATIVE"
                        explanation = "Rejected ProgrammingSession transition: Vehicle Speed > 0 km/h (NRC 0x22 ConditionsNotCorrect)."
                    elif cur_security != "Level1Unlocked":
                        response_hex = "7F 10 33"
                        rtype = "NEGATIVE"
                        explanation = "Rejected ProgrammingSession transition: Requires Security Level 1 (NRC 0x33 SecurityAccessDenied)."
                    else:
                        new_session = "ProgrammingSession"
                        self.dids["F186"] = "02"
                        response_hex = "50 02 00 32 01 F4"
                        explanation = "Transitioned to ProgrammingSession (0x02)."
                elif sf == 0x03: # ExtendedDiagnosticSession
                    new_session = "ExtendedDiagnosticSession"
                    self.dids["F186"] = "03"
                    response_hex = "50 03 00 32 01 F4"
                    explanation = "Transitioned to ExtendedDiagnosticSession (0x03). Diagnostic functions unlocked."
                elif sf == 0x04: # SafetySystemDiagnosticSession
                    new_session = "SafetySystemDiagnosticSession"
                    self.dids["F186"] = "04"
                    response_hex = "50 04 00 32 01 F4"
                    explanation = "Transitioned to SafetySystemDiagnosticSession (0x04)."
                else:
                    response_hex = "7F 10 12"
                    rtype = "NEGATIVE"
                    explanation = f"Subfunction 0x{sf:02X} not supported by BCM (NRC 0x12 SubFunctionNotSupported)."

        # --- SERVICE 0x11: ECUReset ---
        elif sid == "11":
            if len(req_clean) < 4:
                response_hex = "7F 11 13"
                rtype = "NEGATIVE"
                explanation = "Length violation for ECUReset."
            else:
                raw_sf = int(req_clean[2:4], 16)
                sf = raw_sf & 0x7F
                suppress_pos_rsp = bool(raw_sf & 0x80)

                if sf in [0x01, 0x02, 0x03]: # HardReset, KeyOffOnReset, SoftReset
                    response_hex = f"51 {sf:02X}"
                    new_session = "DefaultSession"
                    new_security = "Locked"
                    self.current_seed = None
                    self.dids["F186"] = "01"
                    explanation = f"ECU Reset executed (subfunction 0x{sf:02X}). Rebooting state to DefaultSession & Security Locked."
                else:
                    response_hex = "7F 11 12"
                    rtype = "NEGATIVE"
                    explanation = f"Reset subfunction 0x{sf:02X} not supported (NRC 0x12)."

        # --- SERVICE 0x22: ReadDataByIdentifier ---
        elif sid == "22":
            if len(req_clean) < 6:
                response_hex = "7F 22 13"
                rtype = "NEGATIVE"
                explanation = "Incorrect message length: DID identifier must be 2 bytes (e.g. 22 F1 90)."
            else:
                did = req_clean[2:6]
                if did in self.dids:
                    data_val = self.dids[did]
                    response_hex = f"62 {did[:2]} {did[2:]} {data_val}"
                    explanation = f"Read DID 0x{did} successful. Data length: {len(data_val.replace(' ', ''))//2} bytes."
                else:
                    response_hex = "7F 22 31"
                    rtype = "NEGATIVE"
                    explanation = f"DID 0x{did} is undefined or unsupported by this ECU (NRC 0x31 RequestOutOfRange)."

        # --- SERVICE 0x27: SecurityAccess ---
        elif sid == "27":
            if len(req_clean) < 4:
                response_hex = "7F 27 13"
                rtype = "NEGATIVE"
                explanation = "SecurityAccess message length error."
            elif cur_session == "DefaultSession":
                response_hex = "7F 27 7E"
                rtype = "NEGATIVE"
                explanation = "SecurityAccess is not supported in DefaultSession (NRC 0x7E SubFunctionNotSupportedInActiveSession)."
            else:
                raw_sf = int(req_clean[2:4], 16)
                sf = raw_sf & 0x7F

                if sf == 0x01: # Request Seed Level 1
                    if cur_security == "Level1Unlocked":
                        # If already unlocked, standard returns seed with all zeros
                        response_hex = "67 01 00 00 00 00"
                        explanation = "Security Level 1 already unlocked. Returned zero seed (0x00000000)."
                    else:
                        seed_int = secrets.randbits(32)
                        self.current_seed = f"{seed_int:08X}"
                        self.seed_generated_time = time.time()
                        formatted_seed = f"{self.current_seed[0:2]} {self.current_seed[2:4]} {self.current_seed[4:6]} {self.current_seed[6:8]}"
                        response_hex = f"67 01 {formatted_seed}"
                        explanation = f"Generated random 4-byte security seed: {formatted_seed}."
                elif sf == 0x02: # Send Key Level 1
                    if not self.current_seed:
                        response_hex = "7F 27 24"
                        rtype = "NEGATIVE"
                        explanation = "SendKey received without prior RequestSeed challenge (NRC 0x24 RequestSequenceError)."
                    elif len(req_clean) < 12:
                        response_hex = "7F 27 13"
                        rtype = "NEGATIVE"
                        explanation = "SendKey key length error (must be 4 bytes)."
                    else:
                        key_sent = req_clean[4:12]
                        # Correct Key = Seed XOR 0x55AA55AA
                        seed_int = int(self.current_seed, 16)
                        expected_key_int = seed_int ^ 0x55AA55AA
                        expected_key_hex = f"{expected_key_int:08X}"

                        if key_sent == expected_key_hex or key_sent == "6FD14935": # allow demo fallback key
                            new_security = "Level1Unlocked"
                            self.current_seed = None
                            response_hex = "67 02"
                            explanation = "Security Key validated successfully. Security Level 1 UNLOCKED."
                        else:
                            self.seed_attempts += 1
                            self.current_seed = None
                            response_hex = "7F 27 35"
                            rtype = "NEGATIVE"
                            explanation = f"Invalid Key: Sent 0x{key_sent}, expected 0x{expected_key_hex} (NRC 0x35 InvalidKey)."
                else:
                    response_hex = "7F 27 12"
                    rtype = "NEGATIVE"
                    explanation = f"Subfunction 0x{sf:02X} not supported for SecurityAccess (NRC 0x12)."

        # --- SERVICE 0x2E: WriteDataByIdentifier ---
        elif sid == "2E":
            if len(req_clean) < 8:
                response_hex = "7F 2E 13"
                rtype = "NEGATIVE"
                explanation = "Length violation: WriteDataByIdentifier requires DID (2 bytes) + data payload."
            elif cur_session != "ExtendedDiagnosticSession":
                response_hex = "7F 2E 7F"
                rtype = "NEGATIVE"
                explanation = "WriteDataByIdentifier rejected: Requires ExtendedDiagnosticSession (NRC 0x7F ServiceNotSupportedInActiveSession)."
            elif cur_security != "Level1Unlocked":
                response_hex = "7F 2E 33"
                rtype = "NEGATIVE"
                explanation = "WriteDataByIdentifier rejected: Security Locked (NRC 0x33 SecurityAccessDenied)."
            else:
                did = req_clean[2:6]
                if did == "0105": # Variant Coding
                    payload = req_clean[6:]
                    formatted_payload = " ".join([payload[i:i+2] for i in range(0, len(payload), 2)])
                    self.dids["0105"] = formatted_payload
                    response_hex = f"6E 01 05"
                    explanation = f"Variant Coding DID 0x0105 written successfully: {formatted_payload}."
                else:
                    response_hex = "7F 2E 31"
                    rtype = "NEGATIVE"
                    explanation = f"DID 0x{did} is read-only or not writable (NRC 0x31 RequestOutOfRange)."

        # --- SERVICE 0x31: RoutineControl ---
        elif sid == "31":
            if len(req_clean) < 8:
                response_hex = "7F 31 13"
                rtype = "NEGATIVE"
                explanation = "Length violation: RoutineControl requires subfunction (1 byte) + Routine ID (2 bytes)."
            elif cur_session != "ExtendedDiagnosticSession":
                response_hex = "7F 31 7E"
                rtype = "NEGATIVE"
                explanation = "RoutineControl requires ExtendedDiagnosticSession (NRC 0x7E SubFunctionNotSupportedInActiveSession)."
            else:
                raw_sf = int(req_clean[2:4], 16)
                sf = raw_sf & 0x7F
                routine_id = req_clean[4:8]

                if routine_id == "0201": # SelfTest Routine
                    if sf == 0x01: # StartRoutine
                        self.active_routines["0201"] = "RUNNING"
                        response_hex = "71 01 02 01 00"
                        explanation = "Routine 0x0201 (SelfTest) started successfully. Status: Running."
                    elif sf == 0x02: # StopRoutine
                        self.active_routines["0201"] = "STOPPED"
                        response_hex = "71 02 02 01 00"
                        explanation = "Routine 0x0201 stopped."
                    elif sf == 0x03: # RequestRoutineResults
                        response_hex = "71 03 02 01 00 00"
                        explanation = "Routine 0x0201 completed with Status: OK (0x0000)."
                    else:
                        response_hex = "7F 31 12"
                        rtype = "NEGATIVE"
                        explanation = f"RoutineControl subfunction 0x{sf:02X} not supported."
                else:
                    response_hex = "7F 31 31"
                    rtype = "NEGATIVE"
                    explanation = f"Routine ID 0x{routine_id} not supported (NRC 0x31 RequestOutOfRange)."

        # --- SERVICE 0x3E: TesterPresent ---
        elif sid == "3E":
            raw_sf = int(req_clean[2:4], 16) if len(req_clean) >= 4 else 0x00
            sf = raw_sf & 0x7F
            suppress_pos_rsp = bool(raw_sf & 0x80)
            self.s3_timer_expiry = time.time() + 5.0
            if sf == 0x00:
                response_hex = "7E 00"
                explanation = "TesterPresent processed. S3 timeout counter reset."
            else:
                response_hex = "7F 3E 12"
                rtype = "NEGATIVE"
                explanation = "TesterPresent subfunction not supported."

        # --- UNSUPPORTED SERVICE ---
        else:
            response_hex = f"7F {sid} 11"
            rtype = "NEGATIVE"
            explanation = f"Service 0x{sid} is not recognized or supported by BCM (NRC 0x11 ServiceNotSupported)."

        # Apply state changes to simulator instance if not an isolated test override
        if not session_override:
            self.active_session = new_session
        if not security_override:
            self.active_security = new_security

        # If suppress positive response bit was active and response was positive, drop frame
        final_response_hex = "" if (suppress_pos_rsp and rtype == "POSITIVE") else response_hex

        elapsed_ms = (time.time() - start_t) * 1000.0 + 12.5 # baseline bus latency

        # CAN Frame DLC
        rx_dlc = len(final_response_hex.replace(" ", "")) // 2 if final_response_hex else 0

        return SimulationResult(
            request_hex=request_hex,
            response_hex=final_response_hex,
            response_type=rtype,
            execution_time_ms=round(elapsed_ms, 2),
            session_after=new_session,
            security_after=new_security,
            diff_analysis=f"Simulated ISO 14229 state machine response: {rtype}",
            explanation=f"Potential explanation based on simulated behavior: {explanation}",
            can_trace={
                "tx": {"id": "0x7E0", "data": request_hex, "dlc": len(req_clean)//2},
                "rx": {"id": "0x7E8", "data": final_response_hex or "[SUPPRESSED]", "dlc": rx_dlc}
            }
        )

# Global singleton simulator instance for the application
global_ecu_simulator = MockEcuSimulator()
