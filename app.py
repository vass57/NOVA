"""Bilingual, responsive Streamlit interface for the CorroborIA reviewer."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from corroboria.export import audit_to_json, cases_to_csv, run_to_excel
from corroboria.i18n import translate, translate_value
from corroboria.pipeline import InputPaths, InputValidationError, ReconciliationRun, run_reconciliation


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


def _set_preference(name: str, value: str) -> None:
    st.session_state[name] = value


def _initialise_preferences() -> tuple[str, str]:
    if "locale" not in st.session_state:
        st.session_state.locale = "en"
    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = "light"
    return st.session_state.locale, st.session_state.ui_theme


def _theme_variables(theme: str) -> str:
    if theme == "dark":
        return """
        :root {
          --canvas: #08111f; --canvas-end: #101d34; --ink: #f5f8ff; --muted: #b7c4d6;
          --surface: rgba(20, 35, 59, 0.91); --surface-raised: #1a2c49; --control: #10243f;
          --line: rgba(202, 219, 241, 0.20); --line-strong: rgba(80, 227, 201, 0.48);
          --teal: #18c7af; --teal-dark: #7bf1df; --indigo: #8b86ff; --coral: #ff7c8c;
          --amber: #ffc563; --soft-teal: rgba(18, 199, 175, 0.13); --shadow: rgba(0, 0, 0, 0.30);
        }
        """
    return """
    :root {
      --canvas: #f7fbff; --canvas-end: #edf3fa; --ink: #10172a; --muted: #52647c;
      --surface: rgba(255, 255, 255, 0.91); --surface-raised: #ffffff; --control: #ffffff;
      --line: rgba(15, 23, 42, 0.13); --line-strong: rgba(15, 174, 154, 0.48);
      --teal: #0fae9a; --teal-dark: #087f72; --indigo: #4f46e5; --coral: #ef5f72;
      --amber: #f4a83b; --soft-teal: rgba(15, 174, 154, 0.10); --shadow: rgba(25, 48, 85, 0.14);
    }
    """


def _inject_theme(theme: str) -> None:
    """Render a self-contained visual system with a light and dark palette."""

    css = """
      .stApp, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(circle at 4% 1%, color-mix(in srgb, var(--teal) 17%, transparent), transparent 25rem),
          radial-gradient(circle at 97% 2%, color-mix(in srgb, var(--indigo) 15%, transparent), transparent 28rem),
          linear-gradient(135deg, var(--canvas) 0%, var(--canvas-end) 100%);
        color: var(--ink);
        transition: background 420ms ease, color 260ms ease;
      }

      .block-container { max-width: 1380px; padding-top: 1.35rem; padding-bottom: 3.5rem; }
      [data-testid="stHeader"] { background: transparent; }
      [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label,
      [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] { color: var(--ink); }
      [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }

      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1930 0%, #172745 54%, #087f72 160%);
        border-right: 1px solid rgba(255, 255, 255, 0.11);
      }
      [data-testid="stSidebar"] * { color: #effaff; }
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #b9cddd !important; }
      [data-testid="stSidebar"] [data-testid="stAlert"] * { color: #effaff !important; }
      [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.08); border: 1px dashed rgba(255,255,255,0.36); border-radius: 16px;
      }
      [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
      [data-testid="stSidebar"] button[kind="secondary"] {
        min-height: 2.7rem; background: rgba(255,255,255,0.13); border-color: rgba(255,255,255,0.30);
        color: #f4faff !important; font-size: 0.82rem; font-weight: 760;
      }
      [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.21); border-color: rgba(162,255,237,0.68);
        box-shadow: 0 8px 18px rgba(0,0,0,0.18);
      }
      [data-testid="stSidebar"] button[kind="primary"] {
        min-height: 2.7rem; background: linear-gradient(120deg, #0fae9a, #5360db) !important;
        background-size: 100% 100% !important; color: #ffffff !important; animation: none !important;
      }
      [data-testid="stSidebar"] button:focus-visible,
      [data-testid="stAppViewContainer"] button:focus-visible,
      [data-baseweb="select"] > div:focus-within,
      [data-baseweb="input"] > div:focus-within,
      [data-testid="stTextArea"] textarea:focus {
        outline: 3px solid color-mix(in srgb, var(--teal) 45%, transparent) !important;
        outline-offset: 2px;
      }

      .brand-lockup { display:flex; align-items:center; gap:0.8rem; margin:0.5rem 0 1.45rem; }
      .brand-mark {
        display:grid; place-items:center; width:2.65rem; height:2.65rem; border-radius:15px; color:white; font-size:1.18rem; font-weight:850;
        background:linear-gradient(135deg,#25d0b5,#5d62ef); box-shadow:0 12px 28px rgba(0,0,0,0.28); animation: logo-float 5s ease-in-out infinite;
      }
      .brand-name { font-size:1.14rem; font-weight:790; letter-spacing:-0.02em; }
      .brand-subtitle { color:#acc4d8; font-size:0.69rem; font-weight:700; letter-spacing:0.11em; margin-top:0.1rem; }
      .pref-label { color:#b9cddd; font-size:0.67rem; font-weight:800; letter-spacing:0.10em; text-transform:uppercase; margin:1.1rem 0 0.32rem; }

      .hero {
        position:relative; overflow:hidden; padding:clamp(1.6rem,4vw,3.15rem); border:1px solid rgba(255,255,255,0.55); border-radius:28px;
        background:linear-gradient(125deg,#15213d 0%,#22355e 49%,#164a5b 110%); color:#f8fbff; box-shadow:0 26px 62px var(--shadow);
        animation: rise-in 650ms cubic-bezier(.2,.8,.2,1) both;
      }
      .hero::before,.hero::after { content:""; position:absolute; border-radius:999px; pointer-events:none; filter:blur(1px); opacity:0.62; animation:orbital-drift 13s ease-in-out infinite alternate; }
      .hero::before { right:-7rem; top:-10rem; width:21rem; height:21rem; background:rgba(35,219,190,0.25); }
      .hero::after { left:48%; bottom:-15rem; width:24rem; height:24rem; background:rgba(110,99,255,0.29); animation-delay:-6s; }
      .hero > * { position:relative; z-index:1; }
      .eyebrow { display:inline-flex; align-items:center; gap:0.4rem; margin-bottom:0.78rem; padding:0.35rem 0.68rem; border:1px solid rgba(213,255,248,0.27); border-radius:999px; background:rgba(5,16,35,0.22); color:#c9fff4; font-size:0.70rem; font-weight:780; letter-spacing:0.09em; text-transform:uppercase; }
      .live-dot { width:0.48rem; height:0.48rem; border-radius:50%; background:#53f2d8; box-shadow:0 0 0 0 rgba(83,242,216,0.58); animation:pulse 1.9s infinite; }
      .hero h1 { max-width:780px; margin:0; color:white; font-size:clamp(2rem,5vw,4rem); font-weight:800; letter-spacing:-0.058em; line-height:0.98; }
      .hero p { max-width:640px; margin:1rem 0 0; color:#d6e6f5; font-size:clamp(0.96rem,1.5vw,1.1rem); line-height:1.65; }
      .hero-pills { display:flex; flex-wrap:wrap; gap:0.55rem; margin-top:1.3rem; }
      .hero-pill { padding:0.42rem 0.72rem; border:1px solid rgba(255,255,255,0.15); border-radius:999px; background:rgba(255,255,255,0.12); color:#effbff; font-size:0.76rem; transition:transform 180ms ease, background 180ms ease; }
      .hero-pill:hover { transform:translateY(-2px); background:rgba(255,255,255,0.2); }

      .flow-track { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:0.65rem; margin:1.15rem 0 1.7rem; }
      .flow-step { min-width:0; padding:0.88rem; border:1px solid var(--line); border-radius:16px; background:var(--surface); box-shadow:0 8px 23px rgba(15,23,42,0.045); transition:transform 220ms ease, border-color 220ms ease, background 280ms ease; animation:rise-in 600ms cubic-bezier(.2,.8,.2,1) both; }
      .flow-step:nth-child(2){animation-delay:70ms}.flow-step:nth-child(3){animation-delay:140ms}.flow-step:nth-child(4){animation-delay:210ms}
      .flow-step:hover { transform:translateY(-3px); border-color:var(--line-strong); }
      .flow-step.current { border-color:var(--line-strong); background:linear-gradient(135deg,var(--soft-teal),var(--surface)); }
      .flow-number { display:inline-grid; place-items:center; width:1.58rem; height:1.58rem; margin-bottom:0.45rem; border-radius:50%; background:color-mix(in srgb,var(--muted) 17%,transparent); color:var(--muted); font-size:0.70rem; font-weight:850; }
      .flow-step.current .flow-number { background:var(--teal); color:white; box-shadow:0 6px 14px color-mix(in srgb,var(--teal) 35%,transparent); }
      .flow-title { color:var(--ink); font-size:0.84rem; font-weight:780; }.flow-copy{margin-top:.17rem;color:var(--muted);font-size:.72rem;line-height:1.38}

      .section-kicker { margin:1.55rem 0 0.26rem; color:var(--teal-dark); font-size:0.69rem; font-weight:850; letter-spacing:0.11em; text-transform:uppercase; }
      .section-title { margin:0 0 .9rem; color:var(--ink); font-size:clamp(1.35rem,2.4vw,1.85rem); font-weight:790; letter-spacing:-0.038em; }
      .metric-card { position:relative; overflow:hidden; min-height:132px; padding:1rem 1.05rem; border:1px solid var(--line); border-radius:18px; background:var(--surface); box-shadow:0 12px 25px rgba(15,23,42,.055); transition:transform 220ms ease,box-shadow 220ms ease,border-color 220ms ease; animation:rise-in 600ms cubic-bezier(.2,.8,.2,1) both; }
      .metric-card:nth-child(1){animation-delay:50ms}.metric-card::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:var(--accent)}.metric-card::after{content:"";position:absolute;top:-32px;right:-25px;width:86px;height:86px;border-radius:50%;background:var(--accent-soft);transition:transform 400ms ease}.metric-card:hover{transform:translateY(-4px);box-shadow:0 18px 30px var(--shadow);border-color:color-mix(in srgb,var(--accent) 38%,var(--line))}.metric-card:hover::after{transform:scale(1.28)}
      .metric-card--alert{--accent:var(--coral);--accent-soft:color-mix(in srgb,var(--coral) 12%,transparent)}.metric-card--review{--accent:var(--amber);--accent-soft:color-mix(in srgb,var(--amber) 14%,transparent)}.metric-card--rule{--accent:var(--indigo);--accent-soft:color-mix(in srgb,var(--indigo) 12%,transparent)}.metric-card--match{--accent:var(--teal);--accent-soft:color-mix(in srgb,var(--teal) 13%,transparent)}
      .metric-label{color:var(--muted);font-size:.75rem;font-weight:720}.metric-value{margin:.3rem 0;color:var(--ink);font-size:2.15rem;font-weight:830;letter-spacing:-.065em}.metric-note{color:var(--muted);font-size:.70rem}

      .insight-panel { display:flex; align-items:center; gap:1rem; padding:1rem 1.1rem; border:1px solid color-mix(in srgb,var(--teal) 22%,var(--line)); border-radius:18px; background:linear-gradient(110deg,var(--soft-teal),var(--surface)); color:var(--ink); animation:rise-in 680ms cubic-bezier(.2,.8,.2,1) both; }
      .insight-orb { display:grid; flex:0 0 auto; place-items:center; width:2.7rem; height:2.7rem; border-radius:14px; background:linear-gradient(145deg,#13b8a2,#5a58db); color:white; font-size:1.08rem; box-shadow:0 9px 20px color-mix(in srgb,var(--teal) 25%,transparent); animation:logo-float 4.4s ease-in-out infinite; }
      .insight-title{font-size:.9rem;font-weight:800}.insight-copy{margin-top:.12rem;color:var(--muted);font-size:.8rem;line-height:1.46}

      [data-testid="stButton"]>button,[data-testid="stDownloadButton"]>button { min-height:2.7rem; border-radius:12px; font-weight:730; transition:transform 180ms ease,box-shadow 180ms ease,border-color 180ms ease,background 180ms ease; }
      [data-testid="stButton"]>button:hover,[data-testid="stDownloadButton"]>button:hover { transform:translateY(-2px); box-shadow:0 11px 22px var(--shadow); }
      [data-testid="stButton"]>button[kind="primary"] { min-height:3rem; border:0; background:linear-gradient(110deg,#0a9b8b,#3955dc 58%,#0a9b8b); background-size:210% 100%; box-shadow:0 12px 24px rgba(32,82,177,.24); color:#ffffff !important; animation:sheen 7s linear infinite; }
      [data-testid="stDownloadButton"]>button { background:var(--surface); border-color:var(--line); color:var(--ink); }

      [data-baseweb="select"]>div,[data-baseweb="input"]>div,[data-testid="stTextArea"] textarea { background:var(--control)!important; color:var(--ink)!important; border-color:var(--line)!important; border-radius:12px!important; }
      [data-baseweb="select"] *,[data-baseweb="input"] input,[data-testid="stTextArea"] textarea { color:var(--ink)!important; }
      [data-baseweb="popover"] { background:var(--surface-raised)!important; color:var(--ink)!important; }
      [data-baseweb="popover"] * { color:var(--ink)!important; }
      [data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:17px;overflow:hidden;box-shadow:0 10px 25px rgba(15,23,42,.045)}
      [data-testid="stExpander"]{border:1px solid var(--line);border-radius:15px;background:var(--surface);transition:border-color 180ms ease,box-shadow 180ms ease}[data-testid="stExpander"]:hover{border-color:var(--line-strong);box-shadow:0 8px 18px rgba(15,23,42,.05)}
      [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.42rem;border-bottom:0;overflow-x:auto}[data-testid="stTabs"] button[data-baseweb="tab"]{height:2.65rem;padding:0 1rem;border:1px solid var(--line);border-radius:12px;background:var(--surface);color:var(--muted);font-size:.81rem;font-weight:750;transition:all 180ms ease}[data-testid="stTabs"] button[data-baseweb="tab"]:hover{transform:translateY(-2px);border-color:var(--line-strong)}[data-testid="stTabs"] button[aria-selected="true"]{border-color:var(--line-strong);background:var(--soft-teal);color:var(--teal-dark)}[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none}
      [data-testid="stAlert"],[data-testid="stJson"]{border-radius:14px}[data-testid="stJson"]{border:1px solid var(--line)}

      @keyframes rise-in{from{opacity:0;transform:translateY(13px)}to{opacity:1;transform:translateY(0)}}
      @keyframes orbital-drift{from{transform:translate3d(-1rem,.65rem,0) scale(1)}to{transform:translate3d(1.15rem,-.75rem,0) scale(1.1)}}
      @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(83,242,216,.55)}70%{box-shadow:0 0 0 9px rgba(83,242,216,0)}100%{box-shadow:0 0 0 0 rgba(83,242,216,0)}}
      @keyframes sheen{0%,88%{background-position:100% 0}100%{background-position:-110% 0}}
      @keyframes logo-float{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-4px) rotate(2deg)}}
      @media(max-width:800px){.block-container{padding:.8rem 1rem 2.5rem}.hero{border-radius:22px}.flow-track{grid-template-columns:1fr 1fr}[data-testid="stButton"]>button[kind="primary"]{width:100%}.metric-card{min-height:115px;padding:.85rem}.metric-value{font-size:1.8rem}}
      @media(max-width:520px){.block-container{padding:.65rem .75rem 2rem}.hero{padding:1.35rem;border-radius:19px}.hero h1{font-size:2rem;line-height:1.04}.flow-track{grid-template-columns:1fr;gap:.5rem}.hero-pills{gap:.38rem}.hero-pill{font-size:.69rem}.section-title{font-size:1.34rem}.insight-panel{align-items:flex-start}.insight-orb{width:2.35rem;height:2.35rem;min-width:2.35rem}.metric-card{min-height:104px}.metric-value{font-size:1.7rem}[data-testid="stTabs"] button[data-baseweb="tab"]{padding:0 .78rem;font-size:.76rem}}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
    """
    st.markdown("<style>" + _theme_variables(theme) + css + "</style>", unsafe_allow_html=True)


def _to_buffer(upload: st.runtime.uploaded_file_manager.UploadedFile) -> BytesIO:
    buffer = BytesIO(upload.getvalue())
    buffer.name = upload.name  # type: ignore[attr-defined]
    return buffer


def _sidebar(locale: str, theme: str) -> InputPaths | None:
    """Render language, appearance, and input controls in the persistent rail."""

    t = lambda key, **values: translate(locale, key, **values)
    active_language = f"language_{locale}"
    active_theme = f"theme_{theme}"
    with st.sidebar:
        st.markdown(
            f'<div class="brand-lockup"><div class="brand-mark">C</div><div><div class="brand-name">CorroborIA</div><div class="brand-subtitle">{t("studio")}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="pref-label">{t("language")}</div>', unsafe_allow_html=True)
        language_columns = st.columns(2)
        language_columns[0].button("EN", type="primary" if locale == "en" else "secondary", width="stretch", key="language_en", on_click=_set_preference, args=("locale", "en"))
        language_columns[1].button("FR", type="primary" if locale == "fr" else "secondary", width="stretch", key="language_fr", on_click=_set_preference, args=("locale", "fr"))
        st.markdown(f'<div class="pref-label">{t("appearance")}</div>', unsafe_allow_html=True)
        appearance_columns = st.columns(2)
        appearance_columns[0].button(t("light"), type="primary" if theme == "light" else "secondary", width="stretch", key="theme_light", on_click=_set_preference, args=("ui_theme", "light"))
        appearance_columns[1].button(t("dark"), type="primary" if theme == "dark" else "secondary", width="stretch", key="theme_dark", on_click=_set_preference, args=("ui_theme", "dark"))
        st.markdown(
            f"""<style>
            [data-testid="stSidebar"] .st-key-{active_language} button,
            [data-testid="stSidebar"] .st-key-{active_theme} button {{
              border-color: rgba(190, 255, 243, 0.92) !important;
              box-shadow: 0 9px 22px rgba(5, 11, 28, 0.28) !important;
            }}
            </style>""",
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption(t("input_step"))
        modes = {t("bundled"): "bundled", t("custom"): "custom"}
        selected_mode = st.radio(t("input_source"), list(modes), label_visibility="collapsed")
        if modes[selected_mode] == "bundled":
            st.success(t("bundled_ready"))
            return InputPaths.from_data_directory(DEFAULT_DATA_DIR)

        st.caption(t("upload_help"))
        source = st.file_uploader(t("source_file"), type=["xlsx", "csv"])
        destination = st.file_uploader(t("destination_file"), type=["xlsx", "csv"])
        mapping = st.file_uploader(t("mapping_file"), type=["xlsx"])
        job_details = st.file_uploader(t("job_file"), type=["xlsx", "csv"])
        employment_reasons = st.file_uploader(t("reasons_file"), type=["xlsx", "csv"])
        uploads = [source, destination, mapping, job_details, employment_reasons]
        if not all(uploads):
            st.warning(t("files_required"))
            return None
        return InputPaths(*(_to_buffer(upload) for upload in uploads if upload is not None))


def _hero(locale: str, run: ReconciliationRun | None) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    state = t("hero_results") if run is not None else t("hero_ready")
    st.markdown(
        f'<section class="hero"><div class="eyebrow"><span class="live-dot"></span>{state}</div><h1>{t("hero_title")}</h1><p>{t("hero_copy")}</p><div class="hero-pills"><span class="hero-pill">{t("pill_deterministic")}</span><span class="hero-pill">{t("pill_evidence")}</span><span class="hero-pill">{t("pill_private")}</span></div></section>',
        unsafe_allow_html=True,
    )


def _workflow(locale: str, run: ReconciliationRun | None) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    labels = [
        ("01", t("flow_input_title"), t("flow_input_copy")),
        ("02", t("flow_run_title"), t("flow_run_copy")),
        ("03", t("flow_triage_title"), t("flow_triage_copy")),
        ("04", t("flow_export_title"), t("flow_export_copy")),
    ]
    current = 2 if run is not None else 1
    steps = "".join(
        f'<div class="flow-step {"current" if index == current else ""}"><div class="flow-number">{number}</div><div class="flow-title">{title}</div><div class="flow-copy">{copy}</div></div>'
        for index, (number, title, copy) in enumerate(labels, start=1)
    )
    st.markdown(f'<div class="flow-track">{steps}</div>', unsafe_allow_html=True)


def _display_summary(run: ReconciliationRun, locale: str) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    summary = run.summary.set_index("verdict")["field_comparisons_or_cases"]
    cards = [
        ("Actual anomaly", "alert", t("actual_note")),
        ("Needs review", "review", t("review_note")),
        ("Justified difference", "rule", t("justified_note")),
        ("Match", "match", t("match_note")),
    ]
    st.markdown(f'<div class="section-kicker">{t("pulse_kicker")}</div><h2 class="section-title">{t("pulse_title")}</h2>', unsafe_allow_html=True)
    columns = st.columns(4)
    for column, (verdict, style, note) in zip(columns, cards):
        with column:
            st.markdown(
                f'<article class="metric-card metric-card--{style}"><div class="metric-label">{translate_value(locale, "verdict", verdict)}</div><div class="metric-value">{int(summary.get(verdict, 0))}</div><div class="metric-note">{note}</div></article>',
                unsafe_allow_html=True,
            )
    high_priority = int(run.cases["priority"].eq("High").sum())
    st.markdown(
        f'<div class="insight-panel"><div class="insight-orb">!</div><div><div class="insight-title">{t("start_title")}</div><div class="insight-copy">{t("start_copy", count=high_priority)}</div></div></div>',
        unsafe_allow_html=True,
    )


def _localized_explanation(case: pd.Series, locale: str) -> str:
    t = lambda key, **values: translate(locale, key, **values)
    method = case["decision_method"]
    if method == "direct comparison":
        return t("case_explanation_direct_match") if case["verdict"] == "Match" else t("case_explanation_direct_anomaly")
    if method == "deterministic business rule":
        if case["verdict"] == "Justified difference":
            return t("case_explanation_rule_match", rule_id=case["rule_ids"])
        if case["verdict"] == "Actual anomaly":
            return t("case_explanation_rule_anomaly", rule_id=case["rule_ids"])
        return t("case_explanation_rule_review", rule_id=case["rule_ids"])
    return t("case_explanation_matching")


def _localized_priority_reason(case: pd.Series, locale: str) -> str:
    """Describe priority from the published deterministic criteria."""

    if case["verdict"] == "Actual anomaly":
        return translate(locale, "priority_anomaly")
    if case["verdict"] == "Needs review":
        return translate(locale, "priority_review")
    if case["verdict"] == "Justified difference":
        return translate(locale, "priority_justified")
    return translate(locale, "priority_match")


def _evidence_value(value: object) -> object:
    """Expand JSON evidence when possible, leaving source values untouched."""

    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _filter_cases(cases: pd.DataFrame, locale: str) -> pd.DataFrame:
    t = lambda key, **values: translate(locale, key, **values)
    st.markdown(f'<div class="section-kicker">{t("triage_kicker")}</div><h2 class="section-title">{t("triage_title")}</h2>', unsafe_allow_html=True)
    with st.expander(t("tune_queue"), expanded=False):
        first, second = st.columns(2)
        with first:
            selected_verdicts = st.multiselect(
                t("verdict"), sorted(cases["verdict"].dropna().unique()), default=[value for value in ["Actual anomaly", "Needs review"] if value in set(cases["verdict"])], format_func=lambda value: translate_value(locale, "verdict", value)
            )
            selected_fields = st.multiselect(t("field"), sorted(cases["field"].dropna().unique()))
        with second:
            selected_priorities = st.multiselect(t("priority"), ["High", "Medium", "Low"], default=["High", "Medium"], format_func=lambda value: translate_value(locale, "priority", value))
            selected_rules = st.multiselect(t("rule"), sorted(value for value in cases["rule_ids"].dropna().unique() if value))
    filtered = cases.copy()
    if selected_verdicts:
        filtered = filtered.loc[filtered["verdict"].isin(selected_verdicts)]
    if selected_fields:
        filtered = filtered.loc[filtered["field"].isin(selected_fields)]
    if selected_rules:
        filtered = filtered.loc[filtered["rule_ids"].isin(selected_rules)]
    if selected_priorities:
        filtered = filtered.loc[filtered["priority"].isin(selected_priorities)]
    return filtered.reset_index(drop=True)


def _queue_table(cases: pd.DataFrame, locale: str) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    if cases.empty:
        st.info(t("empty_queue"))
        return
    st.caption(t("queue_count", count=len(cases)))
    columns = ["case_id", "record_identifier", "field", "verdict", "rule_ids", "priority", "explanation"]
    view = cases.loc[:, columns].copy()
    view["verdict"] = view["verdict"].map(lambda value: translate_value(locale, "verdict", value))
    view["priority"] = view["priority"].map(lambda value: translate_value(locale, "priority", value))
    view["explanation"] = cases.apply(lambda case: _localized_explanation(case, locale), axis=1)
    st.dataframe(
        view,
        column_config={
            "case_id": st.column_config.TextColumn(t("case"), width="medium"),
            "record_identifier": st.column_config.TextColumn(t("employee"), width="small"),
            "field": st.column_config.TextColumn(t("field"), width="small"),
            "verdict": st.column_config.TextColumn(t("verdict"), width="medium"),
            "rule_ids": st.column_config.TextColumn(t("rule"), width="medium"),
            "priority": st.column_config.TextColumn(t("priority"), width="small"),
            "explanation": st.column_config.TextColumn(t("why"), width="large"),
        },
        width="stretch",
        hide_index=True,
        height=min(460, 82 + len(view) * 37),
    )


def _case_details(cases: pd.DataFrame, locale: str) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    st.markdown(f'<div class="section-kicker">{t("evidence_kicker")}</div><h2 class="section-title">{t("evidence_title")}</h2>', unsafe_allow_html=True)
    if cases.empty:
        st.info(t("empty_evidence"))
        return
    choices = {f"{row.case_id} | {row.record_identifier or t('missing_id')} | {row.field}": row.case_id for row in cases.itertuples()}
    selected_label = st.selectbox(t("select_case"), list(choices), label_visibility="collapsed")
    case = cases.loc[cases["case_id"].eq(choices[selected_label])].iloc[0]
    status, method = st.columns([1, 2])
    status.metric(t("verdict"), translate_value(locale, "verdict", case["verdict"]))
    method.metric(t("decision_method"), translate_value(locale, "method", case["decision_method"]))
    source, destination = st.columns(2)
    with source:
        st.caption(t("source_evidence"))
        st.json({t("raw"): _evidence_value(case["source_value"]), t("normalized"): _evidence_value(case["source_normalized_value"]), t("row"): case["source_row"]})
    with destination:
        st.caption(t("destination_evidence"))
        st.json({t("raw"): _evidence_value(case["destination_value"]), t("normalized"): _evidence_value(case["destination_normalized_value"]), t("expected"): _evidence_value(case["expected_value"]), t("row"): case["destination_row"]})
    st.info(_localized_explanation(case, locale))
    with st.expander(t("supporting")):
        st.json({t("rule_ids"): case["rule_ids"], t("supporting_records"): _evidence_value(case["supporting_records"]), t("priority"): translate_value(locale, "priority", case["priority"]), t("priority_reason"): _localized_priority_reason(case, locale), t("ai_contributed"): case["ai_contributed"], t("ai_status"): t("not_configured") if case["ai_status"] == "not configured" else case["ai_status"]})


def _exports(run: ReconciliationRun, filtered: pd.DataFrame, locale: str) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    st.markdown(f'<div class="section-kicker">{t("handoff_kicker")}</div><h2 class="section-title">{t("handoff_title")}</h2>', unsafe_allow_html=True)
    csv_column, excel_column, audit_column = st.columns(3)
    csv_column.download_button(t("download_csv"), cases_to_csv(filtered), "corroboria_cases.csv", "text/csv", width="stretch")
    excel_column.download_button(t("download_excel"), run_to_excel(run), "corroboria_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    audit_column.download_button(t("download_audit"), audit_to_json(run), "corroboria_run_audit.json", "application/json", width="stretch")


def _feedback(cases: pd.DataFrame, locale: str) -> None:
    t = lambda key, **values: translate(locale, key, **values)
    st.markdown(f'<div class="section-kicker">{t("governance_kicker")}</div><h2 class="section-title">{t("governance_title")}</h2>', unsafe_allow_html=True)
    st.caption(t("feedback_caption"))
    with st.form("feedback_form", border=False):
        case_id = st.selectbox(t("case"), cases["case_id"].tolist())
        reviewer_verdict = st.selectbox(t("reviewer_verdict"), ["Match", "Justified difference", "Actual anomaly", "Needs review"], format_func=lambda value: translate_value(locale, "verdict", value))
        reason = st.text_area(t("feedback_reason"), placeholder=t("feedback_placeholder"))
        submitted = st.form_submit_button(t("save_feedback"))
    if submitted:
        if not reason.strip():
            st.warning(t("reason_required"))
            return
        original = cases.loc[cases["case_id"].eq(case_id), "verdict"].iloc[0]
        st.session_state.feedback.append({"case_id": case_id, "original_verdict": original, "reviewer_verdict": reviewer_verdict, "reason": reason.strip()})
        st.success(t("feedback_saved"))
    if st.session_state.feedback:
        feedback = pd.DataFrame(st.session_state.feedback)
        feedback_view = feedback.rename(columns={"case_id": t("case"), "original_verdict": t("original_verdict"), "reviewer_verdict": t("reviewer_verdict"), "reason": t("why")}).copy()
        feedback_view[t("original_verdict")] = feedback_view[t("original_verdict")].map(lambda value: translate_value(locale, "verdict", value))
        feedback_view[t("reviewer_verdict")] = feedback_view[t("reviewer_verdict")].map(lambda value: translate_value(locale, "verdict", value))
        st.dataframe(feedback_view, width="stretch", hide_index=True)
        st.download_button(t("download_feedback"), feedback.to_csv(index=False).encode("utf-8-sig"), "corroboria_feedback.csv", "text/csv")


def main() -> None:
    st.set_page_config(page_title="CorroborIA", page_icon="C", layout="wide", initial_sidebar_state="expanded")
    locale, theme = _initialise_preferences()
    _inject_theme(theme)
    if "run" not in st.session_state:
        st.session_state.run = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = []

    inputs = _sidebar(locale, theme)
    run: ReconciliationRun | None = st.session_state.run
    _hero(locale, run)
    _workflow(locale, run)
    run_column, privacy_column = st.columns([1, 2])
    with run_column:
        start = st.button(translate(locale, "run"), type="primary", disabled=inputs is None, width="stretch")
    with privacy_column:
        st.caption(translate(locale, "local_first"))
    if start:
        try:
            with st.spinner(translate(locale, "running")):
                st.session_state.run = run_reconciliation(inputs)
                st.session_state.feedback = []
            st.rerun()
        except InputValidationError as error:
            st.error(translate(locale, "validation_stopped"))
            st.code("\n".join(error.issues))
        except Exception as error:  # The detailed exception stays local to the reviewer.
            st.exception(error)

    run = st.session_state.run
    if run is None:
        st.markdown(f'<div class="insight-panel"><div class="insight-orb">C</div><div><div class="insight-title">{translate(locale, "ready_title")}</div><div class="insight-copy">{translate(locale, "ready_copy")}</div></div></div>', unsafe_allow_html=True)
        return

    overview_tab, queue_tab, governance_tab = st.tabs([translate(locale, "tab_overview"), translate(locale, "tab_queue"), translate(locale, "tab_governance")])
    with overview_tab:
        _display_summary(run, locale)
        st.caption(translate(locale, "count_caption"))
    with queue_tab:
        filtered = _filter_cases(run.cases, locale)
        _queue_table(filtered, locale)
        _case_details(filtered, locale)
        _exports(run, filtered, locale)
    with governance_tab:
        _feedback(run.cases, locale)
        with st.expander(translate(locale, "mapping_evidence")):
            st.dataframe(run.mapping, width="stretch", hide_index=True)
            st.json(run.audit)


if __name__ == "__main__":
    main()
