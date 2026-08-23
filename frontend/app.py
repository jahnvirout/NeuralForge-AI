import os
import requests
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="NeuralForge AI — ML Repository Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend API Endpoint Configuration
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------
# NeuralForge AI Design System
# Minimalist, Apple-inspired editorial scale, pure Inter font,
# preserved Material Icon fonts, and responsive layout primitives.
# ---------------------------------------------------------
RAW_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

@font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 300 900;
    font-display: swap;
    src: url('https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2') format('woff2');
    unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* Base Canvas */
.stApp {
    background-color: #0c0d11;
    color: #f5f3ee;
}

/* Typography Hierarchy — Strictly Inter on all text nodes */
html, body,
div:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]):not([class*="material-icons"]),
p:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]):not([class*="material-icons"]),
span:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]):not([class*="material-icons"]),
h1, h2, h3, h4, h5, h6,
input, textarea, button:not([data-testid="stIconMaterial"]),
select, label, [data-testid="stMarkdownContainer"] p,
.stButton button, .stTextInput input, .stSelectbox,
[data-baseweb="tab"] p, [data-testid="stTab"] p {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Explicit Preservation of Streamlit / Material Symbols Icon Ligatures */
[data-testid="stIconMaterial"],
[data-testid="stIconMaterial"] *,
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
button[data-testid*="stBaseButton-header"] span,
[data-testid="stSidebarCollapseButton"] span {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
}

code, pre, .mono-code {
    font-family: 'Inter', ui-monospace, SFMono-Regular, Consolas, monospace !important;
    font-feature-settings: "tnum" 1;
}

/* Sidebar Styling & Contrast */
section[data-testid="stSidebar"] {
    background-color: #08090c !important;
    border-right: 1px solid #1e2029 !important;
}

.sidebar-brand-wrapper {
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid #1e2029;
    margin-bottom: 1.5rem;
}

.sidebar-logo {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-sub {
    font-size: 0.76rem;
    color: #888a93;
    letter-spacing: -0.01em;
    margin-top: 0.2rem;
}

/* Header Container — Confident Apple-scale Proportions */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 2.25rem 0 1.5rem 0;
    margin-bottom: 2rem;
    border-bottom: 1px solid #22242b;
}

.brand-title {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.045em !important;
    color: #ffffff !important;
    line-height: 1.08 !important;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0;
}

.brand-tag {
    font-size: 1.02rem !important;
    font-weight: 400 !important;
    color: #888a93 !important;
    letter-spacing: -0.015em !important;
    margin-top: 0.5rem !important;
    line-height: 1.4 !important;
}

/* Monochrome / Semantic Status Badges */
.status-pill-online {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid #383a42;
    background: #14151a;
    color: #ffffff;
    transition: background 0.18s ease, border-color 0.18s ease;
}

.status-pill-offline {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.76rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid #2c2e35;
    background: #101114;
    color: #888a93;
}

.status-dot-solid {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #ffffff;
}

.status-dot-ring {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    border: 1px solid #888a93;
    background-color: transparent;
}

/* Tab Navigation — Smooth Focus, Clear Active/Inactive Contrast */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background-color: transparent;
    padding: 0 0 0.65rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2.25rem;
    overflow-x: auto;
}

.stTabs button[data-baseweb="tab"],
.stTabs button[data-testid="stTab"],
div[data-baseweb="tab-list"] button {
    height: auto !important;
    padding: 0.5rem 0 !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    transition: color 0.18s ease, border-color 0.18s ease, opacity 0.18s ease !important;
}

.stTabs button[data-baseweb="tab"] p,
.stTabs button[data-testid="stTab"] p,
div[data-baseweb="tab-list"] button p {
    font-size: 0.96rem !important;
    letter-spacing: -0.015em !important;
    margin: 0 !important;
    transition: color 0.18s ease !important;
}

.stTabs button[data-baseweb="tab"][aria-selected="false"] p,
.stTabs button[data-testid="stTab"][aria-selected="false"] p {
    color: #6e707a !important;
    font-weight: 500 !important;
}

