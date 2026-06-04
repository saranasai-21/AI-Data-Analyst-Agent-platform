import html
import hashlib
import os
import shutil
import tempfile

# Set BROWSER_PATH for Kaleido/Plotly static image export on headless environments (like Hugging Face Spaces)
if "BROWSER_PATH" not in os.environ:
    for browser_bin in ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]:
        browser_path = shutil.which(browser_bin)
        if browser_path:
            os.environ["BROWSER_PATH"] = browser_path
            break
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from agents.data_quality_agent import DataQualityAgent
from agents.profiling_agent import ProfilingAgent
from core.data_loader import DataLoader
from core.state_manager import StateManager
try:
    from orchestrator.graph import invoke_fast_workflow
except ImportError:
    from orchestrator.graph import graph

    def invoke_fast_workflow(state):
        return graph.invoke(state)
from services.presentation_service import PresentationService


st.set_page_config(
    page_title="AI Data Analyst",
    page_icon=":bar_chart:",
    layout="wide",
)

os.makedirs("outputs", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

StateManager.initialize()

SESSION_DEFAULTS = {
    "latest_result": None,
    "selected_chart_keys": [],
    "report_path": None,
    "chart_export_warning": False,
    "chart_cache_key": None,
    "chart_cache": [],
    "analysis_cache": {},
}

for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


INK = "#f3f4f6"
MUTED = "#9ca3af"
PANEL = "#111827"
CANVAS = "#080c14"
BORDER = "#1f2937"
BLUE = "#6366f1"
TEAL = "#06b6d4"
AMBER = "#f59e0b"
GREEN = "#10b981"
RED = "#ef4444"
VIOLET = "#8b5cf6"
SHELL_BG = "linear-gradient(135deg, #1e1b4b 0%, #080c14 100%)"
SHELL_BORDER = "rgba(99, 102, 241, 0.25)"
SHELL_SHADOW = "rgba(0, 0, 0, 0.5)"
GLASS_BG = "rgba(30, 41, 59, 0.45)"
GLASS_SHADOW = "rgba(0, 0, 0, 0.2)"
FILE_DROP_BG = "rgba(17, 24, 39, 0.6)"
CHAT_INPUT_BG = "rgba(8, 12, 20, 0.95)"
TEXTAREA_BG = "rgba(30, 41, 59, 0.7)"
PLOTLY_TEMPLATE = "plotly_dark"
CODE_BG = "#0d1117"
CODE_COLOR = "#e6edf3"
SHADOW = "0 8px 30px rgba(0, 0, 0, 0.3)"

CHART_COLORS = [BLUE, TEAL, AMBER, GREEN, RED, VIOLET, "#0891b2", "#c2410c"]


@dataclass
class ChartSpec:
    key: str
    title: str
    caption: str
    group: str
    priority: int
    fig: Any
    path: str | None = None


st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --ink: {INK};
        --muted: {MUTED};
        --panel: {PANEL};
        --canvas: {CANVAS};
        --border: {BORDER};
        --blue: {BLUE};
        --teal: {TEAL};
        --amber: {AMBER};
        --green: {GREEN};
        --red: {RED};
        --code-bg: {CODE_BG};
        --code-color: {CODE_COLOR};
        --shadow: {SHADOW};
    }}

    .stApp {{
        background: var(--canvas);
        color: var(--ink);
    }}

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {{
        display: none;
    }}

    .block-container {{
        max-width: 1340px;
        padding: 1.15rem 1.25rem 5.5rem;
    }}

    h1, h2, h3, h4, h5, h6, p, label, span {{
        color: var(--ink);
        font-family: "Plus Jakarta Sans", "Inter", -apple-system, sans-serif;
        letter-spacing: 0;
    }}

    .app-shell {{
        background: {SHELL_BG};
        border: 1px solid {SHELL_BORDER};
        border-radius: 12px;
        padding: 1.5rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 40px {SHELL_SHADOW}, inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }}

    .app-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
    }}

    .app-title {{
        min-width: 260px;
        flex: 1;
    }}

    .eyebrow {{
        margin: 0 0 0.3rem;
        color: var(--teal);
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .app-title h1 {{
        margin: 0;
        color: var(--ink);
        font-size: clamp(2rem, 4vw, 3.35rem);
        line-height: 1;
        font-weight: 850;
    }}

    .app-title p {{
        margin: 0.55rem 0 0;
        color: var(--muted);
        font-size: 1rem;
        max-width: 720px;
    }}

    .header-stack {{
        display: grid;
        grid-template-columns: repeat(2, minmax(128px, 1fr));
        gap: 0.6rem;
        min-width: min(100%, 320px);
    }}

    .header-chip,
    .metric-tile,
    .status-tile {{
        border: 1px solid var(--border);
        border-radius: 12px;
        background: {GLASS_BG};
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px 0 {GLASS_SHADOW};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .header-chip:hover,
    .metric-tile:hover,
    .status-tile:hover {{
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.1);
    }}

    .header-chip {{
        padding: 0.75rem 0.8rem;
    }}

    .header-chip span,
    .metric-tile span,
    .status-tile span {{
        display: block;
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }}

    .header-chip strong {{
        display: block;
        margin-top: 0.25rem;
        color: var(--ink);
        font-size: 0.98rem;
        overflow-wrap: anywhere;
    }}

    .metric-tile {{
        min-height: 114px;
        padding: 0.95rem;
        border-top: 4px solid var(--blue);
    }}

    .metric-tile strong {{
        display: block;
        margin-top: 0.35rem;
        color: var(--ink);
        font-size: clamp(1.55rem, 2.4vw, 2.35rem);
        line-height: 1.05;
        font-weight: 850;
        overflow-wrap: anywhere;
    }}

    .metric-tile small {{
        display: block;
        margin-top: 0.45rem;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.35;
    }}

    .tone-teal {{ border-top-color: var(--teal); }}
    .tone-amber {{ border-top-color: var(--amber); }}
    .tone-green {{ border-top-color: var(--green); }}
    .tone-red {{ border-top-color: var(--red); }}
    .tone-violet {{ border-top-color: #6d4aff; }}

    .status-tile {{
        padding: 0.9rem;
        min-height: 102px;
    }}

    .status-tile strong {{
        display: block;
        margin-top: 0.35rem;
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--ink);
    }}

    .status-tile small {{
        display: block;
        margin-top: 0.35rem;
        color: var(--muted);
        font-size: 0.84rem;
        line-height: 1.35;
    }}

    .section-label {{
        margin: 0.3rem 0 0.8rem;
        color: var(--ink);
        font-size: 1.08rem;
        font-weight: 800;
    }}

    .chart-copy {{
        margin: 0.2rem 0 0.45rem;
    }}

    .chart-copy h3 {{
        margin: 0;
        color: var(--ink);
        font-size: 1.05rem;
        line-height: 1.25;
        font-weight: 800;
    }}

    .chart-copy p {{
        margin: 0.25rem 0 0;
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.42;
    }}

    .empty-note {{
        background: rgba(99, 102, 241, 0.05) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        color: var(--muted) !important;
        line-height: 1.5 !important;
    }}

    [data-testid="stTabs"] [role="tablist"] {{
        gap: 0.5rem;
        border-bottom: 1px solid var(--border) !important;
        padding: 0.2rem 0;
    }}

    [data-testid="stTabs"] [role="tab"] {{
        border-radius: 8px !important;
        color: var(--muted) !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.1rem !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
    }}

    [data-testid="stTabs"] [role="tab"]:hover {{
        color: var(--blue) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }}

    [data-testid="stTabs"] [aria-selected="true"] {{
        background: rgba(99, 102, 241, 0.1) !important;
        color: var(--blue) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }}

    [data-testid="stMetric"],
    [data-testid="stDataFrame"],
    [data-testid="stImage"],
    [data-testid="stExpander"],
    [data-testid="stAlert"],
    [data-testid="stChatMessage"],
    [data-baseweb="select"],
    .stTextArea textarea {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow) !important;
    }}

    [data-testid="stFileUploader"] {{
        padding: 1.25rem;
        background: rgba(30, 41, 59, 0.3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important;
        background: {FILE_DROP_BG} !important;
        color: var(--ink) !important;
        padding: 1.5rem 1rem !important;
        transition: all 0.25s ease !important;
    }}

    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--blue) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }}

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] small {{
        color: var(--muted) !important;
    }}

    [data-testid="stFileUploaderDropzone"] div {{
        color: var(--ink) !important;
    }}

    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {{
        background: linear-gradient(135deg, var(--blue) 0%, #4f46e5 100%) !important;
        border: 1px solid var(--blue) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2) !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s ease !important;
    }}

    [data-testid="stFileUploaderDropzone"] button:hover,
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]:hover {{
        background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%) !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 6px 12px rgba(139, 92, 246, 0.3) !important;
    }}

    [data-testid="stFileUploaderDropzone"] button *,
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] * {{
        color: white !important;
        fill: white !important;
        stroke: white !important;
    }}

    .stButton>button,
    .stDownloadButton>button {{
        border-radius: 10px;
        border: 1px solid var(--blue);
        background: linear-gradient(135deg, var(--blue) 0%, #4f46e5 100%);
        color: white !important;
        font-weight: 600;
        font-family: "Plus Jakarta Sans", sans-serif;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    .stButton>button:hover,
    .stDownloadButton>button:hover {{
        transform: translateY(-1px);
        border-color: #8b5cf6;
        background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%);
        color: white !important;
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
    }}

    .secondary-action button {{
        border-color: var(--border) !important;
        background: rgba(30, 41, 59, 0.6) !important;
        color: var(--ink) !important;
    }}

    [data-testid="stChatInput"] {{
        border-top: 1px solid var(--border) !important;
        background: {CHAT_INPUT_BG} !important;
    }}

    [data-testid="stChatInput"] textarea {{
        background: {TEXTAREA_BG} !important;
        color: var(--ink) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        caret-color: var(--blue) !important;
    }}

    .readable-output {{
        background: rgba(30, 41, 59, 0.3) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        color: var(--ink) !important;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        line-height: 1.6;
    }}

    pre, code {{
        background: var(--code-bg) !important;
        color: var(--code-color) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }}

    .stPlotlyChart {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        box-shadow: var(--shadow) !important;
    }}

    /* Table Styling for Markdown Outputs */
    table {{
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        background-color: var(--panel) !important;
        color: var(--ink) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
    }}
    th {{
        background-color: var(--blue) !important;
        color: white !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding: 0.65rem 0.95rem !important;
        border: 1px solid var(--border) !important;
    }}
    td {{
        padding: 0.55rem 0.95rem !important;
        border: 1px solid var(--border) !important;
        background-color: var(--panel) !important;
        color: var(--ink) !important;
    }}
    tr:nth-child(even) td {{
        background-color: var(--canvas) !important;
    }}

    /* Dropdown Portal Styling for Light/Dark Mode compatibility */
    div[data-baseweb="popover"] {{
        z-index: 9999999 !important;
    }}
    div[data-baseweb="popover"] ul {{
        background-color: var(--panel) !important;
        color: var(--ink) !important;
        border: 1px solid var(--border) !important;
    }}
    div[data-baseweb="popover"] li {{
        color: var(--ink) !important;
        background-color: transparent !important;
        transition: background-color 0.15s ease !important;
    }}
    div[data-baseweb="popover"] li:hover {{
        background-color: rgba(99, 102, 241, 0.12) !important;
        color: var(--blue) !important;
    }}

    /* Text overrides inside select elements */
    [data-baseweb="select"] * {{
        color: var(--ink) !important;
    }}
    /* Chips (multi-select tags) text contrast */
    div[data-baseweb="tag"] {{
        background-color: var(--blue) !important;
        color: white !important;
        border-radius: 6px !important;
    }}
    div[data-baseweb="tag"] * {{
        color: white !important;
        fill: white !important;
    }}


    hr {{
        border-color: var(--border);
    }}

    @media (max-width: 720px) {{
        .block-container {{
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}

        .header-stack {{
            grid-template-columns: 1fr;
        }}

        .metric-tile {{
            min-height: 96px;
        }}
    }}
</style>
""",
    unsafe_allow_html=True,
)


def escape(value):
    return html.escape(str(value))


def unique_columns(columns):
    seen = {}
    fixed = []

    for col in columns:
        name = str(col)
        count = seen.get(name, 0)
        fixed.append(name if count == 0 else f"{name}_{count + 1}")
        seen[name] = count + 1

    return fixed


def safe_filename(value):
    return "".join(
        ch if ch.isalnum() or ch in ("-", "_") else "_"
        for ch in str(value)
    ).strip("_") or "chart"


def format_number(value):
    try:
        number = float(value)
    except Exception:
        return str(value)

    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.1f}K"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}"


def dataframe_fingerprint(df, sample_size=400):
    hasher = hashlib.sha256()
    hasher.update(str(df.shape).encode("utf-8"))
    hasher.update("|".join(map(str, df.columns)).encode("utf-8"))
    hasher.update("|".join(map(str, df.dtypes)).encode("utf-8"))

    if df.empty:
        return hasher.hexdigest()

    sample = pd.concat(
        [
            df.head(sample_size // 2),
            df.tail(sample_size // 2),
        ],
        axis=0,
    )

    try:
        row_hashes = pd.util.hash_pandas_object(
            sample,
            index=True,
        ).values
        hasher.update(row_hashes.tobytes())
    except Exception:
        hasher.update(sample.to_csv(index=True).encode("utf-8", errors="ignore"))

    return hasher.hexdigest()


def compact_conversation(conversation, max_messages=6, max_chars=2200):
    trimmed = conversation[-max_messages:]
    compacted = []
    used = 0

    for item in reversed(trimmed):
        role = item.get("role", "assistant")
        content = str(item.get("content", "")).strip()

        if not content:
            continue

        remaining = max_chars - used
        if remaining <= 0:
            break

        if len(content) > remaining:
            content = content[:remaining]

        compacted.append(
            {
                "role": role,
                "content": content,
            }
        )
        used += len(content)

    return list(reversed(compacted))


def pct(part, total):
    if not total:
        return "0.0%"
    return f"{(part / total) * 100:.1f}%"


def uploaded_source(uploaded_file):
    ext = os.path.splitext(uploaded_file.name.lower())[1]

    if ext in (".db", ".sqlite", ".sqlite3"):
        return "SQLite"
    if ext == ".csv":
        return "CSV"
    if ext in (".xlsx", ".xls"):
        return "Excel"
    if ext == ".json":
        return "JSON"

    return "Unknown"


def working_dataframe(df):
    chart_df = df.copy()
    chart_df.columns = unique_columns(chart_df.columns)
    return chart_df


def reset_workspace():
    st.session_state.df = None
    st.session_state.file_name = None
    st.session_state.data_source = None
    st.session_state.conversation = []
    st.session_state.latest_result = None
    st.session_state.selected_chart_keys = []
    st.session_state.report_path = None
    st.session_state.chart_export_warning = False
    st.session_state.chart_cache_key = None
    st.session_state.chart_cache = []
    st.session_state.analysis_cache = {}


def render_header(df=None):
    file_name = StateManager.get_file_name() or "No dataset loaded"
    source = st.session_state.get("data_source") or "Local file"
    rows = format_number(df.shape[0]) if df is not None else "Ready"
    cols = format_number(df.shape[1]) if df is not None else "Waiting"
    subtitle = (
        f"{escape(file_name)} is active"
        if df is not None
        else "Start with a dataset file"
    )

    st.markdown(
        f"""
<div class="app-shell">
    <div class="app-header">
        <div class="app-title">
            <p class="eyebrow">AI analyst workspace</p>
            <h1>AI Data Analyst</h1>
            <p>{subtitle}</p>
        </div>
        <div class="header-stack">
            <div class="header-chip">
                <span>Source</span>
                <strong>{escape(source)}</strong>
            </div>
            <div class="header-chip">
                <span>Rows</span>
                <strong>{rows}</strong>
            </div>
            <div class="header-chip">
                <span>Columns</span>
                <strong>{cols}</strong>
            </div>
            <div class="header-chip">
                <span>Report</span>
                <strong>{'Available' if st.session_state.get('report_path') else 'Not built'}</strong>
            </div>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric(label, value, note="", tone="blue"):
    st.markdown(
        f"""
<div class="metric-tile tone-{tone}">
    <span>{escape(label)}</span>
    <strong>{escape(value)}</strong>
    <small>{escape(note)}</small>
</div>
""",
        unsafe_allow_html=True,
    )


def render_status(label, value, note=""):
    st.markdown(
        f"""
<div class="status-tile">
    <span>{escape(label)}</span>
    <strong>{escape(value)}</strong>
    <small>{escape(note)}</small>
</div>
""",
        unsafe_allow_html=True,
    )


def is_identifier_column(name, series):
    lower = str(name).lower()
    non_null = series.dropna()

    if non_null.empty:
        return False

    unique_ratio = non_null.nunique(dropna=True) / len(non_null)
    id_hint = any(
        token in lower
        for token in ("id", "uuid", "guid", "reference", "serial", "code")
    )

    if id_hint and (unique_ratio > 0.35 or non_null.nunique(dropna=True) > 30):
        return True

    if unique_ratio > 0.96 and len(non_null) > 25:
        return True

    if pd.api.types.is_numeric_dtype(series) and unique_ratio > 0.9:
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(numeric) > 25 and (numeric.is_monotonic_increasing or numeric.is_monotonic_decreasing):
            return True

    return False


def detect_time_columns(df):
    time_cols = []
    date_keywords = ("date", "time", "timestamp", "period", "month", "quarter", "year")

    for col in df.columns:
        series = df[col]
        lower = str(col).lower()
        non_null = series.dropna()

        if non_null.empty:
            continue

        if pd.api.types.is_datetime64_any_dtype(series):
            if non_null.nunique() > 1:
                time_cols.append((col, "datetime"))
            continue

        if pd.api.types.is_numeric_dtype(series):
            if any(token in lower for token in ("period", "month", "quarter", "year")):
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                if numeric.nunique() > 1 and not is_identifier_column(col, series):
                    time_cols.append((col, "numeric"))
            continue

        should_try = any(token in lower for token in date_keywords)
        parsed = pd.to_datetime(series, errors="coerce")
        valid_ratio = parsed.notna().mean()

        if (should_try and valid_ratio >= 0.4) or valid_ratio >= 0.8:
            if parsed.nunique(dropna=True) > 1:
                time_cols.append((col, "datetime"))

    return time_cols


def numeric_columns_ranked(df):
    numeric = df.select_dtypes(include="number")
    candidates = []
    metric_keywords = (
        "amount",
        "sales",
        "revenue",
        "income",
        "price",
        "cost",
        "profit",
        "value",
        "score",
        "rate",
        "balance",
        "payment",
        "quantity",
        "units",
        "data",
        "tenure",
    )

    for col in numeric.columns:
        series = pd.to_numeric(numeric[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        clean = series.dropna()

        if clean.empty or clean.nunique() <= 1:
            continue

        lower = str(col).lower()
        completeness = len(clean) / max(len(series), 1)
        unique_score = min(clean.nunique(), 100) / 100
        spread = clean.quantile(0.75) - clean.quantile(0.25)
        median = abs(clean.median()) or 1
        spread_score = min(abs(spread / median), 8) / 8
        skew_score = min(abs(clean.skew()) if len(clean) > 2 else 0, 3) / 3

        score = completeness + unique_score + spread_score + (0.35 * skew_score)

        if any(token in lower for token in metric_keywords):
            score += 0.8

        if any(token in lower for token in ("period", "month", "quarter", "year")):
            score -= 0.9

        if is_identifier_column(col, numeric[col]):
            score -= 3.0

        candidates.append((score, col))

    candidates = [item for item in candidates if item[0] > -0.2]
    return [col for _, col in sorted(candidates, reverse=True)]


def categorical_columns_ranked(df, time_cols):
    time_names = {col for col, _ in time_cols}
    candidates = []
    segment_keywords = (
        "category",
        "segment",
        "region",
        "country",
        "state",
        "city",
        "status",
        "type",
        "group",
        "product",
        "channel",
        "department",
        "class",
        "name",
    )

    for col in df.columns:
        if col in time_names or pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = df[col]
        non_null = series.dropna()

        if non_null.empty or is_identifier_column(col, series):
            continue

        nunique = non_null.nunique(dropna=True)
        if nunique < 2 or nunique > 60:
            continue

        top_share = non_null.value_counts(normalize=True).iloc[0]
        lower = str(col).lower()
        score = (1 - min(top_share, 0.95)) + min(nunique, 20) / 20

        if 2 <= nunique <= 20:
            score += 0.55
        if any(token in lower for token in segment_keywords):
            score += 0.55

        candidates.append((score, col))

    return [col for _, col in sorted(candidates, reverse=True)]


def strongest_corr_pair(df, numeric_cols):
    if len(numeric_cols) < 2:
        return None

    corr = df[numeric_cols].corr(numeric_only=True).abs()
    mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    pairs = corr.where(mask).stack().sort_values(ascending=False)

    if pairs.empty:
        return numeric_cols[0], numeric_cols[1]

    return pairs.index[0]


def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        colorway=CHART_COLORS,
        font=dict(color=INK, family="Inter, Segoe UI, Arial", size=13),
        title_font=dict(color=INK, size=18),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=58, r=30, t=58, b=58),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(color=INK, gridcolor="#e8edf3", zerolinecolor="#cfd7e3", linecolor="#cfd7e3")
    fig.update_yaxes(color=INK, gridcolor="#e8edf3", zerolinecolor="#cfd7e3", linecolor="#cfd7e3")
    return fig


def save_chart(fig, path):
    try:
        style_chart(fig)
        fig.write_image(path, width=1100, height=620, scale=1)
        return path
    except Exception as exc:
        if not st.session_state.get("chart_export_warning"):
            st.warning(
                "Interactive charts are available, but static chart export failed. "
                f"PPT charts may be skipped until Kaleido can render images. Details: {exc}"
            )
            st.session_state.chart_export_warning = True
        return None


def add_chart(charts, key, title, caption, group, priority, fig):
    safe_key = safe_filename(key)
    path = save_chart(fig, f"outputs/charts/{safe_key}.png")
    charts.append(
        ChartSpec(
            key=key,
            title=title,
            caption=caption,
            group=group,
            priority=priority,
            fig=fig,
            path=path,
        )
    )


def build_chart_catalog(df):
    chart_df = working_dataframe(df)
    time_cols = detect_time_columns(chart_df)
    numeric_cols = numeric_columns_ranked(chart_df)
    categorical_cols = categorical_columns_ranked(chart_df, time_cols)
    charts = []

    missing = chart_df.isnull().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    if not missing.empty:
        missing_frame = (
            pd.DataFrame(
                {
                    "Column": missing.index.astype(str),
                    "Missing values": missing.values,
                    "Missing rate": missing.values / len(chart_df),
                }
            )
            .head(14)
            .sort_values("Missing values")
        )
        fig = px.bar(
            missing_frame,
            x="Missing values",
            y="Column",
            orientation="h",
            color="Missing rate",
            color_continuous_scale=["#dbeafe", RED],
            title="Missing Values by Column",
        )
        add_chart(
            charts,
            "missing_values",
            "Missing Values by Column",
            "Highlights columns most likely to affect model quality, summaries, and downstream decisions.",
            "Quality",
            100,
            fig,
        )

    if numeric_cols:
        metric = numeric_cols[0]
        clean_count = pd.to_numeric(chart_df[metric], errors="coerce").notna().sum()
        bins = int(min(45, max(12, np.sqrt(max(clean_count, 1)))))
        fig = px.histogram(
            chart_df,
            x=metric,
            nbins=bins,
            marginal="box",
            title=f"Distribution of {metric}",
            color_discrete_sequence=[BLUE],
        )
        add_chart(
            charts,
            f"distribution_{metric}",
            f"Distribution of {metric}",
            "Shows the main numeric measure's range, skew, and unusual values in one view.",
            "Measures",
            95,
            fig,
        )

    outlier_candidates = []
    for col in numeric_cols[:8]:
        series = pd.to_numeric(chart_df[col], errors="coerce").dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        count = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
        outlier_candidates.append((count, col))

    outlier_candidates = sorted(outlier_candidates, reverse=True)
    if outlier_candidates and outlier_candidates[0][0] > 0:
        _, outlier_col = outlier_candidates[0]
        fig = px.box(
            chart_df,
            y=outlier_col,
            points="outliers",
            title=f"Outlier Scan for {outlier_col}",
            color_discrete_sequence=[AMBER],
        )
        add_chart(
            charts,
            f"outliers_{outlier_col}",
            f"Outlier Scan for {outlier_col}",
            "Focuses attention on extreme records that can distort averages, forecasts, and reports.",
            "Quality",
            88,
            fig,
        )

    if time_cols and numeric_cols:
        time_col, time_kind = time_cols[0]
        metric = next((col for col in numeric_cols if col != time_col), numeric_cols[0])
        tmp = pd.DataFrame({"time": chart_df[time_col], "value": chart_df[metric]}).dropna()

        if not tmp.empty and tmp["time"].nunique() > 1:
            if time_kind == "datetime":
                tmp["time"] = pd.to_datetime(tmp["time"], errors="coerce")
                tmp = tmp.dropna().sort_values("time")
                if tmp["time"].nunique() > 35:
                    grouped = (
                        tmp.set_index("time")["value"]
                        .resample("ME")
                        .mean()
                        .dropna()
                        .reset_index()
                    )
                    grouped.columns = ["time", "value"]
                else:
                    grouped = tmp.groupby("time", as_index=False)["value"].mean()
            else:
                tmp["time"] = pd.to_numeric(tmp["time"], errors="coerce")
                grouped = tmp.dropna().groupby("time", as_index=False)["value"].mean()

            if len(grouped) > 1:
                fig = px.line(
                    grouped,
                    x="time",
                    y="value",
                    markers=True,
                    title=f"Trend of {metric} by {time_col}",
                    color_discrete_sequence=[TEAL],
                )
                add_chart(
                    charts,
                    f"trend_{metric}_by_{time_col}",
                    f"Trend of {metric} by {time_col}",
                    "Tracks whether the most important measure is rising, falling, or changing by period.",
                    "Trend",
                    92,
                    fig,
                )

    if categorical_cols:
        cat = categorical_cols[0]
        top = chart_df[cat].astype(str).value_counts().nlargest(12)
        top_frame = pd.DataFrame({"Category": top.index, "Records": top.values}).sort_values("Records")
        fig = px.bar(
            top_frame,
            x="Records",
            y="Category",
            orientation="h",
            title=f"Top Segments in {cat}",
            color="Records",
            color_continuous_scale=["#d1fae5", TEAL],
        )
        add_chart(
            charts,
            f"segments_{cat}",
            f"Top Segments in {cat}",
            "Shows where the dataset is concentrated so analysis is not driven by hidden segment imbalance.",
            "Segments",
            86,
            fig,
        )

    if categorical_cols and numeric_cols:
        metric = numeric_cols[0]
        selected_cat = None
        for cat in categorical_cols:
            if 2 <= chart_df[cat].nunique(dropna=True) <= 24:
                selected_cat = cat
                break

        if selected_cat:
            grouped = (
                chart_df.groupby(selected_cat, dropna=False)[metric]
                .agg(["mean", "count"])
                .reset_index()
                .dropna(subset=["mean"])
                .sort_values("mean", ascending=False)
                .head(12)
            )

            if not grouped.empty:
                grouped[selected_cat] = grouped[selected_cat].astype(str)
                fig = px.bar(
                    grouped.sort_values("mean"),
                    x="mean",
                    y=selected_cat,
                    orientation="h",
                    color="count",
                    color_continuous_scale=["#fff7ed", AMBER],
                    title=f"Average {metric} by {selected_cat}",
                )
                fig.update_layout(coloraxis_colorbar_title="Records")
                add_chart(
                    charts,
                    f"metric_by_segment_{metric}_{selected_cat}",
                    f"Average {metric} by {selected_cat}",
                    "Compares performance by segment while color shows whether each average has enough records behind it.",
                    "Segments",
                    90,
                    fig,
                )

    if len(numeric_cols) >= 2:
        pair = strongest_corr_pair(chart_df, numeric_cols[:8])
        if pair:
            x_col, y_col = pair
            color_col = None
            for cat in categorical_cols:
                if chart_df[cat].nunique(dropna=True) <= 8:
                    color_col = cat
                    break

            fig = px.scatter(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col,
                opacity=0.74,
                title=f"Relationship: {y_col} vs {x_col}",
            )

            clean = chart_df[[x_col, y_col]].dropna()
            if len(clean) >= 3:
                clean = clean.sort_values(x_col)
                try:
                    slope, intercept = np.polyfit(clean[x_col], clean[y_col], 1)
                    fig.add_scatter(
                        x=clean[x_col],
                        y=(slope * clean[x_col]) + intercept,
                        mode="lines",
                        name="Linear fit",
                        line=dict(color=RED, width=2),
                    )
                except Exception:
                    pass

            add_chart(
                charts,
                f"relationship_{y_col}_vs_{x_col}",
                f"Relationship: {y_col} vs {x_col}",
                "Uses the strongest numeric pair to reveal correlation, clusters, and records far from the pattern.",
                "Relationships",
                84,
                fig,
            )

    if len(numeric_cols) >= 2:
        corr_cols = numeric_cols[: min(8, len(numeric_cols))]
        corr = chart_df[corr_cols].corr(numeric_only=True)

        if not corr.empty and not corr.isnull().all().all():
            fig = px.imshow(
                corr,
                text_auto=".2f",
                zmin=-1,
                zmax=1,
                color_continuous_scale="RdBu",
                color_continuous_midpoint=0,
                title="Correlation Map for Key Measures",
            )
            add_chart(
                charts,
                "correlation_key_measures",
                "Correlation Map for Key Measures",
                "Identifies which important numeric parameters move together and which ones behave independently.",
                "Relationships",
                82,
                fig,
            )

        spread_rows = []
        for col in corr_cols[:6]:
            series = pd.to_numeric(chart_df[col], errors="coerce").dropna()
            if series.empty:
                continue
            spread_rows.append(
                {
                    "Parameter": col,
                    "IQR": series.quantile(0.75) - series.quantile(0.25),
                    "Median": series.median(),
                }
            )

        if spread_rows:
            spread_frame = pd.DataFrame(spread_rows).sort_values("IQR", ascending=False)
            fig = px.bar(
                spread_frame,
                x="Parameter",
                y="IQR",
                color="Median",
                color_continuous_scale=["#eef2ff", VIOLET],
                title="Most Variable Numeric Parameters",
            )
            add_chart(
                charts,
                "important_numeric_parameters",
                "Most Variable Numeric Parameters",
                "Ranks numeric fields by spread so the dashboard prioritizes parameters with real movement.",
                "Measures",
                80,
                fig,
            )

    charts.sort(key=lambda item: item.priority, reverse=True)
    return charts


def get_cached_chart_catalog(df):
    cache_key = dataframe_fingerprint(df)

    if (
        st.session_state.chart_cache_key == cache_key
        and st.session_state.chart_cache
    ):
        return st.session_state.chart_cache

    charts = build_chart_catalog(df)
    st.session_state.chart_cache_key = cache_key
    st.session_state.chart_cache = charts
    return charts


def chart_lookup(charts):
    return {chart.key: chart for chart in charts}


def build_column_summary(df):
    time_cols = detect_time_columns(df)
    time_names = {col for col, _ in time_cols}
    numeric_cols = set(numeric_columns_ranked(df))
    categorical_cols = set(categorical_columns_ranked(df, time_cols))
    rows = []

    for col in df.columns:
        series = df[col]
        missing = int(series.isnull().sum())
        unique = int(series.nunique(dropna=True))

        if col in time_names:
            role = "Time"
        elif col in numeric_cols:
            role = "Measure"
        elif col in categorical_cols:
            role = "Segment"
        elif is_identifier_column(col, series):
            role = "Identifier"
        else:
            role = "Attribute"

        rows.append(
            {
                "Column": col,
                "Role": role,
                "Type": str(series.dtype),
                "Missing": missing,
                "Missing %": round((missing / len(df)) * 100, 2) if len(df) else 0,
                "Unique": unique,
            }
        )

    return pd.DataFrame(rows)


def render_readable_value(value):
    if value is None:
        st.info("No result returned.")
    elif isinstance(value, pd.DataFrame):
        st.dataframe(value, use_container_width=True)
    elif isinstance(value, pd.Series):
        st.dataframe(value.reset_index(), use_container_width=True)
    elif isinstance(value, dict):
        for key, item in value.items():
            st.markdown(f"**{escape(key)}**")
            render_readable_value(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            st.write(item)
    else:
        st.markdown(
            f"<div class='readable-output'>{escape(value)}</div>",
            unsafe_allow_html=True,
        )


def format_agent_value(value):
    if value is None:
        return None
    if isinstance(value, pd.Series):
        try:
            return value.to_list()
        except Exception:
            return str(value)
    if isinstance(value, pd.DataFrame):
        return value.head(12).to_dict()
    return str(value)


def local_report_inputs(df):
    chart_df = working_dataframe(df)
    return ProfilingAgent().run(chart_df), DataQualityAgent().run(chart_df)


def run_agent_workflow(query, df):
    conv = StateManager.get_conversation()
    cache_key = (
        dataframe_fingerprint(df),
        query.strip().lower(),
        tuple(
            (item.get("role", ""), str(item.get("content", ""))[:250])
            for item in compact_conversation(conv, max_messages=4, max_chars=1000)
        ),
    )

    conv.append({"role": "user", "content": query})
    StateManager.update_conversation(conv)

    cached_result = st.session_state.analysis_cache.get(cache_key)

    if cached_result:
        cached_conv = StateManager.get_conversation()
        cached_conv.append(
            {
                "role": "assistant",
                "content": "Loaded the previous analysis for this same question.",
            }
        )
        StateManager.update_conversation(cached_conv)
        st.session_state.latest_result = cached_result
        st.session_state.report_path = None
        return

    state = {
        "query": query,
        "df": df,
        "conversation": compact_conversation(conv),
        "profile": {},
        "quality_report": {},
        "dataset_summary": "",
        "analysis_result": {},
        "visualization_result": {},
        "insights": "",
        "recommendations": "",
        "execution_trace": [],
    }

    result = invoke_fast_workflow(state)

    analysis_res = result.get("analysis_result", {}).get("result")
    insights = result.get("insights")
    ar = format_agent_value(analysis_res)
    ir = format_agent_value(insights)
    assistant_reply = (
        ar
        if ar is not None and ar != []
        else (ir if ir is not None and ir != [] else "Analysis complete.")
    )

    conv = StateManager.get_conversation()
    conv.append({"role": "assistant", "content": str(assistant_reply)})
    StateManager.update_conversation(conv)
    st.session_state.latest_result = result
    st.session_state.analysis_cache[cache_key] = result
    st.session_state.report_path = None


def render_upload():
    render_header()

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown('<div class="section-label">Dataset Intake</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Dataset file",
            type=("csv", "xlsx", "xls", "json", "db", "sqlite", "sqlite3"),
            help="CSV, Excel, JSON, and SQLite files are supported.",
        )

        query = None
        source_type = None

        if uploaded_file is not None:
            source_type = uploaded_source(uploaded_file)
            st.info(f"Detected source: {source_type}")

            if source_type == "SQLite":
                query = st.text_area("SQL Query", "SELECT * FROM table_name LIMIT 1000")

            try:
                if source_type == "SQLite":
                    tmp_path = None
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    try:
                        df = DataLoader.load_sqlite(
                            tmp_path,
                            query or "SELECT name FROM sqlite_master WHERE type='table';",
                        )
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.remove(tmp_path)
                elif source_type in ("CSV", "Excel", "JSON"):
                    df = DataLoader.load_file(uploaded_file)
                else:
                    raise ValueError("Unsupported file type.")

                StateManager.save_dataframe(
                    df=df,
                    file_name=getattr(uploaded_file, "name", "uploaded"),
                    source=source_type,
                )
                StateManager.update_conversation([])
                st.session_state.latest_result = None
                st.session_state.selected_chart_keys = []
                st.session_state.report_path = None
                st.session_state.chart_cache_key = None
                st.session_state.chart_cache = []
                st.session_state.analysis_cache = {}
                st.success("Dataset loaded.")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to load dataset: {exc}")

    with right:
        st.markdown('<div class="section-label">Workspace Snapshot</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            render_status("Formats", "CSV, Excel, JSON", "SQLite is available for query-based intake.")
        with c2:
            render_status("Output", "PPT report", "Selected charts are included in the export.")

        st.markdown(
            """
<div class="empty-note">
    Upload a dataset to open the dashboard.
</div>
""",
            unsafe_allow_html=True,
        )


def render_overview(df, profile, quality_report, column_summary):
    rows, cols = df.shape
    missing_count = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    numeric_count = int(df.select_dtypes(include="number").shape[1])
    segment_count = int(
        column_summary[column_summary["Role"].isin(["Segment", "Attribute"])].shape[0]
    )

    metric_cols = st.columns(6)
    with metric_cols[0]:
        render_metric("Rows", format_number(rows), "Records loaded", "blue")
    with metric_cols[1]:
        render_metric("Columns", format_number(cols), "Fields available", "teal")
    with metric_cols[2]:
        render_metric("Missing", format_number(missing_count), pct(missing_count, rows * cols), "amber")
    with metric_cols[3]:
        render_metric("Duplicates", format_number(duplicate_count), pct(duplicate_count, rows), "red")
    with metric_cols[4]:
        render_metric("Measures", format_number(numeric_count), "Numeric parameters", "green")
    with metric_cols[5]:
        render_metric("Attributes", format_number(segment_count), "Segments and labels", "violet")

    st.divider()

    q1, q2, q3 = st.columns(3)
    constant_cols = quality_report.get("constant_columns", [])
    high_cardinality = quality_report.get("high_cardinality", {})
    outliers = quality_report.get("outliers", {})
    outlier_total = sum(outliers.values()) if isinstance(outliers, dict) else 0

    with q1:
        render_status("Data completeness", pct((rows * cols) - missing_count, rows * cols), "Non-missing cell coverage.")
    with q2:
        render_status("Constant columns", format_number(len(constant_cols)), "Fields with one observed value.")
    with q3:
        render_status("Outlier flags", format_number(outlier_total), "IQR-based numeric outlier count.")

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown('<div class="section-label">Column Roles</div>', unsafe_allow_html=True)
        st.dataframe(column_summary, use_container_width=True, hide_index=True)

    with right:
        st.markdown('<div class="section-label">Data Preview</div>', unsafe_allow_html=True)
        st.dataframe(df.head(12), use_container_width=True)

        top_missing = column_summary.sort_values("Missing", ascending=False).head(8)
        if top_missing["Missing"].sum() > 0:
            st.markdown('<div class="section-label">Missing Data Focus</div>', unsafe_allow_html=True)
            st.dataframe(
                top_missing[["Column", "Missing", "Missing %"]],
                use_container_width=True,
                hide_index=True,
            )

    if high_cardinality:
        with st.expander("High-cardinality fields"):
            st.dataframe(
                pd.DataFrame(
                    {"Column": list(high_cardinality.keys()), "Unique": list(high_cardinality.values())}
                ),
                use_container_width=True,
                hide_index=True,
            )

    if profile.get("statistics"):
        with st.expander("Numeric statistics"):
            stats = pd.DataFrame(profile["statistics"]).T.reset_index().rename(columns={"index": "Column"})
            st.dataframe(stats, use_container_width=True, hide_index=True)


def render_visual_lab(charts):
    if not charts:
        st.markdown(
            """
<div class="empty-note">
    This dataset does not have enough numeric, categorical, missing-value, or time fields for automatic charts.
</div>
""",
            unsafe_allow_html=True,
        )
        return []

    lookup = chart_lookup(charts)
    chart_keys = [chart.key for chart in charts if chart.path]
    default_keys = chart_keys[: min(6, len(chart_keys))]
    saved_keys = [key for key in st.session_state.selected_chart_keys if key in chart_keys]

    if not saved_keys and default_keys:
        st.session_state.selected_chart_keys = default_keys

    top, controls = st.columns([1, 0.9], gap="large")

    with top:
        st.markdown('<div class="section-label">Priority Visuals</div>', unsafe_allow_html=True)
        render_status(
            "Generated charts",
            format_number(len(charts)),
            "Ranked by quality, trend, segment, and relationship value.",
        )

    with controls:
        st.markdown('<div class="section-label">Report Visuals</div>', unsafe_allow_html=True)
        if chart_keys:
            selected = st.multiselect(
                "Charts for PPT",
                chart_keys,
                format_func=lambda key: lookup[key].title,
                key="selected_chart_keys",
            )
        else:
            selected = []
            st.info("Static chart export is unavailable, so no charts can be added to the PPT yet.")

    st.divider()

    st.markdown('<div class="section-label">Generated Graph Names</div>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(
            {
                "Graph name": [chart.title for chart in charts],
                "Type": [chart.group for chart in charts],
                "Why it is useful": [chart.caption for chart in charts],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    grid = st.columns(2)
    for index, chart in enumerate(charts):
        with grid[index % 2]:
            st.markdown(
                f"""
<div class="chart-copy">
    <h3>{escape(chart.title)}</h3>
    <p>{escape(chart.caption)}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                chart.fig,
                use_container_width=True,
                config={"displaylogo": False, "responsive": True},
            )

    return selected


def render_ai_workspace(df):
    st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)

    conversation = StateManager.get_conversation()
    if not conversation:
        st.markdown(
            """
<div class="empty-note">
    Ask a question to run the multi-agent workflow.
</div>
""",
            unsafe_allow_html=True,
        )

    for item in conversation:
        role = item.get("role", "assistant")
        with st.chat_message(role):
            st.write(item.get("content", ""))

    query = st.chat_input("Ask a question about this dataset")

    if query:
        with st.spinner("Running the analysis workflow..."):
            try:
                run_agent_workflow(query, df)
            except Exception as exc:
                conv = StateManager.get_conversation()
                conv.append({"role": "assistant", "content": f"Analysis failed: {exc}"})
                StateManager.update_conversation(conv)
                st.session_state.latest_result = None
                st.error(f"Analysis failed: {exc}")
        st.rerun()

    result = st.session_state.get("latest_result")
    if not result:
        return

    st.divider()
    st.markdown('<div class="section-label">Latest Agent Output</div>', unsafe_allow_html=True)

    trace = result.get("execution_trace", [])
    if trace:
        with st.expander("Execution trace", expanded=False):
            for step in trace:
                clean_step = (
                    str(step)
                    .replace("âœ…", "Completed:")
                    .replace("✅", "Completed:")
                )
                st.write(clean_step)

    visual_result = result.get("visualization_result", {})
    fig = visual_result.get("figure") if isinstance(visual_result, dict) else None
    if fig is not None:
        st.markdown('<div class="section-label">AI-Generated Chart</div>', unsafe_allow_html=True)
        try:
            st.plotly_chart(
                style_chart(fig),
                use_container_width=True,
                config={"displaylogo": False, "responsive": True},
            )
        except Exception:
            st.info("The AI generated a chart, but Streamlit could not render it.")

    analysis_result = result.get("analysis_result", {})
    with st.expander("Analysis result", expanded=True):
        if isinstance(analysis_result, dict):
            st.markdown("**Success**")
            st.write(analysis_result.get("success", ""))
            generated_code = analysis_result.get("generated_code")
            if generated_code:
                with st.expander("Generated code"):
                    st.code(generated_code, language="python")
            st.markdown("**Result**")
            render_readable_value(analysis_result.get("result"))
        else:
            render_readable_value(analysis_result)

    insight_col, rec_col = st.columns(2, gap="large")
    with insight_col:
        st.markdown('<div class="section-label">Insights</div>', unsafe_allow_html=True)
        render_readable_value(result.get("insights", ""))
    with rec_col:
        st.markdown('<div class="section-label">Recommendations</div>', unsafe_allow_html=True)
        render_readable_value(result.get("recommendations", ""))


def render_report(df, charts, profile, quality_report):
    lookup = chart_lookup(charts)
    selected_keys = [key for key in st.session_state.selected_chart_keys if key in lookup]
    selected_charts = [lookup[key] for key in selected_keys if lookup[key].path]

    st.markdown('<div class="section-label">Report Builder</div>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    with r1:
        render_status("Selected visuals", format_number(len(selected_charts)), "Charts included in PPT export.")
    with r2:
        render_status("AI result", "Ready" if st.session_state.get("latest_result") else "Pending", "Analysis text is added when available.")
    with r3:
        render_status("Export file", "PPTX", "Generated in the outputs folder.")

    if selected_charts:
        st.dataframe(
            pd.DataFrame(
                {
                    "Chart": [chart.title for chart in selected_charts],
                    "Group": [chart.group for chart in selected_charts],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Select at least one exported chart in Visual Lab to add visuals to the PPT.")

    latest = st.session_state.get("latest_result") or {}
    report_profile = latest.get("profile") or profile
    report_quality = latest.get("quality_report") or quality_report
    insights = latest.get("insights", "No AI insights generated yet.")
    recommendations = latest.get("recommendations", "No AI recommendations generated yet.")
    analysis_result = latest.get("analysis_result", {"result": "No AI analysis generated yet."})

    if st.button("Build PPT Report"):
        chart_items = [
            (chart.path, chart.title, chart.caption)
            for chart in selected_charts
        ]
        prs = PresentationService()
        output_name = safe_filename(StateManager.get_file_name() or "AI_Report")
        report_path = prs.create_report(
            file_name=StateManager.get_file_name() or "dataset",
            profile=report_profile,
            quality_report=report_quality,
            analysis_result=analysis_result,
            insights=insights,
            recommendations=recommendations,
            chart_items=chart_items,
            output_path=f"outputs/{output_name}.pptx",
        )
        st.session_state.report_path = report_path
        st.success("PPT report built.")

    report_path = st.session_state.get("report_path")
    if report_path and os.path.exists(report_path):
        with open(report_path, "rb") as report_file:
            st.download_button(
                "Download PPT Report",
                data=report_file,
                file_name=os.path.basename(report_path),
            )


df = StateManager.get_dataframe()

if df is None:
    render_upload()
    st.stop()

df = working_dataframe(df)
profile, quality_report = local_report_inputs(df)
column_summary = build_column_summary(df)
charts = get_cached_chart_catalog(df)

render_header(df)

action_left, action_right = st.columns([1, 5])
with action_left:
    if st.button("Reset Dataset"):
        reset_workspace()
        st.rerun()
with action_right:
    file_name = StateManager.get_file_name() or "dataset"
    st.caption(f"Active dataset: {file_name}")

overview_tab, visual_tab, ai_tab, report_tab = st.tabs(
    ["Overview", "Visual Lab", "AI Workspace", "Report"]
)

with overview_tab:
    render_overview(df, profile, quality_report, column_summary)

with visual_tab:
    render_visual_lab(charts)

with ai_tab:
    render_ai_workspace(df)

with report_tab:
    render_report(df, charts, profile, quality_report)
