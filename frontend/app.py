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
# Strictly Monochrome Minimalist Design (Inter + Grayscale Only)
# Confident Apple-scale typography hierarchy and smooth transitions
# ---------------------------------------------------------
RAW_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

@font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 300 900;
    font-display: swap;
    src: url('https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2') format('woff2');
    unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

/* Universal Typography Reset */
*, *::before, *::after,
html, body, div, span, applet, object, iframe,
h1, h2, h3, h4, h5, h6, p, blockquote, pre,
a, abbr, acronym, address, big, cite, code,
del, dfn, em, img, ins, kbd, q, s, samp,
small, strike, strong, sub, sup, tt, var,
b, u, i, center, dl, dt, dd, ol, ul, li,
fieldset, form, label, legend, table, caption,
tbody, tfoot, thead, tr, th, td, article, aside,
canvas, details, embed, figure, figcaption, footer,
header, hgroup, menu, nav, output, ruby, section,
summary, time, mark, audio, video, input, textarea,
button, select, option,
.stApp, [class*="css"], [class*="st-"], [data-testid],
.stMarkdown, .stText, [data-baseweb], .stButton, .stTextInput,
.stSelectbox, .stTabs, [role="tab"], [data-testid="stSidebar"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

code, pre, .mono-code {
    font-family: 'Inter', monospace !important;
    font-feature-settings: "tnum" 1;
}

/* Canvas Base */
.stApp {
    background-color: #090a0d;
    color: #f4f4f6;
}

/* Header Container — Confident Scale & Generous Whitespace */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 2.25rem 0 1.75rem 0;
    margin-bottom: 2.25rem;
    border-bottom: 1px solid #22242b;
}

.brand-title {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: #ffffff !important;
    line-height: 1.1 !important;
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 0;
}

.brand-tag {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 400 !important;
    color: #888a93 !important;
    letter-spacing: -0.015em !important;
    margin-top: 0.5rem !important;
    line-height: 1.4 !important;
}

/* Monochrome Status Pill */
.status-pill-online {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.78rem;
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
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid #2c2e35;
    background: #101114;
    color: #888a93;
}

.status-dot-solid {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #ffffff;
}

.status-dot-ring {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    border: 1px solid #888a93;
    background-color: transparent;
}

/* Tab Navigation Styling — Explicit Inter & Confident Hierarchy */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background-color: transparent;
    padding: 0 0 0.65rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2rem;
}

.stTabs button[data-baseweb="tab"],
.stTabs button[data-testid="stTab"],
div[data-baseweb="tab-list"] button {
    height: auto !important;
    padding: 0.5rem 0 !important;
    background-color: transparent !important;
    border: none !important;
    transition: color 0.18s ease, border-color 0.18s ease, opacity 0.18s ease !important;
}

.stTabs button[data-baseweb="tab"] p,
.stTabs button[data-testid="stTab"] p,
div[data-baseweb="tab-list"] button p {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 0.98rem !important;
    letter-spacing: -0.015em !important;
    margin: 0 !important;
    transition: color 0.18s ease !important;
}

/* Inactive Tabs */
.stTabs button[data-baseweb="tab"][aria-selected="false"],
.stTabs button[data-baseweb="tab"][aria-selected="false"] p,
.stTabs button[data-testid="stTab"][aria-selected="false"],
.stTabs button[data-testid="stTab"][aria-selected="false"] p {
    color: #71717a !important;
    font-weight: 500 !important;
}

.stTabs button[data-baseweb="tab"][aria-selected="false"]:hover,
.stTabs button[data-baseweb="tab"][aria-selected="false"]:hover p,
.stTabs button[data-testid="stTab"][aria-selected="false"]:hover,
.stTabs button[data-testid="stTab"][aria-selected="false"]:hover p {
    color: #d4d4d8 !important;
}