.stTabs button[data-baseweb="tab"][aria-selected="false"]:hover p,
.stTabs button[data-testid="stTab"][aria-selected="false"]:hover p {
    color: #d4d4d8 !important;
}

.stTabs button[data-baseweb="tab"][aria-selected="true"] p,
.stTabs button[data-testid="stTab"][aria-selected="true"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

.stTabs [aria-selected="true"] {
    border-bottom: 2px solid #ffffff !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* Headings & Section Dividers */
.section-headline {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #ffffff !important;
    margin-bottom: 0.35rem !important;
}

.section-description {
    font-size: 0.92rem !important;
    color: #888a93 !important;
    margin-bottom: 1.75rem !important;
    line-height: 1.6 !important;
}

/* Overview & Score Hero Component */
.score-hero-container {
    padding: 2.25rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2rem;
}

.score-display-wrapper {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
}

.score-huge-num {
    font-size: 4.5rem;
    font-weight: 800;
    letter-spacing: -0.05em;
    line-height: 1;
    color: #ffffff;
}

.score-total-denom {
    font-size: 1.35rem;
    font-weight: 400;
    color: #6e707a;
    letter-spacing: -0.02em;
}

.score-status-text {
    font-size: 1.02rem;
    font-weight: 500;
    color: #b0b2ba;
    margin-top: 0.65rem;
    letter-spacing: -0.015em;
}

/* Sub-Score Strip */
.subscore-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    padding: 1.25rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2.25rem;
}

.subscore-card {
    display: flex;
    flex-direction: column;
}

.subscore-val {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.035em;
    color: #ffffff;
}

.subscore-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #888a93;
    margin-top: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Diagnostic Finding Rows */
.issue-row {
    padding: 1.4rem 0;
    border-bottom: 1px solid #1c1d24;
    transition: background 0.18s ease;
}

.issue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.45rem;
}

.issue-file-loc {
    font-size: 0.92rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.015em;
}

.badge-high {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #f87171;
    background: #251416;
    border: 1px solid #4a2428;
    padding: 0.22rem 0.6rem;
    border-radius: 4px;
}

.badge-med {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #fbbf24;
    background: #251d10;
    border: 1px solid #483918;
    padding: 0.22rem 0.6rem;
    border-radius: 4px;
}

.badge-clean {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #4ade80;
    background: #122417;
    border: 1px solid #1c4526;
    padding: 0.22rem 0.6rem;
    border-radius: 4px;
}

.issue-title-text {
    font-size: 0.92rem;
    font-weight: 400;
    color: #d4d4d8;
    line-height: 1.55;
    margin-bottom: 0.45rem;
}

.issue-remedy-box {
    font-size: 0.86rem;
    font-weight: 400;
    color: #a1a1aa;
    background: #111218;
    border-left: 2px solid #52525b;
    padding: 0.6rem 0.95rem;
    margin-top: 0.4rem;
    border-radius: 0 4px 4px 0;
    line-height: 1.55;
}

/* Chat UI Messages — Apple Editorial Spacing & Cards */
.chat-bubble-user {
    background: #13141b;
    border: 1px solid #252733;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.25rem;
    font-size: 0.94rem;
    color: #f5f3ee;
    line-height: 1.6;
}

.chat-role-tag {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #888a93;
    margin-bottom: 0.35rem;
}

.chat-bubble-user p {
    margin: 0 !important;
    color: #f5f3ee !important;
}

.chat-bubble-ai {
    background: transparent;
    padding: 1rem 0.2rem;
    margin-bottom: 1.75rem;
    font-size: 0.94rem;
    color: #d4d4d8;
    line-height: 1.68;
    border-bottom: 1px solid #1e2029;
}

.mono-banner {
    padding: 1rem 1.25rem;
    background: #111218;
    border: 1px solid #252733;
    border-radius: 8px;
    font-size: 0.88rem;
    color: #a1a1aa;
    margin-bottom: 1.5rem;
    line-height: 1.55;
}

/* Interactive Buttons — No-wrap & Subtle 180ms ease transitions */
.stButton button {
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    white-space: nowrap !important;
    transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease !important;
    border: 1px solid #2c2e3a !important;
    background: #14151e !important;
    color: #e4e4e7 !important;
}

