"""
DiagGenAI — Automotive Diagnostic Intelligence Platform
Enterprise Engineering Workstation Design System.
Provides calm, mature, light-palette styling, refined typography,
clean tables, contextual panels, and precise technical metadata.
"""

import streamlit as st
from typing import Optional, List, Dict, Any

# Minimalist Monochrome Line Icons (Lucide style, 15x15)
ICONS = {
    "activity": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    "layers": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>',
    "book": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>',
    "search": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    "terminal": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>',
    "cpu": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
    "shield": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
    "flask": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31L4.69 19.3A2 2 0 0 0 6.44 22h11.12a2 2 0 0 0 1.75-2.7L14 9.31V2"></path><line x1="8.5" y1="2" x2="15.5" y2="2"></line><line x1="14" y1="9.3" x2="10" y2="9.3"></line></svg>',
    "chart": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    "play": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>',
    "code": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
    "git": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><path d="M13 6h3a2 2 0 0 1 2 2v7"></path><line x1="6" y1="9" x2="6" y2="21"></line></svg>',
    "check": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    "x": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    "alert": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
}

def get_icon(name: str) -> str:
    """Returns SVG line icon HTML string."""
    return ICONS.get(name, "")

def inject_automotive_theme():
    """
    Injects enterprise light workstation CSS:
    - Primary background: warm white / light cool gray (#f8fafc)
    - Surfaces: crisp white (#ffffff)
    - Text: deep charcoal (#0f172a, #1e293b)
    - Subtle hairline borders (#e2e8f0)
    - Accent: muted navy / steel blue (#1e3a8a, #2563eb)
    - Monospace ONLY for frames, logs, and code
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Global Reset & Base Styling */
        html, body, [data-testid="stAppViewContainer"], .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            background-color: #f8fafc !important;
            color: #0f172a !important;
            -webkit-font-smoothing: antialiased;
        }

        /* Top margin & container spacing */
        .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 98% !important;
        }

        /* Sidebar: Clean, quiet, enterprise navigation */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
        }

        /* Sidebar Navigation Radio Styling */
        div[data-testid="stRadio"] > div {
            gap: 2px !important;
        }

        div[data-testid="stRadio"] label {
            padding: 6px 10px !important;
            border-radius: 4px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #475569 !important;
            transition: background 0.12s ease, color 0.12s ease !important;
            border-left: 2px solid transparent !important;
            cursor: pointer !important;
        }

        div[data-testid="stRadio"] label:hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }

        div[data-testid="stRadio"] label[data-checked="true"],
        div[data-testid="stRadio"] input:checked + div {
            background-color: #f1f5f9 !important;
            color: #1e3a8a !important;
            font-weight: 600 !important;
            border-left: 2px solid #2563eb !important;
        }

        /* Clean Top Header Shell */
        .app-header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px 16px;
            margin-bottom: 20px;
        }

        .app-brand-name {
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.6px;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .app-brand-sub {
            font-size: 0.72rem;
            color: #64748b;
            font-weight: 500;
            margin-top: 1px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .header-meta-strip {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.76rem;
            color: #64748b;
        }

        .meta-divider {
            color: #cbd5e1;
        }

        .meta-val {
            color: #0f172a;
            font-weight: 600;
        }

        .sim-indicator {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.72rem;
            font-weight: 600;
            color: #92400e;
            background: #fef3c7;
            border: 1px solid #fde68a;
            border-radius: 3px;
            padding: 2px 7px;
        }

        /* Section Titles */
        .section-heading {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.2px;
            margin-bottom: 2px;
        }

        .section-subheading {
            font-size: 0.80rem;
            color: #64748b;
            margin-bottom: 16px;
        }

        /* Subtle Summary Row (Non-card, integrated) */
        .summary-metric-row {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            padding: 14px 18px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .summary-metric-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .summary-metric-label {
            font-size: 0.68rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }

        .summary-metric-value {
            font-size: 1.45rem;
            font-weight: 700;
            color: #0f172a;
            font-variant-numeric: tabular-nums;
        }

        .summary-metric-caption {
            font-size: 0.72rem;
            color: #94a3b8;
        }

        /* Refined Coverage Bars */
        .cov-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 0.80rem;
            border-bottom: 1px solid #f1f5f9;
        }

        .cov-label {
            color: #334155;
            font-weight: 500;
        }

        .cov-val {
            font-size: 0.80rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            color: #0f172a;
            margin-right: 12px;
            min-width: 44px;
            text-align: right;
        }

        .cov-bar-bg {
            flex: 1;
            height: 5px;
            background: #e2e8f0;
            border-radius: 2px;
            overflow: hidden;
            margin-left: 12px;
            margin-right: 12px;
        }

        .cov-bar-fill-muted {
            height: 100%;
            background: #2563eb;
            border-radius: 2px;
        }

        .cov-bar-fill-amber {
            height: 100%;
            background: #d97706;
            border-radius: 2px;
        }

        /* Status Badges: Soft, quiet pastel fills */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 7px;
            border-radius: 3px;
            font-size: 0.70rem;
            font-weight: 600;
            letter-spacing: 0.2px;
            text-transform: uppercase;
        }

        .status-pass { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
        .status-pending { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
        .status-fail { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
        .status-retest { background: #f0f9ff; color: #075985; border: 1px solid #bae6fd; }

        /* Monospace Hex Token */
        .hex-token-clean {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.80rem;
            font-weight: 500;
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid #e2e8f0;
            padding: 2px 6px;
            border-radius: 3px;
        }

        /* CAN Trace Terminal: Clean, high-legibility light technical monitor */
        .can-trace-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            line-height: 1.55;
            color: #1e293b;
            overflow-x: auto;
        }

        .can-line {
            display: flex;
            gap: 12px;
            padding: 2px 0;
            border-bottom: 1px solid #f8fafc;
        }

        .can-time { color: #94a3b8; }
        .can-dir-tx { color: #2563eb; font-weight: 600; }
        .can-dir-rx { color: #16a34a; font-weight: 600; }
        .can-id { color: #64748b; }
        .can-bytes { color: #0f172a; font-weight: 600; }
        .can-desc { color: #475569; }

        /* Buttons & Controls: Subdued, professional */
        button[kind="primary"] {
            background-color: #1e3a8a !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 4px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }

        button[kind="primary"]:hover {
            background-color: #1e40af !important;
        }

        button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #334155 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 4px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
        }

        button[kind="secondary"]:hover {
            background-color: #f8fafc !important;
            border-color: #94a3b8 !important;
        }

        /* Input Fields: Crisp white, light border */
        input[type="text"], input[type="number"], textarea, select, div[data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 4px !important;
            font-size: 0.84rem !important;
        }

        /* Streamlit Dataframe Overrides */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0 !important;
            border-radius: 4px !important;
            background: #ffffff !important;
        }

        /* Streamlit Tabs: Clean bottom border */
        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #64748b !important;
            border: none !important;
            padding: 8px 14px !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #1e3a8a !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #2563eb !important;
        }

        /* Contextual Panel */
        .context-panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 14px;
            margin-bottom: 16px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_global_header(
    target_ecu: str = "BCM-Demo-ECU",
    active_session: str = "DefaultSession",
    security_state: str = "Locked"
):
    """Renders the top application header with subtle metadata and simulation notice."""
    inject_automotive_theme()

    clean_sess = active_session.replace("DiagnosticSession", "").replace("Session", "")
    sess_display = f"{clean_sess} Session" if clean_sess else "Default Session"

    st.markdown(f"""
    <div class="app-header-bar">
        <div>
            <div class="app-brand-name">
                <span style="display:inline-block; width:3px; height:14px; background:#2563eb; border-radius:1px;"></span>
                DIAGGENAI
            </div>
            <div class="app-brand-sub">Automotive Diagnostic Intelligence</div>
        </div>
        <div class="header-meta-strip">
            <span class="sim-indicator">
                Simulation Environment &bull; No physical ECU connection
            </span>
            <span class="meta-divider">&bull;</span>
            <span>Target: <span class="meta-val">{target_ecu}</span></span>
            <span class="meta-divider">&bull;</span>
            <span>Session: <span class="meta-val">{sess_display}</span></span>
            <span class="meta-divider">&bull;</span>
            <span>Security: <span class="meta-val">{security_state}</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title: str, subtitle: str = ""):
    """Renders a restrained, clean section title in sentence/title case."""
    sub_html = f'<div class="section-subheading">{subtitle}</div>' if subtitle else '<div style="height:6px;"></div>'
    st.markdown(f"""
    <div>
        <div class="section-heading">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def render_status_pill(status: str) -> str:
    """Returns HTML for a quiet, professional status badge with pastel tint."""
    s = (status or "").upper().strip()
    if s in ["APPROVED", "PASS", "PASSED", "INDEXED", "VALID"]:
        cls = "status-pass"
    elif s in ["PENDING_REVIEW", "PENDING", "WARNING", "REQUIRES REVIEW"]:
        cls = "status-pending"
    elif s in ["REQUIRES_RETEST", "RETEST"]:
        cls = "status-retest"
    else:
        cls = "status-fail"
    return f'<span class="status-badge {cls}">{status}</span>'

def render_hex_token(hex_str: str) -> str:
    """Returns formatted clean monospace hex token."""
    return f'<span class="hex-token-clean">{hex_str}</span>'

def render_coverage_bar(label: str, pct: float, detail: str = ""):
    """Renders a clean, single-accent horizontal coverage bar."""
    fill_cls = "cov-bar-fill-muted" if pct >= 50.0 else "cov-bar-fill-amber"
    st.markdown(f"""
    <div class="cov-row">
        <span class="cov-label" style="width: 170px;">{label}</span>
        <div class="cov-bar-bg">
            <div class="{fill_cls}" style="width: {min(100.0, max(0.0, pct))}%;"></div>
        </div>
        <span class="cov-val">{pct:.1f}%</span>
        {f'<span style="font-size:0.72rem; color:#94a3b8; width: 100px; text-align:right;">{detail}</span>' if detail else ''}
    </div>
    """, unsafe_allow_html=True)

def render_can_trace(timestamp: str, direction: str, can_id: str, dlc: int, data_bytes: str, interpretation: str):
    """Renders a single line for the clean technical CAN trace view."""
    dir_class = "can-dir-tx" if direction == "Tx" else "can-dir-rx"
    return f"""
    <div class="can-line">
        <span class="can-time">[{timestamp}]</span>
        <span class="{dir_class}">{direction:<3}</span>
        <span class="can-id">{can_id}</span>
        <span class="can-bytes">{data_bytes:<24}</span>
        <span class="can-desc">// {interpretation}</span>
    </div>
    """

# Backward compatibility stubs
def render_kpi_card(title: str, value: str, subtext: str = "", status: str = "normal"):
    """Compact inline metric cell."""
    st.markdown(f"""
    <div style="padding: 10px 14px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px;">
        <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
        <div style="font-size: 1.35rem; font-weight: 700; color: #0f172a; margin-top: 2px;">{value}</div>
        {f'<div style="font-size: 0.70rem; color: #94a3b8; margin-top: 1px;">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def render_metric_hud(title: str, value: str, subtext: str = "", accent_color: str = "#2563eb", icon: str = ""):
    render_kpi_card(title, value, subtext)

def render_safety_and_telemetry():
    render_global_header()