/* Active Tab */
.stTabs button[data-baseweb="tab"][aria-selected="true"],
.stTabs button[data-baseweb="tab"][aria-selected="true"] p,
.stTabs button[data-testid="stTab"][aria-selected="true"],
.stTabs button[data-testid="stTab"][aria-selected="true"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

.stTabs [aria-selected="true"] {
    border-bottom: 2px solid #ffffff !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* Section Headings */
.section-headline {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #ffffff !important;
    margin-bottom: 0.35rem !important;
}

.section-description {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 0.92rem !important;
    color: #888a93 !important;
    margin-bottom: 1.75rem !important;
    line-height: 1.6 !important;
}

/* Editorial Score Hero */
.score-hero-container {
    padding: 2.5rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2rem;
}

.score-display-wrapper {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
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
    color: #6e7079;
    letter-spacing: -0.02em;
}

.score-status-text {
    font-size: 1.05rem;
    font-weight: 500;
    color: #b0b2ba;
    margin-top: 0.65rem;
    letter-spacing: -0.015em;
}

/* Metric Summary Strip */
.metric-strip-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    padding: 1.5rem 0;
    border-bottom: 1px solid #22242b;
    margin-bottom: 2.25rem;
}

.metric-strip-item {
    display: flex;
    flex-direction: column;
}

.metric-strip-count {
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: #ffffff;
}

.metric-strip-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #888a93;
    margin-top: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Issue Findings */
.issue-row {
    padding: 1.5rem 0;
    border-bottom: 1px solid #1c1d22;
    transition: background 0.18s ease;
}

.issue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.issue-file-loc {
    font-size: 0.92rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.015em;
}

.badge-mono-high {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ffffff;
    background: #1e2026;
    border: 1px solid #4a4d58;
    padding: 0.22rem 0.6rem;
    border-radius: 4px;
}

.badge-mono-med {
    font-size: 0.72rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #b0b2ba;
    background: #14151a;
    border: 1px dashed #34363e;
    padding: 0.22rem 0.6rem;
    border-radius: 4px;
}

.issue-title-text {
    font-size: 0.94rem;
    font-weight: 400;
    color: #d4d4d8;
    line-height: 1.55;
    margin-bottom: 0.5rem;
}

.issue-remedy-box {
    font-size: 0.86rem;
    font-weight: 400;
    color: #a1a1aa;
    background: #111216;
    border-left: 2px solid #52525b;
    padding: 0.6rem 0.95rem;
    margin-top: 0.45rem;
    border-radius: 0 4px 4px 0;
    line-height: 1.55;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #060709;
    border-right: 1px solid #1c1d22;
}

/* Buttons — Smooth Subtle Transitions */
.stButton button {
    border-radius: 6px;
    font-size: 0.88rem;
    font-weight: 500;
    letter-spacing: -0.01em;
    transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
    border: 1px solid #2c2e35;
    background: #14151a;
    color: #e4e4e7;
}

.stButton button:hover {
    background: #20222a;
    border-color: #4a4d58;
    color: #ffffff;
}

.stButton button[kind="primary"] {
    background: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    font-weight: 600;
}

.stButton button[kind="primary"]:hover {
    background: #e4e4e7;
    color: #000000;
    border-color: #e4e4e7;
}

/* Chat Messages */
.chat-bubble-user {
    background: #14151a;
    border: 1px solid #272830;
    padding: 1rem 1.25rem;
    border-radius: 6px;
    margin-bottom: 1.25rem;
    font-size: 0.94rem;
    color: #f4f4f6;
    line-height: 1.6;
}

.chat-bubble-ai {
    background: transparent;
    padding: 1rem 0.2rem;
    margin-bottom: 1.75rem;
    font-size: 0.94rem;
    color: #d4d4d8;
    line-height: 1.68;
    border-bottom: 1px solid #1c1d22;
}

.mono-banner {
    padding: 1rem 1.25rem;
    background: #111216;
    border: 1px solid #272830;
    border-radius: 6px;
    font-size: 0.88rem;
    color: #a1a1aa;
    margin-bottom: 1.5rem;
    line-height: 1.55;
}
</style>
"""

# Inject CSS cleanly via st.html (or st.markdown as fallback)
if hasattr(st, "html"):
    st.html(RAW_CSS)
else:
    st.markdown(RAW_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# State Initialization
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chunks_found" not in st.session_state:
    st.session_state.chunks_found = 0
if "repo_path" not in st.session_state:
    st.session_state.repo_path = "data/sample_repo"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "markdown_report" not in st.session_state:
    st.session_state.markdown_report = None


# ---------------------------------------------------------
# API Helper Functions (Exact Contracts Preserved)
# ---------------------------------------------------------
def check_backend_health():
    """Pings backend root endpoint to check connectivity."""
    try:
        res = requests.get(f"{API_BASE_URL}/", timeout=2)
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
            timeout=30,
        )
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"error": f"Failed to connect to backend: {str(e)}"}


def api_ask_question(session_id: str, question: str):
    """Calls POST /ask endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/ask",
            json={"session_id": session_id, "question": question},
            timeout=60,
        )
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"error": f"Inquiry failed: {str(e)}"}


