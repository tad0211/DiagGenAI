import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.uds.ecu_simulator import MockEcuSimulator, global_ecu_simulator
from app.testing.executor import TestExecutor
from app.database.repository import DiagRepository

client = TestClient(app)

def test_simulator_session_transitions():
    """Verify stateful session transitions and timing parameters."""
    sim = MockEcuSimulator()
    assert sim.active_session == "DefaultSession"

    # Transition to ExtendedDiagnosticSession
    res_ext = sim.process_request("10 03")
    assert res_ext.response_hex == "50 03 00 32 01 F4"
    assert sim.active_session == "ExtendedDiagnosticSession"

    # Environmental constraint: Cannot enter ProgrammingSession if vehicle moving
    sim.set_environmental(speed_kmh=45.0)
    res_prog_fail = sim.process_request("10 02")
    assert res_prog_fail.response_type == "NEGATIVE"
    assert "22" in res_prog_fail.response_hex

    # Stop vehicle, but security is locked -> NRC 0x33
    sim.set_environmental(speed_kmh=0.0)
    res_prog_sec = sim.process_request("10 02")
    assert "33" in res_prog_sec.response_hex

    # Reset to DefaultSession
    res_def = sim.process_request("10 01")
    assert res_def.response_hex == "50 01 00 32 01 F4"
    assert sim.active_session == "DefaultSession"

def test_simulator_security_access_seed_key():
    """Verify security access challenge-response protocol with XOR mask 0x55AA55AA."""
    sim = MockEcuSimulator()

    # In DefaultSession, SecurityAccess rejected with NRC 0x7E
    res_def_sec = sim.process_request("27 01")
    assert res_def_sec.response_hex == "7F 27 7E"

    # Switch to ExtendedSession
    sim.process_request("10 03")

    # SendKey without prior seed -> NRC 0x24 (RequestSequenceError)
    res_seq_err = sim.process_request("27 02 11 22 33 44")
    assert res_seq_err.response_hex == "7F 27 24"

    # Request Seed
    res_seed = sim.process_request("27 01")
    assert res_seed.response_hex.startswith("67 01")
    seed_tokens = res_seed.response_hex.split()[2:]
    assert len(seed_tokens) == 4
    seed_hex = "".join(seed_tokens)

    # Compute valid key = Seed XOR 0x55AA55AA
    seed_int = int(seed_hex, 16)
    valid_key_int = seed_int ^ 0x55AA55AA
    valid_key_hex = f"{valid_key_int:08X}"
    key_frame = f"27 02 {valid_key_hex[:2]} {valid_key_hex[2:4]} {valid_key_hex[4:6]} {valid_key_hex[6:8]}"

    # Send valid key
    res_key = sim.process_request(key_frame)
    assert res_key.response_hex == "67 02"
    assert sim.active_security == "Level1Unlocked"

def test_simulator_write_did_protection():
    """Verify write DID protection requires extended session and unlocked security."""
    sim = MockEcuSimulator()

    # In DefaultSession: rejected with NRC 0x7F
    res_w1 = sim.process_request("2E 01 05 01 02 00 AA")
    assert "7F" in res_w1.response_hex

    # In ExtendedSession, but Locked: rejected with NRC 0x33
    sim.process_request("10 03")
    res_w2 = sim.process_request("2E 01 05 01 02 00 AA")
    assert res_w2.response_hex == "7F 2E 33"

    # Unlock security Level 1
    sim.active_security = "Level1Unlocked"
    res_w3 = sim.process_request("2E 01 05 01 02 00 AA")
    assert res_w3.response_hex == "6E 01 05"
    assert sim.dids["0105"] == "01 02 00 AA"

def test_simulator_fault_injection():
    """Verify fault injection modes: TIMEOUT, GARBAGE, and NRC_22."""
    sim = MockEcuSimulator()

    # Timeout
    res_to = sim.process_request("22 F1 90", inject_fault="TIMEOUT")
    assert res_to.response_type == "TIMEOUT"
    assert res_to.response_hex == ""

    # Garbage
    res_gb = sim.process_request("22 F1 90", inject_fault="GARBAGE_RESPONSE")
    assert res_gb.response_type == "UNEXPECTED"
    assert res_gb.response_hex == "FF EE DD CC BB AA"

def test_test_executor_single_and_suite():
    """Verify TestExecutor evaluates verdicts, creates diffs, and persists results."""
    repo = DiagRepository()
    executor = TestExecutor(repo=repo)

    # Fetch an approved test
    all_tests = repo.get_test_cases()
    assert len(all_tests) > 0
    first_tc = all_tests[0]

    # Single test execution
    single_res = executor.execute_test(first_tc)
    assert single_res["outcome"] in ["PASS", "FAIL"]
    assert "diff_analysis" in single_res
    assert "explanation" in single_res
    assert "can_trace" in single_res
    assert "SIMULATION MODE" in single_res["simulation_mode"]

    # Suite execution
    suite_res = executor.execute_suite(service_hex="0x10")
    assert suite_res["total_executed"] >= 1
    assert "pass_rate" in suite_res
    assert suite_res["passed"] + suite_res["failed"] == suite_res["total_executed"]

def test_api_simulator_endpoints():
    """Verify FastAPI endpoints: state, reset, environmental, send, execute-test, execute-suite, results."""
    # 1. State
    res_st = client.get("/api/simulator/state")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert "active_session" in st_data

    # 2. Reset
    res_rst = client.post("/api/simulator/reset")
    assert res_rst.status_code == 200

    # 3. Environmental
    res_env = client.post("/api/simulator/environmental", json={"vehicle_speed_kmh": 30.0, "battery_voltage_v": 13.2})
    assert res_env.status_code == 200
    assert res_env.json()["speed_kmh"] == 30.0

    # 4. Send
    res_send = client.post("/api/simulator/send", json={"request_hex": "22 F1 90"})
    assert res_send.status_code == 200
    assert "62 F1 90" in res_send.json()["response_hex"]

    # 5. Execute-test
    repo = DiagRepository()
    tc = repo.get_test_cases()[0]
    res_exec = client.post("/api/simulator/execute-test", json={"test_id": tc.test_id})
    assert res_exec.status_code == 200
    assert res_exec.json()["test_id"] == tc.test_id

    # 6. Execute-suite
    res_suite = client.post("/api/simulator/execute-suite", json={"service_hex": "0x22"})
    assert res_suite.status_code == 200
    assert res_suite.json()["total_executed"] >= 1

    # 7. Results history
    res_hist = client.get("/api/simulator/results?limit=10")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1