.stButton button:hover {
    background: #20222e !important;
    border-color: #4a4d60 !important;
    color: #ffffff !important;
}

.stButton button[kind="primary"] {
    background: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #ffffff !important;
    font-weight: 600 !important;
}

.stButton button[kind="primary"]:hover {
    background: #e4e4e7 !important;
    color: #000000 !important;
    border-color: #e4e4e7 !important;
}
</style>
"""

# Inject CSS cleanly via st.html (or st.markdown as fallback)
if hasattr(st, "html"):
    st.html(RAW_CSS)
else:
    st.markdown(RAW_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# State Initialization (Clean Single-Source-of-Truth)
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chunks_found" not in st.session_state:
    st.session_state.chunks_found = 0
if "repo_path" not in st.session_state:
    st.session_state.repo_path = "data/sample_repo"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "markdown_report" not in st.session_state:
    st.session_state.markdown_report = None


# ---------------------------------------------------------
# API Helper Functions (Exact Contracts Preserved)
# ---------------------------------------------------------
def parse_api_response(res):
    try:
        data = res.json()
    except ValueError:
        data = {
            "error": f"Backend returned HTTP {res.status_code}: "
                     f"{res.text[:300] or 'empty response'}"
        }

    return 200 <= res.status_code < 300, data

def check_backend_health():
    """Pings backend root endpoint to check connectivity."""
    try:
        res = requests.get(f"{API_BASE_URL}/", timeout=30)
        if res.status_code == 200:
            return True, res.json().get("message", "API running")
    except Exception as e:
        return False, str(e)
    return False, "Non-200 response"


def api_upload_repo(repo_path: str):
    """Calls POST /upload-repo endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/upload-repo",
            json={"repo_path": repo_path},
            timeout=300,
        )
        return parse_api_response(res)
    except Exception as e:
        return False, {"error": f"Failed to connect to backend: {str(e)}"}


def api_ask_question(session_id: str, question: str):
    """Calls POST /ask endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/ask",
            json={"session_id": session_id, "question": question},
            timeout=120,
        )
        return parse_api_response(res)
    except Exception as e:
        return False, {"error": f"Inquiry failed: {str(e)}"}


def api_analyze_repo(repo_path: str):
    """Calls POST /analyze endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/analyze",
            json={"repo_path": repo_path},
            timeout=180,
        )
        return parse_api_response(res)
    except Exception as e:
        return False, {"error": f"Static ML analysis failed: {str(e)}"}