def api_analyze_repo(repo_path: str):
    """Calls POST /analyze endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/analyze",
            json={"repo_path": repo_path},
            timeout=30,
        )
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"error": f"Static ML analysis failed: {str(e)}"}


def api_get_report(repo_path: str):
    """Calls POST /report endpoint."""
    try:
        res = requests.post(
            f"{API_BASE_URL}/report",
            json={"repo_path": repo_path},
            timeout=30,
        )
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, {"error": f"Report generation failed: {str(e)}"}


# ---------------------------------------------------------
# Minimalist Sidebar — Control & Repository Indexing
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### NeuralForge")
    st.caption("Repository Ingestion & Controls")
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Repository Path Input
    target_repo = st.text_input(
        "Repository Path",
        value=st.session_state.repo_path,
        help="Local filesystem path to target repository",
    )
    st.session_state.repo_path = target_repo

    # Presets
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Sample Repo", use_container_width=True):
            st.session_state.repo_path = "data/sample_repo"
            st.rerun()
    with col_p2:
        if st.button("Root Project", use_container_width=True):
            st.session_state.repo_path = "."
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Ingestion Actions
    if st.button("Index Repository", use_container_width=True, type="primary"):
        if not target_repo.strip():
            st.error("Specify a valid path.")
        else:
            with st.spinner("Extracting AST chunks & indexing in FAISS..."):
                success, data = api_upload_repo(target_repo)
                if success and "session_id" in data:
                    st.session_state.session_id = data["session_id"]
                    st.session_state.chunks_found = data.get("chunks_found", 0)
                    st.success(f"Indexed {data.get('chunks_found', 0)} chunks.")
                else:
                    st.error(data.get("error", "Indexing error"))

    if st.button("Run Health Audit", use_container_width=True):
        if not target_repo.strip():
            st.error("Specify a valid path.")
        else:
            with st.spinner("Executing static ML audits..."):
                success_audit, audit_data = api_analyze_repo(target_repo)
                if success_audit:
                    st.session_state.audit_report = audit_data
                else:
                    st.error(audit_data.get("error", "Audit failed"))

                success_rep, rep_data = api_get_report(target_repo)
                if success_rep:
                    st.session_state.markdown_report = rep_data.get("report", "")

                if success_audit:
                    st.success("Audit complete.")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Telemetry Summary
    st.markdown("##### Session Telemetry")
    if st.session_state.session_id:
        st.markdown(
            f"""
            <div style="font-size: 0.8rem; color: #888a93; line-height: 1.6;">
                <div>Active Target: <span style="color: #ffffff; font-weight: 500;">{st.session_state.session_id}</span></div>
                <div>AST Chunks: <span style="color: #ffffff; font-weight: 500;">{st.session_state.chunks_found}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("No repository indexed in this session.")


# ---------------------------------------------------------
# Top Navigation Bar — Confident Headline & Minimalist Status
# ---------------------------------------------------------
is_connected, _ = check_backend_health()

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
            Execute <code>uvicorn backend.main:app --port 8000</code> in your terminal.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------
tab_chat, tab_audit, tab_report, tab_inspector = st.tabs(
    [
        "Copilot Q&A",
        "ML Health Dashboard",
        "Full ML Report",
        "Repo Inspector",
    ]
)

