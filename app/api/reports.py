import json
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, HTMLResponse
from app.database.repository import DiagRepository
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/engineering", response_class=PlainTextResponse)
def get_engineering_report():
    repo = DiagRepository()
    summary = repo.get_dashboard_summary()
    docs = repo.get_documents()
    services = repo.get_services()
    tests = repo.get_test_cases()
    results = repo.get_test_results(limit=50)

    doc_lines = "\n".join([f"- **{d.name}** (v{d.version}, Type: {d.doc_type}, Status: {d.status})" for d in docs])
    service_lines = "\n".join([f"- **{s.service_id_hex} ({s.name})**: {len(s.subfunctions)} subfunctions, {len(s.parameters)} parameters, Standard: {getattr(s, 'standard_ref', 'ISO 14229-1')}" for s in services])
    test_lines = "\n".join([f"- [{t.review_status}] **{t.test_id}** ({t.test_type}): {t.objective} | Req: {t.requirement_id or 'N/A'}" for t in tests[:50]])

    passed_cnt = sum(1 for r in results if r.outcome == "PASS")
    total_res = len(results)
    pass_rate = (passed_cnt / total_res * 100.0) if total_res > 0 else 0.0

    report = f"""# DiagGenAI - Comprehensive Engineering Validation Report
**Project:** DiagGenAI Academic Prototype
**ECU Under Evaluation:** Body Control Module (BCM-Demo-ECU)
**Notice:** {settings.SAFETY_BANNER}

---

## 1. Executive Summary & Verification KPIs
- **Indexed Specification Documents:** {summary['documents_indexed']}
- **Configured UDS Diagnostic Services:** {summary['uds_services']}
- **Parameters / DIDs Analyzed:** {summary['parameters_count']}
- **Total Test Cases Synthesized:** {summary['total_tests']}
  - Approved by Lead Engineer: {summary['approved_tests']}
  - Pending Human Review: {summary['pending_tests']}
  - Rejected: {summary['rejected_tests']}
- **Simulation Test Runs:** {passed_cnt} Passed, {total_res - passed_cnt} Failed (Pass Rate: {pass_rate:.1f}%)

---

## 2. Specification Sources Analyzed
{doc_lines}

---

## 3. Services & Coverage Status
### Multi-Dimensional Coverage Breakdown:
- **Requirement Coverage:** {summary['coverage'].get('req_coverage', 0.0):.1f}%
- **Service Coverage:** {summary['coverage'].get('service_coverage', 0.0):.1f}%
- **Subfunction Coverage:** {summary['coverage'].get('subfunction_coverage', 0.0):.1f}%
- **Positive Test Coverage:** {summary['coverage'].get('positive_coverage', 0.0):.1f}%
- **Negative (NRC) Test Coverage:** {summary['coverage'].get('negative_coverage', 0.0):.1f}%
- **Session Transition Coverage:** {summary['coverage'].get('session_coverage', 0.0):.1f}%
- **Security Access Coverage:** {summary['coverage'].get('security_coverage', 0.0):.1f}%
- **Boundary Test Coverage:** {summary['coverage'].get('boundary_coverage', 0.0):.1f}%

### Configured Services:
{service_lines}

---

## 4. Test Cases & Review Status
{test_lines}

---

## 5. Traceability & Safety Verification
- **Traceability:** Requirements -> UDS Services -> Test Scenarios -> Execution Results verified via deterministic mapping.
- **Safety Guardrail:** All generated artifacts require human review prior to bench deployment. Every AI output starts in `PENDING_REVIEW` state.

---

## 6. Hardware-in-the-Loop (HIL) Transition Checklist
- [ ] Confirm P2/P2* server timing on real microcontroller clock.
- [ ] Verify voltage threshold triggers (brownout / overvoltage) on bench power supply.
- [ ] Perform physical CAN bus load analysis at 500k baud with active background traffic.
- [ ] Run automated regression test suite via Vector CANoe / CAPL.

---

## 7. Engineering Limitations & Scope
This report was generated using the DiagGenAI assistant in **SIMULATION MODE**. No physical ECU or CAN bus was connected. Actual timing, bus load, and voltage thresholds must be verified in Hardware-in-the-Loop (HIL) environments.
"""
    return report