def api_get_report(repo_path: str):
    """Calls POST /report endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/report",
            json={"repo_path": repo_path},
            timeout=180,
        )
        return parse_api_response(res)
    except Exception as e:
        return False, {"error": f"Report generation failed: {str(e)}"}


# ---------------------------------------------------------
# Sidebar — Control Center & Repository Ingestion
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-wrapper">
            <div class="sidebar-logo">◈ NEURALFORGE AI</div>
            <div class="sidebar-sub">Turn messy ML repositories into auditable projects.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### Target Repository")
    target_repo = st.text_input(
        "Target Repository Path",
        value=st.session_state.repo_path,
        label_visibility="collapsed",
        help="Path to repository on local filesystem",
    )
    st.session_state.repo_path = target_repo

    # Presets Row
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Sample Repo", use_container_width=True):
            st.session_state.repo_path = "data/sample_repo"
            st.rerun()
    with col_p2:
        if st.button("Root Project", use_container_width=True):
            st.session_state.repo_path = "."
            st.rerun()

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Primary Action: Index / Analyze Repository
    if st.button("Analyze Repository", use_container_width=True, type="primary"):
        if not target_repo.strip():
            st.error("Specify a valid repository path.")
        else:
            with st.spinner("Extracting AST chunks & indexing embeddings..."):
                # 1. Index Repo
                success_idx, idx_data = api_upload_repo(target_repo)
                if success_idx and "session_id" in idx_data:
                    st.session_state.session_id = idx_data["session_id"]
                    st.session_state.chunks_found = idx_data.get("chunks_found", 0)

                    # 2. Run Static Audit
                    success_audit, audit_data = api_analyze_repo(target_repo)
                    if success_audit:
                        st.session_state.audit_report = audit_data

                    # 3. Generate Report
                    success_rep, rep_data = api_get_report(target_repo)
                    if success_rep:
                        st.session_state.markdown_report = rep_data.get("report", "")

                    st.success(f"Analysis complete: {idx_data.get('chunks_found', 0)} AST chunks indexed.")
                    st.rerun()
                else:
                    st.error(idx_data.get("error", "Failed to index repository."))

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Session Status & Telemetry
    st.markdown("##### Session Telemetry")
    is_connected, _ = check_backend_health()

    st.markdown(
        f"""
        <div style="font-size: 0.8rem; color: #888a93; line-height: 1.7;">
            <div>Backend Engine: <span style="color: {'#4ade80' if is_connected else '#f87171'}; font-weight: 600;">{'ONLINE (8000)' if is_connected else 'OFFLINE'}</span></div>
            <div>Indexed Target: <span style="color: #ffffff; font-weight: 500;">{st.session_state.session_id or 'None'}</span></div>
            <div>AST Chunks: <span style="color: #ffffff; font-weight: 500;">{st.session_state.chunks_found}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="header-container">
        <div>
            <div class="brand-title">◈ NEURALFORGE AI</div>
            <div class="brand-tag">Repository Intelligence & ML Code Auditing</div>
        </div>
        <div>
            {f'<div class="status-pill-online"><span class="status-dot-solid"></span> Engine Online</div>' if is_connected else f'<div class="status-pill-offline"><span class="status-dot-ring"></span> Engine Offline</div>'}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_connected:
    st.markdown(
        f"""
        <div class="mono-banner">
            <strong>Engine Offline:</strong> Backend API is unreachable at <code>{API_BASE_URL}</code>.<br>
            Start the server via <code>uvicorn backend.main:app --port 8000</code> in your terminal.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Main Product Navigation (5 Unified Workflow Stages)
# ---------------------------------------------------------
tab_overview, tab_copilot, tab_audit, tab_report, tab_inspector = st.tabs(
    [
        "01 Overview",
        "02 Copilot",
        "03 ML Audit",
        "04 Full Report",
        "05 Architecture",
    ]
)


# ---------------------------------------------------------
# TAB 1: Overview / Repository Intelligence
# ---------------------------------------------------------
with tab_overview:
    st.markdown('<div class="section-headline">Repository Health & Executive Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">High-level executive evaluation of ML engineering hygiene, data leakage safeguards, and pipeline validation.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.audit_report is None:
        st.markdown(
            f"""
            <div class="mono-banner">
                <strong>Repository Loaded:</strong> <code>{st.session_state.repo_path}</code><br>
                Click <strong>Analyze Repository</strong> in the sidebar to extract AST chunks, run static ML hygiene audits, and index the vector database.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        report = st.session_state.audit_report
        score = report.get("overall_score", 0)
        total_issues = report.get("total_issues", 0)
        leakage = report.get("data_leakage_issues", [])
        overfitting = report.get("overfitting_risk_issues", [])
        hyperparams = report.get("hyperparameter_issues", [])

        status_text = "Clean Baseline · Adheres to core ML engineering standards" if score >= 80 else ("Review Recommended · Moderate pipeline vulnerabilities found" if score >= 50 else "Critical Risk · Severe data leakage or unvalidated models")

        # Large Apple-style Score Hero
        st.markdown(
            f"""
            <div class="score-hero-container">
                <div class="score-display-wrapper">
                    <span class="score-huge-num">{score}</span>
                    <span class="score-total-denom">/ 100</span>
                </div>
                <div class="score-status-text">{status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Sub-score Metrics Strip
        st.markdown(
            f"""
            <div class="subscore-grid">
                <div class="subscore-card">
                    <div class="subscore-val">{100 - (len(leakage) * 10)}</div>
                    <div class="subscore-label">ML Preprocessing & Leakage</div>
                </div>
                <div class="subscore-card">
                    <div class="subscore-val">{100 - (len(overfitting) * 10)}</div>
                    <div class="subscore-label">Validation & Overfitting</div>
                </div>
                <div class="subscore-card">
                    <div class="subscore-val">{100 - (len(hyperparams) * 10)}</div>
                    <div class="subscore-label">Hyperparameter Bounding</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Overview Summary Findings
        st.markdown("##### At-a-Glance Diagnostic Summary")
        if total_issues == 0:
            st.markdown('<div class="mono-banner">No vulnerabilities detected. AST structure follows recommended best practices.</div>', unsafe_allow_html=True)
        else:
            for item in leakage:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')} {f'· Line {item.get("line")}' if item.get("line") else ''}</span>
                            <span class="badge-high">High · Data Leakage</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            for item in overfitting:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')}</span>
                            <span class="badge-med">Medium · Validation Gap</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            for item in hyperparams:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')}</span>
                            <span class="badge-med">Medium · Hyperparameter</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------
# TAB 2: Copilot Q&A (RAG Assistant)
# ---------------------------------------------------------
with tab_copilot:
    st.markdown('<div class="section-headline">Repository Copilot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Ask technical questions about model pipelines, preprocessing, architecture, or algorithmic components. Responses are strictly grounded in retrieved AST chunks.</div>',
        unsafe_allow_html=True,
    )

    # Prompt Suggestion Chips (Dispatches to pending_query)
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    with col_q1:
        if st.button("Model Architectures", key="btn_q_arch", use_container_width=True):
            st.session_state.pending_query = "What machine learning models or algorithms are implemented in this repository?"
            st.rerun()
    with col_q2:
        if st.button("Data Leakage Audit", key="btn_q_leak", use_container_width=True):
            st.session_state.pending_query = "Is there any data leakage or preprocessing issues in the training pipeline?"
            st.rerun()
    with col_q3:
        if st.button("Search & Sorting", key="btn_q_sort", use_container_width=True):
            st.session_state.pending_query = "Explain how search and sorting functions work in this codebase."
            st.rerun()
    with col_q4:
        if st.button("Hyperparameter Risks", key="btn_q_hyper", use_container_width=True):
            st.session_state.pending_query = "Are there any tree models with unbounded depth or risky hyperparameters?"
            st.rerun()

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Process Incoming Pending Query (Single Pipeline Step)
    if st.session_state.pending_query:
        active_query = st.session_state.pending_query
        st.session_state.pending_query = None  # Consume query immediately

        if not st.session_state.session_id:
            st.session_state.chat_history.append({"role": "user", "content": active_query})
            st.session_state.chat_history.append({"role": "assistant", "content": "Please index a repository first using the **Analyze Repository** button in the sidebar."})
        else:
            st.session_state.chat_history.append({"role": "user", "content": active_query})
            with st.spinner("Retrieving AST chunks & generating grounded response..."):
                success, res = api_ask_question(st.session_state.session_id, active_query)
                if success and "answer" in res:
                    st.session_state.chat_history.append({"role": "assistant", "content": res["answer"]})
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": res.get("error", "Error connecting to LLM service.")})
        st.rerun()

    # Render Chat History (Single Loop — Guaranteed Zero Duplicates)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-bubble-user">
                    <span class="chat-role-tag">Query</span>
                    <p>{msg['content']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # Chat Input Box
    user_chat_input = st.chat_input("Ask a question about the repository...")
    if user_chat_input:
        st.session_state.pending_query = user_chat_input
        st.rerun()

    # Clear Conversation Action
    if st.session_state.chat_history:
        st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
        if st.button("Clear Conversation", key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()


# ---------------------------------------------------------
# TAB 3: ML Audit / Health Dashboard
# ---------------------------------------------------------
with tab_audit:
    st.markdown('<div class="section-headline">ML Engineering Diagnostics & Audit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Deep-dive AST-level inspection evaluating preprocessing leakage, validation coverage, and hyperparameter bounding with actionable remediation steps.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.audit_report is None:
        st.markdown('<div class="mono-banner">Run an ML Health Audit from the sidebar to inspect this repository.</div>', unsafe_allow_html=True)
        if st.button("Run Audit Now", type="primary", key="audit_run_now_btn"):
            with st.spinner("Executing static AST inspection..."):
                success, audit_data = api_analyze_repo(st.session_state.repo_path)
                if success:
                    st.session_state.audit_report = audit_data
                    st.rerun()
                else:
                    st.error("Audit execution failed.")
    else:
        report = st.session_state.audit_report
        total_issues = report.get("total_issues", 0)
        leakage = report.get("data_leakage_issues", [])
        overfitting = report.get("overfitting_risk_issues", [])
        hyperparams = report.get("hyperparameter_issues", [])

        if total_issues == 0:
            st.markdown('<div class="mono-banner">No issues flagged across all rules. Clean ML codebase.</div>', unsafe_allow_html=True)
        else:
            st.markdown("##### Detailed Vulnerabilities & Remediation")

            # Data Leakage Findings
            for item in leakage:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')} {f'· Line {item.get("line")}' if item.get("line") else ''}</span>
                            <span class="badge-high">High · Data Leakage</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                        <div class="issue-remedy-box"><strong>Remediation:</strong> {item.get('suggestion')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Validation Gaps
            for item in overfitting:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')}</span>
                            <span class="badge-med">Medium · Validation Gap</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                        <div class="issue-remedy-box"><strong>Remediation:</strong> {item.get('suggestion')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Hyperparameter Risks
            for item in hyperparams:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')}</span>
                            <span class="badge-med">Medium · Hyperparameter Risk</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                        <div class="issue-remedy-box"><strong>Remediation:</strong> {item.get('suggestion')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------
# TAB 4: Full ML Report
# ---------------------------------------------------------
with tab_report:
    st.markdown('<div class="section-headline">Publication-Grade ML Project Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Comprehensive engineering report documenting repository architecture, structural findings, and remediation steps.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.markdown_report:
        st.markdown('<div class="mono-banner">Generate the ML Health Report to view the document.</div>', unsafe_allow_html=True)
        if st.button("Generate Report", type="primary", key="gen_rep_btn_tab4"):
            with st.spinner("Compiling report..."):
                success, rep_data = api_get_report(st.session_state.repo_path)
                if success:
                    st.session_state.markdown_report = rep_data.get("report", "")
                    st.rerun()
                else:
                    st.error("Report generation failed.")
    else:
        col_r1, col_r2 = st.columns([1, 4])
        with col_r1:
            st.download_button(
                label="Export Markdown (.md)",
                data=st.session_state.markdown_report,
                file_name="ml_project_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_r2:
            if st.button("Regenerate Report", key="regen_rep_btn_tab4"):
                with st.spinner("Regenerating..."):
                    success, rep_data = api_get_report(st.session_state.repo_path)
                    if success:
                        st.session_state.markdown_report = rep_data.get("report", "")
                        st.rerun()

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.markdown_report)


# ---------------------------------------------------------
# TAB 5: Repo Inspector & System Architecture
# ---------------------------------------------------------
with tab_inspector:
    st.markdown('<div class="section-headline">Repository Inspector & System Architecture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Technical details on AST parser rules, FAISS vector indexing, and pipeline contracts.</div>',
        unsafe_allow_html=True,
    )

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("##### Execution Pipeline")
        st.code(
            """
1. Repository Parsing  -> Ignores .git, venv, node_modules
2. AST Code Chunking   -> Preserves Function & Class block boundaries
3. Dense Vectorization -> sentence-transformers/all-MiniLM-L6-v2 (384d)
4. FAISS Indexing      -> In-memory cosine/L2 similarity index
5. Contextual Query    -> Top-k chunk retrieval + Groq LLM (gpt-oss-20b)
            """,
            language="text",
        )

    with col_i2:
        st.markdown("##### Endpoint Status & Session Verification")
        st.markdown(
            f"""
            - **Target Path**: `{st.session_state.repo_path}`
            - **Active Session ID**: `{st.session_state.session_id or 'None'}`
            - **Indexed Chunks**: `{st.session_state.chunks_found}`
            - **Backend Status**: `{'Connected' if is_connected else 'Offline'}`
            """
        )