# ---------------------------------------------------------
# TAB 1: Copilot Q&A (RAG Assistant)
# ---------------------------------------------------------
with tab_chat:
    st.markdown('<div class="section-headline">Repository Copilot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Ask technical questions about model pipelines, preprocessing, architecture, or algorithmic components. Responses are strictly grounded in retrieved AST chunks.</div>',
        unsafe_allow_html=True,
    )

    # Prompt Suggestion Strip
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    quick_query = None
    with col_q1:
        if st.button("Model Architectures", use_container_width=True):
            quick_query = "What machine learning models or algorithms are implemented in this repository?"
    with col_q2:
        if st.button("Data Leakage Audit", use_container_width=True):
            quick_query = "Is there any data leakage or preprocessing issues in the training pipeline?"
    with col_q3:
        if st.button("Search & Sorting", use_container_width=True):
            quick_query = "Explain how search and sorting functions work in this codebase."
    with col_q4:
        if st.button("Hyperparameter Risks", use_container_width=True):
            quick_query = "Are there any tree models with unbounded depth or risky hyperparameters?"

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Chat Feed
    for msg_item in st.session_state.chat_history:
        if msg_item["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user"><strong>Query</strong><br>{msg_item["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg_item["content"])

    # Chat Input Box
    user_input = st.chat_input("Ask a question about the repository...")
    query_to_send = quick_query or user_input

    if query_to_send:
        if not st.session_state.session_id:
            st.markdown('<div class="mono-banner">Index a repository first in the sidebar before initiating queries.</div>', unsafe_allow_html=True)
        else:
            st.session_state.chat_history.append({"role": "user", "content": query_to_send})
            st.markdown(f'<div class="chat-bubble-user"><strong>Query</strong><br>{query_to_send}</div>', unsafe_allow_html=True)

            with st.chat_message("assistant"):
                with st.spinner("Retrieving code context & generating response..."):
                    success, res = api_ask_question(st.session_state.session_id, query_to_send)
                    if success and "answer" in res:
                        answer_text = res["answer"]
                        st.markdown(answer_text)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer_text})
                    else:
                        err_msg = res.get("error", "Error generating response.")
                        st.markdown(f'<div class="mono-banner">{err_msg}</div>', unsafe_allow_html=True)
                        st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

    if st.session_state.chat_history:
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Clear Conversation", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()


# ---------------------------------------------------------
# TAB 2: ML Health Dashboard (Phase 2 Intelligence)
# ---------------------------------------------------------
with tab_audit:
    st.markdown('<div class="section-headline">ML Engineering Health & Diagnostics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Automated static inspection evaluating data leakage prevention, test validation coverage, and hyperparameter bounding.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.audit_report is None:
        st.markdown('<div class="mono-banner">Run an ML Health Audit from the sidebar to inspect this repository.</div>', unsafe_allow_html=True)
        if st.button("Run Audit Now", type="primary"):
            with st.spinner("Analyzing repository..."):
                success, audit_data = api_analyze_repo(st.session_state.repo_path)
                if success:
                    st.session_state.audit_report = audit_data
                    st.rerun()
                else:
                    st.error(audit_data.get("error", "Audit failed"))
    else:
        report = st.session_state.audit_report
        score = report.get("overall_score", 0)
        total_issues = report.get("total_issues", 0)
        leakage = report.get("data_leakage_issues", [])
        overfitting = report.get("overfitting_risk_issues", [])
        hyperparams = report.get("hyperparameter_issues", [])

        status_text = "Clean Baseline · Follows ML engineering best practices" if score >= 80 else ("Review Recommended · Moderate risks identified" if score >= 50 else "High Risk · Critical data leakage or unvalidated pipelines")

        # Large Editorial Score Hero
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

        # Minimal Metric Summary Strip
        st.markdown(
            f"""
            <div class="metric-strip-row">
                <div class="metric-strip-item">
                    <div class="metric-strip-count">{len(leakage)}</div>
                    <div class="metric-strip-label">Data Leakage Checks</div>
                </div>
                <div class="metric-strip-item">
                    <div class="metric-strip-count">{len(overfitting)}</div>
                    <div class="metric-strip-label">Validation Gaps</div>
                </div>
                <div class="metric-strip-item">
                    <div class="metric-strip-count">{len(hyperparams)}</div>
                    <div class="metric-strip-label">Hyperparameter Risks</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Diagnostic Findings List
        if total_issues == 0:
            st.markdown('<div class="mono-banner">No issues flagged. Clean implementation.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-headline" style="font-size: 1rem; margin-top: 1rem; text-transform: uppercase; letter-spacing: 0.04em;">Detailed Findings</div>', unsafe_allow_html=True)

            # Data Leakage
            for item in leakage:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')} {f'· Line {item.get("line")}' if item.get("line") else ''}</span>
                            <span class="badge-mono-high">High · Data Leakage</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                        <div class="issue-remedy-box"><strong>Remediation:</strong> {item.get('suggestion')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Overfitting Risks
            for item in overfitting:
                st.markdown(
                    f"""
                    <div class="issue-row">
                        <div class="issue-header">
                            <span class="issue-file-loc">{item.get('file')}</span>
                            <span class="badge-mono-med">Medium · Validation Gap</span>
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
                            <span class="badge-mono-med">Medium · Hyperparameter</span>
                        </div>
                        <div class="issue-title-text">{item.get('issue')}</div>
                        <div class="issue-remedy-box"><strong>Remediation:</strong> {item.get('suggestion')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------
# TAB 3: Full ML Project Report (Markdown)
# ---------------------------------------------------------
with tab_report:
    st.markdown('<div class="section-headline">ML Project Health Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-description">Publication-grade Markdown report documenting repository architecture, structural findings, and remediation steps.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.markdown_report:
        st.markdown('<div class="mono-banner">Generate the ML Health Report to view the document.</div>', unsafe_allow_html=True)
        if st.button("Generate Report", type="primary", key="gen_rep_btn"):
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
            if st.button("Regenerate", key="regen_rep_btn"):
                with st.spinner("Regenerating..."):
                    success, rep_data = api_get_report(st.session_state.repo_path)
                    if success:
                        st.session_state.markdown_report = rep_data.get("report", "")
                        st.rerun()

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.markdown_report)


# ---------------------------------------------------------
# TAB 4: Repo Inspector & Telemetry
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