@router.get("/html", response_class=HTMLResponse)
def get_html_report():
    repo = DiagRepository()
    summary = repo.get_dashboard_summary()
    docs = repo.get_documents()
    services = repo.get_services()
    tests = repo.get_test_cases()
    results = repo.get_test_results(limit=50)

    doc_rows = "".join([f"<tr><td><b>{d.name}</b></td><td>v{d.version}</td><td>{d.doc_type}</td><td><span class='badge'>{d.status}</span></td></tr>" for d in docs])
    srv_rows = "".join([f"<tr><td><code>{s.service_id_hex}</code></td><td>{s.name}</td><td>{len(s.subfunctions)}</td><td>{len(s.parameters)}</td><td>{getattr(s, 'standard_ref', 'ISO 14229-1')}</td></tr>" for s in services])
    tc_rows = "".join([f"<tr><td><code>{t.test_id}</code></td><td>{t.test_type}</td><td>{t.objective[:50]}...</td><td><code>{t.request_hex}</code></td><td><span class='badge'>{t.review_status}</span></td></tr>" for t in tests[:30]])

    passed_cnt = sum(1 for r in results if r.outcome == "PASS")
    total_res = len(results)
    pass_rate = (passed_cnt / total_res * 100.0) if total_res > 0 else 0.0

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>DiagGenAI - Comprehensive Engineering Validation Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; margin: 0; line-height: 1.6; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
  .banner {{ background: #dc2626; color: white; padding: 10px 16px; border-radius: 6px; font-weight: 800; font-size: 0.85rem; letter-spacing: 1px; text-align: center; margin-bottom: 24px; }}
  h1 {{ color: #38bdf8; font-size: 1.8rem; margin-top: 0; }}
  h2 {{ color: #f8fafc; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-top: 28px; font-size: 1.25rem; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
  .kpi-card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; text-align: center; }}
  .kpi-card .val {{ font-size: 1.6rem; font-weight: 800; color: #38bdf8; }}
  .kpi-card .lbl {{ font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.84rem; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #1e293b; }}
  th {{ background: #0f172a; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; }}
  code {{ font-family: monospace; color: #38bdf8; background: #0b0f19; padding: 2px 6px; border-radius: 4px; }}
  .badge {{ background: #10b98122; color: #10b981; border: 1px solid #10b98155; padding: 2px 6px; border-radius: 4px; font-size: 0.70rem; font-weight: 700; }}
  @media print {{ body {{ background: white; color: black; }} .container {{ border: none; box-shadow: none; padding: 0; }} }}
</style>
</head>
<body>
<div class="container">
  <div class="banner">⚠️ {settings.SAFETY_BANNER}</div>
  <h1>⚡ DiagGenAI - Comprehensive Engineering Validation Report</h1>
  <div style="font-size: 0.85rem; color: #94a3b8;">Target System: <b>Body Control Module (BCM-Demo-ECU)</b> | Release: <b>1.0.0</b></div>

  <h2>1. Executive Summary & KPIs</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="val">{summary['total_tests']}</div><div class="lbl">Synthesized Tests</div></div>
    <div class="kpi-card"><div class="val" style="color:#10b981;">{summary['coverage']['req_coverage']:.0f}%</div><div class="lbl">Req Coverage</div></div>
    <div class="kpi-card"><div class="val" style="color:#10b981;">{pass_rate:.1f}%</div><div class="lbl">Simulation Pass Rate</div></div>
    <div class="kpi-card"><div class="val" style="color:#a855f7;">{summary['uds_services']}</div><div class="lbl">Services Verified</div></div>
  </div>

  <h2>2. Specification Document Inventory</h2>
  <table>
    <thead><tr><th>Document</th><th>Version</th><th>Type</th><th>Status</th></tr></thead>
    <tbody>{doc_rows}</tbody>
  </table>

  <h2>3. Configured UDS Diagnostic Services</h2>
  <table>
    <thead><tr><th>Service Hex</th><th>Service Name</th><th>Subfunctions</th><th>DIDs</th><th>Standard</th></tr></thead>
    <tbody>{srv_rows}</tbody>
  </table>

  <h2>4. Diagnostic Test Cases Preview</h2>
  <table>
    <thead><tr><th>Test ID</th><th>Type</th><th>Objective</th><th>Request Frame</th><th>Review Status</th></tr></thead>
    <tbody>{tc_rows}</tbody>
  </table>

  <h2>5. ASPICE & Safety Governance Notice</h2>
  <p style="font-size: 0.85rem; color: #cbd5e1;">
    All diagnostic test generation artifacts were produced under human-in-the-loop governance. Every synthesized test starts in <b>PENDING_REVIEW</b> status and requires approval by a lead diagnostic engineer before bench deployment.
  </p>
</div>
</body>
</html>
"""
    return html

@router.get("/summary")
def get_report_summary():
    repo = DiagRepository()
    return repo.get_dashboard_summary()
