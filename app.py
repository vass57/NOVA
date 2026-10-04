"""Bilingual Streamlit interface for CorroborIA."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from corroboria.export import (
    audit_to_json,
    cases_to_csv,
    run_to_excel,
)
from corroboria.i18n import (
    translate,
    translate_value,
)
from corroboria.pipeline import (
    InputPaths,
    InputValidationError,
    ReconciliationRun,
    run_reconciliation,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


# ============================================================
# SESSION PREFERENCES
# ============================================================

def _set_preference(
    name: str,
    value: str,
) -> None:
    st.session_state[name] = value


def _initialise_preferences() -> tuple[str, str]:
    if "locale" not in st.session_state:
        st.session_state.locale = "en"

    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = "dark"

    return (
        st.session_state.locale,
        st.session_state.ui_theme,
    )


# ============================================================
# THEME VARIABLES
# ============================================================

def _theme_variables(
    theme: str,
) -> str:

    if theme == "dark":
        return """
        :root {
            --canvas: #08111f;
            --canvas-end: #101d34;

            --ink: #f5f8ff;
            --muted: #b7c4d6;

            --surface: rgba(20, 35, 59, 0.94);
            --surface-raised: #1a2c49;
            --control: #10243f;

            --line: rgba(202, 219, 241, 0.20);
            --line-strong: rgba(80, 227, 201, 0.48);

            --teal: #18c7af;
            --teal-dark: #7bf1df;

            --indigo: #8b86ff;
            --coral: #ff7c8c;
            --amber: #ffc563;

            --soft-teal: rgba(18, 199, 175, 0.13);
            --shadow: rgba(0, 0, 0, 0.30);
        }
        """

    return """
    :root {
        --canvas: #f7fbff;
        --canvas-end: #edf3fa;

        --ink: #10172a;
        --muted: #52647c;

        --surface: rgba(255, 255, 255, 0.95);
        --surface-raised: #ffffff;
        --control: #ffffff;

        --line: rgba(15, 23, 42, 0.13);
        --line-strong: rgba(15, 174, 154, 0.48);

        --teal: #0fae9a;
        --teal-dark: #087f72;

        --indigo: #4f46e5;
        --coral: #ef5f72;
        --amber: #f4a83b;

        --soft-teal: rgba(15, 174, 154, 0.10);
        --shadow: rgba(25, 48, 85, 0.14);
    }
    """


# ============================================================
# CSS
# ============================================================

def _inject_theme(
    theme: str,
) -> None:

    css = """
    /* ======================================================
       APP
       ====================================================== */

    .stApp,
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(
                circle at 4% 1%,
                color-mix(in srgb, var(--teal) 17%, transparent),
                transparent 25rem
            ),
            radial-gradient(
                circle at 97% 2%,
                color-mix(in srgb, var(--indigo) 15%, transparent),
                transparent 28rem
            ),
            linear-gradient(
                135deg,
                var(--canvas) 0%,
                var(--canvas-end) 100%
            );

        color: var(--ink);
    }

    .block-container {
        max-width: 1380px;
        padding-top: 1.35rem;
        padding-bottom: 3.5rem;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }


    /* ======================================================
       TEXT
       ====================================================== */

    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"]
    [data-testid="stMarkdownContainer"] {
        color: var(--ink);
    }

    [data-testid="stCaptionContainer"] p {
        color: var(--muted) !important;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #0e1930 0%,
                #172745 54%,
                #087f72 160%
            );

        border-right:
            1px solid rgba(255, 255, 255, 0.11);
    }

    [data-testid="stSidebar"] * {
        color: #effaff;
    }

    [data-testid="stSidebar"]
    [data-testid="stCaptionContainer"] p {
        color: #b9cddd !important;
    }

    [data-testid="stSidebar"] hr {
        border-color:
            rgba(255, 255, 255, 0.10) !important;
    }


    /* ======================================================
       SIDEBAR BUTTONS
       ====================================================== */

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button {
        min-height: 2.75rem;
        border-radius: 12px;
        font-weight: 760;

        transition:
            transform 180ms ease,
            box-shadow 180ms ease,
            border-color 180ms ease,
            background 180ms ease;
    }

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="secondary"] {
        background:
            rgba(255, 255, 255, 0.08) !important;

        border:
            1px solid
            rgba(255, 255, 255, 0.25) !important;

        color: #effaff !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="secondary"] *,
    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="secondary"] p,
    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="secondary"] span {
        color: #effaff !important;
    }

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="secondary"]:hover {
        background:
            rgba(255, 255, 255, 0.16) !important;

        border-color:
            rgba(130, 240, 220, 0.65) !important;

        transform: translateY(-2px);
    }

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="primary"] {
        background:
            linear-gradient(
                120deg,
                #0fae9a,
                #5360db
            ) !important;

        border:
            1px solid
            rgba(180, 255, 245, 0.35) !important;

        color: white !important;

        box-shadow:
            0 9px 22px
            rgba(5, 11, 28, 0.28) !important;
    }

    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="primary"] *,
    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="primary"] p,
    [data-testid="stSidebar"]
    [data-testid="stButton"] > button[kind="primary"] span {
        color: white !important;
    }


    /* ======================================================
       SIDEBAR INPUTS
       ====================================================== */

    [data-testid="stSidebar"]
    [data-testid="stRadio"] label,
    [data-testid="stSidebar"]
    [data-testid="stRadio"] p {
        color: #f1f7ff !important;
        font-weight: 650;
    }

    [data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] {
        background:
            rgba(255, 255, 255, 0.08);

        border:
            1px dashed
            rgba(255, 255, 255, 0.36);

        border-radius: 16px;
    }

    [data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] * {
        color: #effaff !important;
    }

    [data-testid="stSidebar"]
    [data-testid="stAlert"] {
        background:
            rgba(15, 174, 154, 0.18) !important;

        border:
            1px solid
            rgba(72, 230, 205, 0.15);

        border-radius: 12px;
    }

    [data-testid="stSidebar"]
    [data-testid="stAlert"] * {
        color: #effaff !important;
    }


    /* ======================================================
       BRAND
       ====================================================== */

    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.8rem;

        margin:
            0.5rem 0 1.45rem;
    }

    .brand-mark {
        display: grid;
        place-items: center;

        width: 2.65rem;
        height: 2.65rem;

        border-radius: 15px;

        color: white;

        font-size: 1.18rem;
        font-weight: 850;

        background:
            linear-gradient(
                135deg,
                #25d0b5,
                #5d62ef
            );

        box-shadow:
            0 12px 28px
            rgba(0, 0, 0, 0.28);
    }

    .brand-name {
        font-size: 1.14rem;
        font-weight: 790;
        letter-spacing: -0.02em;
    }

    .brand-subtitle {
        color: #acc4d8;

        font-size: 0.69rem;
        font-weight: 700;

        letter-spacing: 0.11em;

        margin-top: 0.1rem;
    }

    .pref-label {
        color: #b9cddd;

        font-size: 0.67rem;
        font-weight: 800;

        letter-spacing: 0.10em;
        text-transform: uppercase;

        margin:
            1.1rem 0 0.32rem;
    }


    /* ======================================================
       HERO
       ====================================================== */

    .hero {
        position: relative;
        overflow: hidden;

        padding:
            clamp(
                1.6rem,
                4vw,
                3.15rem
            );

        border:
            1px solid
            rgba(255, 255, 255, 0.55);

        border-radius: 28px;

        background:
            linear-gradient(
                125deg,
                #15213d 0%,
                #22355e 49%,
                #164a5b 110%
            );

        color: #f8fbff;

        box-shadow:
            0 26px 62px
            var(--shadow);
    }

    .hero::before,
    .hero::after {
        content: "";

        position: absolute;

        border-radius: 999px;
        pointer-events: none;

        opacity: 0.62;
    }

    .hero::before {
        right: -7rem;
        top: -10rem;

        width: 21rem;
        height: 21rem;

        background:
            rgba(35, 219, 190, 0.25);
    }

    .hero::after {
        left: 48%;
        bottom: -15rem;

        width: 24rem;
        height: 24rem;

        background:
            rgba(110, 99, 255, 0.29);
    }

    .hero > * {
        position: relative;
        z-index: 1;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;

        margin-bottom: 0.78rem;

        padding:
            0.35rem 0.68rem;

        border:
            1px solid
            rgba(213, 255, 248, 0.27);

        border-radius: 999px;

        background:
            rgba(5, 16, 35, 0.22);

        color: #c9fff4;

        font-size: 0.70rem;
        font-weight: 780;

        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .live-dot {
        width: 0.48rem;
        height: 0.48rem;

        border-radius: 50%;

        background: #53f2d8;
    }

    .hero h1 {
        max-width: 800px;
        margin: 0;

        color: white;

        font-size:
            clamp(
                2rem,
                5vw,
                4rem
            );

        font-weight: 800;
        letter-spacing: -0.058em;
        line-height: 0.98;
    }

    .hero p {
        max-width: 680px;

        margin:
            1rem 0 0;

        color: #d6e6f5;

        font-size:
            clamp(
                0.96rem,
                1.5vw,
                1.1rem
            );

        line-height: 1.65;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;

        margin-top: 1.3rem;
    }

    .hero-pill {
        padding:
            0.42rem 0.72rem;

        border:
            1px solid
            rgba(255, 255, 255, 0.15);

        border-radius: 999px;

        background:
            rgba(255, 255, 255, 0.12);

        color: #effbff;

        font-size: 0.76rem;
    }


    /* ======================================================
       WORKFLOW
       ====================================================== */

    .flow-track {
        display: grid;

        grid-template-columns:
            repeat(
                4,
                minmax(0, 1fr)
            );

        gap: 0.65rem;

        margin:
            1.15rem 0 1.7rem;
    }

    .flow-step {
        min-width: 0;

        padding: 0.88rem;

        border:
            1px solid
            var(--line);

        border-radius: 16px;

        background:
            var(--surface);
    }

    .flow-step.current {
        border-color:
            var(--line-strong);

        background:
            linear-gradient(
                135deg,
                var(--soft-teal),
                var(--surface)
            );
    }

    .flow-number {
        display: inline-grid;
        place-items: center;

        width: 1.58rem;
        height: 1.58rem;

        margin-bottom: 0.45rem;

        border-radius: 50%;

        background:
            color-mix(
                in srgb,
                var(--muted) 17%,
                transparent
            );

        color: var(--muted);

        font-size: 0.70rem;
        font-weight: 850;
    }

    .flow-step.current
    .flow-number {
        background:
            var(--teal);

        color: white;
    }

    .flow-title {
        color: var(--ink);

        font-size: 0.84rem;
        font-weight: 780;
    }

    .flow-copy {
        margin-top: 0.17rem;

        color: var(--muted);

        font-size: 0.72rem;
        line-height: 1.38;
    }


    /* ======================================================
       SECTION TITLES
       ====================================================== */

    .section-kicker {
        margin:
            1.55rem 0 0.26rem;

        color: var(--teal-dark);

        font-size: 0.69rem;
        font-weight: 850;

        letter-spacing: 0.11em;
        text-transform: uppercase;
    }

    .section-title {
        margin:
            0 0 0.9rem;

        color: var(--ink);

        font-size:
            clamp(
                1.35rem,
                2.4vw,
                1.85rem
            );

        font-weight: 790;
        letter-spacing: -0.038em;
    }


    /* ======================================================
       SUMMARY METRIC CARDS
       ====================================================== */

    .metric-card {
        position: relative;
        overflow: hidden;

        min-height: 132px;

        padding:
            1rem 1.05rem;

        border:
            1px solid
            var(--line);

        border-radius: 18px;

        background:
            var(--surface);

        box-shadow:
            0 12px 25px
            rgba(15, 23, 42, 0.055);
    }

    .metric-card::before {
        content: "";

        position: absolute;

        inset:
            0 auto 0 0;

        width: 4px;

        background:
            var(--accent);
    }

    .metric-card--alert {
        --accent:
            var(--coral);
    }

    .metric-card--review {
        --accent:
            var(--amber);
    }

    .metric-card--rule {
        --accent:
            var(--indigo);
    }

    .metric-card--match {
        --accent:
            var(--teal);
    }

    .metric-label {
        color: var(--muted);

        font-size: 0.75rem;
        font-weight: 720;
    }

    .metric-value {
        margin:
            0.3rem 0;

        color: var(--ink);

        font-size: 2.15rem;
        font-weight: 830;

        letter-spacing: -0.065em;
    }

    .metric-note {
        color: var(--muted);

        font-size: 0.70rem;
    }


    /* ======================================================
       CASE META CARDS
       ====================================================== */

    .case-meta-grid {
        display: grid;

        grid-template-columns:
            repeat(
                3,
                minmax(0, 1fr)
            );

        gap: 0.85rem;

        margin:
            0.8rem 0 1.35rem;
    }

    .case-meta-card {
        padding:
            1rem 1.05rem;

        border:
            1px solid
            var(--line);

        border-radius: 16px;

        background:
            var(--surface);

        min-height: 108px;
    }

    .case-meta-label {
        color: var(--muted);

        font-size: 0.74rem;
        font-weight: 760;

        margin-bottom: 0.42rem;
    }

    .case-meta-value {
        color: var(--ink);

        font-size:
            clamp(
                1.05rem,
                2vw,
                1.55rem
            );

        font-weight: 790;

        line-height: 1.18;

        overflow-wrap: anywhere;
    }


    /* ======================================================
       INSIGHT PANEL
       ====================================================== */

    .insight-panel {
        display: flex;
        align-items: center;
        gap: 1rem;

        padding:
            1rem 1.1rem;

        border:
            1px solid
            color-mix(
                in srgb,
                var(--teal) 22%,
                var(--line)
            );

        border-radius: 18px;

        background:
            linear-gradient(
                110deg,
                var(--soft-teal),
                var(--surface)
            );

        color: var(--ink);
    }

    .insight-orb {
        display: grid;
        flex: 0 0 auto;
        place-items: center;

        width: 2.7rem;
        height: 2.7rem;

        border-radius: 14px;

        background:
            linear-gradient(
                145deg,
                #13b8a2,
                #5a58db
            );

        color: white;

        font-size: 1.08rem;
        font-weight: 800;
    }

    .insight-title {
        font-size: 0.9rem;
        font-weight: 800;
    }

    .insight-copy {
        margin-top: 0.12rem;

        color: var(--muted);

        font-size: 0.8rem;
        line-height: 1.46;
    }


    /* ======================================================
       MAIN BUTTONS
       ====================================================== */

    [data-testid="stAppViewContainer"]
    [data-testid="stButton"] > button,
    [data-testid="stAppViewContainer"]
    [data-testid="stDownloadButton"] > button {
        min-height: 2.7rem;

        border-radius: 12px;

        font-weight: 730;
    }

    [data-testid="stAppViewContainer"]
    [data-testid="stButton"]
    > button[kind="primary"] {
        min-height: 3rem;

        border: 0;

        background:
            linear-gradient(
                110deg,
                #0a9b8b,
                #3955dc 58%,
                #0a9b8b
            );

        color: white !important;

        box-shadow:
            0 12px 24px
            rgba(32, 82, 177, 0.24);
    }

    [data-testid="stAppViewContainer"]
    [data-testid="stButton"]
    > button[kind="primary"] * {
        color: white !important;
    }

    [data-testid="stDownloadButton"] > button {
        background:
            var(--surface) !important;

        border-color:
            var(--line) !important;

        color:
            var(--ink) !important;
    }


    /* ======================================================
       FORM CONTROLS
       ====================================================== */

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-testid="stTextArea"] textarea {
        background:
            var(--control) !important;

        color:
            var(--ink) !important;

        border-color:
            var(--line) !important;

        border-radius:
            12px !important;
    }

    [data-baseweb="select"] *,
    [data-baseweb="input"] input,
    [data-testid="stTextArea"] textarea {
        color:
            var(--ink) !important;
    }


    /* ======================================================
       DATA TABLES / EXPANDERS / TABS
       ====================================================== */

    [data-testid="stDataFrame"] {
        border:
            1px solid
            var(--line);

        border-radius: 17px;

        overflow: hidden;
    }

    [data-testid="stExpander"] {
        border:
            1px solid
            var(--line);

        border-radius: 15px;

        background:
            var(--surface);
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-list"] {
        gap: 0.42rem;

        border-bottom: 0;

        overflow-x: auto;
    }

    [data-testid="stTabs"]
    button[data-baseweb="tab"] {
        height: 2.65rem;

        padding:
            0 1rem;

        border:
            1px solid
            var(--line);

        border-radius: 12px;

        background:
            var(--surface);

        color:
            var(--muted);

        font-size: 0.81rem;
        font-weight: 750;
    }

    [data-testid="stTabs"]
    button[aria-selected="true"] {
        border-color:
            var(--line-strong);

        background:
            var(--soft-teal);

        color:
            var(--teal-dark);
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-highlight"] {
        display: none;
    }


    /* ======================================================
       RESPONSIVE
       ====================================================== */

    @media(max-width: 800px) {

        .flow-track {
            grid-template-columns:
                1fr 1fr;
        }

        .case-meta-grid {
            grid-template-columns:
                1fr;
        }
    }

    @media(max-width: 520px) {

        .flow-track {
            grid-template-columns:
                1fr;
        }

        .hero h1 {
            font-size: 2rem;
        }
    }
    """

    st.markdown(
        "<style>"
        + _theme_variables(theme)
        + css
        + "</style>",
        unsafe_allow_html=True,
    )


# ============================================================
# UPLOAD HELPERS
# ============================================================

def _to_buffer(
    upload,
) -> BytesIO:

    buffer = BytesIO(
        upload.getvalue()
    )

    buffer.name = upload.name

    return buffer


# ============================================================
# SIDEBAR
# ============================================================

def _sidebar(
    locale: str,
    theme: str,
) -> InputPaths | None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    with st.sidebar:

        st.markdown(
            (
                '<div class="brand-lockup">'
                '<div class="brand-mark">C</div>'
                '<div>'
                '<div class="brand-name">CorroborIA</div>'
                f'<div class="brand-subtitle">{t("studio")}</div>'
                '</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="pref-label">{t("language")}</div>',
            unsafe_allow_html=True,
        )

        language_columns = st.columns(
            2
        )

        language_columns[0].button(
            "EN",
            type=(
                "primary"
                if locale == "en"
                else "secondary"
            ),
            width="stretch",
            key="language_en",
            on_click=_set_preference,
            args=(
                "locale",
                "en",
            ),
        )

        language_columns[1].button(
            "FR",
            type=(
                "primary"
                if locale == "fr"
                else "secondary"
            ),
            width="stretch",
            key="language_fr",
            on_click=_set_preference,
            args=(
                "locale",
                "fr",
            ),
        )

        st.markdown(
            f'<div class="pref-label">{t("appearance")}</div>',
            unsafe_allow_html=True,
        )

        appearance_columns = st.columns(
            2
        )

        appearance_columns[0].button(
            t(
                "light"
            ),
            type=(
                "primary"
                if theme == "light"
                else "secondary"
            ),
            width="stretch",
            key="theme_light",
            on_click=_set_preference,
            args=(
                "ui_theme",
                "light",
            ),
        )

        appearance_columns[1].button(
            t(
                "dark"
            ),
            type=(
                "primary"
                if theme == "dark"
                else "secondary"
            ),
            width="stretch",
            key="theme_dark",
            on_click=_set_preference,
            args=(
                "ui_theme",
                "dark",
            ),
        )

        st.divider()

        st.caption(
            t(
                "input_step"
            )
        )

        modes = {
            t(
                "bundled"
            ):
                "bundled",

            t(
                "custom"
            ):
                "custom",
        }

        selected_mode = st.radio(
            t(
                "input_source"
            ),
            list(
                modes
            ),
            label_visibility="collapsed",
        )

        if (
            modes[
                selected_mode
            ]
            ==
            "bundled"
        ):

            st.success(
                t(
                    "bundled_ready"
                )
            )

            return InputPaths.from_data_directory(
                DEFAULT_DATA_DIR
            )

        st.caption(
            t(
                "upload_help"
            )
        )

        source = st.file_uploader(
            t(
                "source_file"
            ),
            type=[
                "xlsx",
                "csv",
            ],
        )

        destination = st.file_uploader(
            t(
                "destination_file"
            ),
            type=[
                "xlsx",
                "csv",
            ],
        )

        mapping = st.file_uploader(
            t(
                "mapping_file"
            ),
            type=[
                "xlsx",
            ],
        )

        job_details = st.file_uploader(
            t(
                "job_file"
            ),
            type=[
                "xlsx",
                "csv",
            ],
        )

        employment_reasons = st.file_uploader(
            t(
                "reasons_file"
            ),
            type=[
                "xlsx",
                "csv",
            ],
        )

        uploads = [
            source,
            destination,
            mapping,
            job_details,
            employment_reasons,
        ]

        if not all(
            uploads
        ):

            st.warning(
                t(
                    "files_required"
                )
            )

            return None

        return InputPaths(
            source=_to_buffer(
                source
            ),
            destination=_to_buffer(
                destination
            ),
            mapping=_to_buffer(
                mapping
            ),
            job_details=_to_buffer(
                job_details
            ),
            employment_reasons=_to_buffer(
                employment_reasons
            ),
        )


# ============================================================
# HERO
# ============================================================

def _hero(
    locale: str,
    run: ReconciliationRun | None,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    state = (
        t(
            "hero_results"
        )
        if run is not None
        else
        t(
            "hero_ready"
        )
    )

    st.markdown(
        (
            '<section class="hero">'

            '<div class="eyebrow">'
            '<span class="live-dot"></span>'
            f'{state}'
            '</div>'

            f'<h1>{t("hero_title")}</h1>'

            f'<p>{t("hero_copy")}</p>'

            '<div class="hero-pills">'

            f'<span class="hero-pill">'
            f'{t("pill_deterministic")}'
            '</span>'

            f'<span class="hero-pill">'
            f'{t("pill_ai")}'
            '</span>'

            f'<span class="hero-pill">'
            f'{t("pill_evidence")}'
            '</span>'

            f'<span class="hero-pill">'
            f'{t("pill_private")}'
            '</span>'

            '</div>'
            '</section>'
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# WORKFLOW
# ============================================================

def _workflow(
    locale: str,
    run: ReconciliationRun | None,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    labels = [
        (
            "01",
            t(
                "flow_input_title"
            ),
            t(
                "flow_input_copy"
            ),
        ),
        (
            "02",
            t(
                "flow_run_title"
            ),
            t(
                "flow_run_copy"
            ),
        ),
        (
            "03",
            t(
                "flow_triage_title"
            ),
            t(
                "flow_triage_copy"
            ),
        ),
        (
            "04",
            t(
                "flow_export_title"
            ),
            t(
                "flow_export_copy"
            ),
        ),
    ]

    current = (
        3
        if run is not None
        else
        2
    )

    steps = "".join(
        (
            f'<div class="flow-step '
            f'{"current" if index == current else ""}">'

            f'<div class="flow-number">'
            f'{number}'
            '</div>'

            f'<div class="flow-title">'
            f'{title}'
            '</div>'

            f'<div class="flow-copy">'
            f'{copy}'
            '</div>'

            '</div>'
        )

        for index, (
            number,
            title,
            copy,
        )
        in enumerate(
            labels,
            start=1,
        )
    )

    st.markdown(
        f'<div class="flow-track">{steps}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# SUMMARY
# ============================================================

def _display_summary(
    run: ReconciliationRun,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    summary = (
        run.summary
        .set_index(
            "verdict"
        )[
            "field_comparisons_or_cases"
        ]
    )

    cards = [
        (
            "Actual anomaly",
            "alert",
            t(
                "actual_note"
            ),
        ),
        (
            "Needs review",
            "review",
            t(
                "review_note"
            ),
        ),
        (
            "Justified difference",
            "rule",
            t(
                "justified_note"
            ),
        ),
        (
            "Match",
            "match",
            t(
                "match_note"
            ),
        ),
    ]

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("pulse_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("pulse_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    columns = st.columns(
        4
    )

    for column, (
        verdict,
        style,
        note,
    ) in zip(
        columns,
        cards,
    ):

        localized_verdict = translate_value(
            locale,
            "verdict",
            verdict,
        )

        value = int(
            summary.get(
                verdict,
                0,
            )
        )

        with column:

            st.markdown(
                (
                    f'<article '
                    f'class="metric-card metric-card--{style}">'

                    f'<div class="metric-label">'
                    f'{localized_verdict}'
                    '</div>'

                    f'<div class="metric-value">'
                    f'{value}'
                    '</div>'

                    f'<div class="metric-note">'
                    f'{note}'
                    '</div>'

                    '</article>'
                ),
                unsafe_allow_html=True,
            )

    high_priority = int(
        run.cases[
            "priority"
        ].eq(
            "High"
        ).sum()
    )

    st.markdown(
        (
            '<div class="insight-panel">'

            '<div class="insight-orb">'
            '!'
            '</div>'

            '<div>'

            f'<div class="insight-title">'
            f'{t("start_title")}'
            '</div>'

            f'<div class="insight-copy">'
            f'{t("start_copy", count=high_priority)}'
            '</div>'

            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        t(
            "count_caption"
        )
    )


# ============================================================
# GENERIC HELPERS
# ============================================================

def _evidence_value(
    value: object,
) -> object:

    if not isinstance(
        value,
        str,
    ):
        return value

    try:
        return json.loads(
            value
        )

    except json.JSONDecodeError:
        return value


def _is_missing(
    value: object,
) -> bool:

    if value is None:
        return True

    try:
        return bool(
            pd.isna(
                value
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return False


def _supporting_dictionary(
    case: pd.Series,
) -> dict:

    value = case.get(
        "supporting_records"
    )

    if isinstance(
        value,
        dict,
    ):
        return value

    if isinstance(
        value,
        str,
    ):

        try:
            parsed = json.loads(
                value
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

        except json.JSONDecodeError:
            pass

    return {}


def _comparison_type(
    case: pd.Series,
) -> str:

    supporting = _supporting_dictionary(
        case
    )

    return str(
        supporting.get(
            "comparison_type",
            "",
        )
    )


def _friendly_field(
    value: object,
    locale: str,
) -> str:

    raw = str(
        value
    )

    if raw == "__ASSIGNMENT__":

        return (
            "Affectation"
            if locale == "fr"
            else
            "Assignment"
        )

    return raw


# ============================================================
# STRUCTURAL EXPLANATIONS
# ============================================================

def _structural_explanation(
    case: pd.Series,
    locale: str,
) -> str | None:

    comparison_type = _comparison_type(
        case
    )

    if locale == "fr":

        messages = {

            "SOURCE_ONLY_ASSIGNMENT":
                (
                    "Une affectation existe dans le "
                    "Système A, mais aucune affectation "
                    "correspondante n'existe dans le "
                    "Système B."
                ),

            "DESTINATION_ONLY_ASSIGNMENT":
                (
                    "Une affectation existe dans le "
                    "Système B, mais aucune affectation "
                    "correspondante n'existe dans le "
                    "Système A."
                ),

            "AMBIGUOUS_ASSIGNMENT_MATCH":
                (
                    "Plusieurs affectations candidates "
                    "existent dans les deux systèmes. "
                    "Les règles déterministes ne peuvent "
                    "pas sélectionner un appariement unique."
                ),
        }

    else:

        messages = {

            "SOURCE_ONLY_ASSIGNMENT":
                (
                    "An assignment exists in System A, "
                    "but no corresponding assignment "
                    "exists in System B."
                ),

            "DESTINATION_ONLY_ASSIGNMENT":
                (
                    "An assignment exists in System B, "
                    "but no corresponding assignment "
                    "exists in System A."
                ),

            "AMBIGUOUS_ASSIGNMENT_MATCH":
                (
                    "Multiple candidate assignments exist "
                    "in both systems. Deterministic rules "
                    "cannot select one unique matching."
                ),
        }

    return messages.get(
        comparison_type
    )


# ============================================================
# CASE EXPLANATIONS
# ============================================================

def _localized_explanation(
    case: pd.Series,
    locale: str,
) -> str:

    structural = _structural_explanation(
        case,
        locale,
    )

    if structural:
        return structural

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    method = str(
        case[
            "decision_method"
        ]
    )

    verdict = str(
        case[
            "verdict"
        ]
    )

    if (
        verdict
        ==
        "Justified difference"
    ):

        return t(
            "case_explanation_normalized"
        )

    if (
        method
        ==
        "direct comparison"
    ):

        if (
            verdict
            ==
            "Match"
        ):

            return t(
                "case_explanation_direct_match"
            )

        return t(
            "case_explanation_direct_anomaly"
        )

    if (
        method
        ==
        "deterministic business rule"
    ):

        if (
            verdict
            ==
            "Match"
        ):

            return t(
                "case_explanation_rule_match",
                rule_id=case[
                    "rule_ids"
                ],
            )

        if (
            verdict
            ==
            "Actual anomaly"
        ):

            return t(
                "case_explanation_rule_anomaly",
                rule_id=case[
                    "rule_ids"
                ],
            )

        return t(
            "case_explanation_rule_review",
            rule_id=case[
                "rule_ids"
            ],
        )

    return t(
        "case_explanation_matching"
    )


def _localized_priority_reason(
    case: pd.Series,
    locale: str,
) -> str:

    verdict = str(
        case[
            "verdict"
        ]
    )

    if verdict == "Actual anomaly":

        return translate(
            locale,
            "priority_anomaly",
        )

    if verdict == "Needs review":

        return translate(
            locale,
            "priority_review",
        )

    if verdict == "Justified difference":

        return translate(
            locale,
            "priority_justified",
        )

    return translate(
        locale,
        "priority_match",
    )


# ============================================================
# AI LABEL LOCALIZATION
# ============================================================

def _localized_ai_priority(
    value: object,
    locale: str,
) -> str:

    raw = str(
        value
    )

    if locale == "fr":

        mapping = {
            "CRITIQUE":
                "Critique",

            "ÉLEVÉE":
                "Élevée",

            "MOYENNE":
                "Moyenne",

            "FAIBLE":
                "Faible",
        }

    else:

        mapping = {
            "CRITIQUE":
                "Critical",

            "ÉLEVÉE":
                "High",

            "MOYENNE":
                "Medium",

            "FAIBLE":
                "Low",
        }

    return mapping.get(
        raw,
        raw,
    )


def _localized_pattern(
    value: object,
    locale: str,
) -> str:

    raw = str(
        value
    )

    if locale == "fr":

        mapping = {
            "SYSTEMATIQUE":
                "Systématique",

            "RECURRENT":
                "Récurrent",

            "ISOLE":
                "Isolé",
        }

    else:

        mapping = {
            "SYSTEMATIQUE":
                "Systematic",

            "RECURRENT":
                "Recurrent",

            "ISOLE":
                "Isolated",
        }

    return mapping.get(
        raw,
        raw,
    )


def _localized_recommendation(
    value: object,
    locale: str,
) -> str:

    raw = str(
        value
    )

    if locale == "fr":

        mapping = {
            "PROPOSITION_IA":
                "Proposition IA",

            "CANDIDAT_ALTERNATIF":
                "Candidat alternatif",

            "REVUE_HUMAINE":
                "Revue humaine",
        }

    else:

        mapping = {
            "PROPOSITION_IA":
                "AI proposal",

            "CANDIDAT_ALTERNATIF":
                "Alternative candidate",

            "REVUE_HUMAINE":
                "Human review",
        }

    return mapping.get(
        raw,
        raw,
    )


# ============================================================
# FILTER CASES
# ============================================================

def _filter_cases(
    cases: pd.DataFrame,
    locale: str,
) -> pd.DataFrame:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("triage_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("triage_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    with st.expander(
        t(
            "tune_queue"
        ),
        expanded=False,
    ):

        first, second = st.columns(
            2
        )

        with first:

            verdict_values = sorted(
                cases[
                    "verdict"
                ]
                .dropna()
                .unique()
            )

            selected_verdicts = st.multiselect(
                t(
                    "verdict"
                ),
                verdict_values,
                default=[
                    value
                    for value
                    in [
                        "Actual anomaly",
                        "Needs review",
                    ]
                    if value
                    in set(
                        verdict_values
                    )
                ],
                format_func=lambda value:
                    translate_value(
                        locale,
                        "verdict",
                        value,
                    ),
            )

            selected_fields = st.multiselect(
                t(
                    "field"
                ),
                sorted(
                    cases[
                        "field"
                    ]
                    .dropna()
                    .unique()
                ),
                format_func=lambda value:
                    _friendly_field(
                        value,
                        locale,
                    ),
            )

        with second:

            selected_priorities = st.multiselect(
                t(
                    "priority"
                ),
                [
                    "High",
                    "Medium",
                    "Low",
                ],
                default=[
                    "High",
                    "Medium",
                    "Low",
                ],
                format_func=lambda value:
                    translate_value(
                        locale,
                        "priority",
                        value,
                    ),
            )

            selected_rules = st.multiselect(
                t(
                    "rule"
                ),
                sorted(
                    value
                    for value
                    in cases[
                        "rule_ids"
                    ]
                    .dropna()
                    .unique()
                    if value
                ),
            )

    filtered = cases.copy()

    if selected_verdicts:

        filtered = filtered.loc[
            filtered[
                "verdict"
            ].isin(
                selected_verdicts
            )
        ]

    if selected_fields:

        filtered = filtered.loc[
            filtered[
                "field"
            ].isin(
                selected_fields
            )
        ]

    if selected_rules:

        filtered = filtered.loc[
            filtered[
                "rule_ids"
            ].isin(
                selected_rules
            )
        ]

    if selected_priorities:

        filtered = filtered.loc[
            filtered[
                "priority"
            ].isin(
                selected_priorities
            )
        ]

    return filtered.reset_index(
        drop=True
    )


# ============================================================
# QUEUE TABLE
# ============================================================

def _queue_table(
    cases: pd.DataFrame,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    if cases.empty:

        st.info(
            t(
                "empty_queue"
            )
        )

        return

    st.caption(
        t(
            "queue_count",
            count=len(
                cases
            ),
        )
    )

    columns = [
        "case_id",
        "record_identifier",
        "field",
        "verdict",
        "rule_ids",
        "priority",
        "pattern_type",
        "explanation",
    ]

    existing = [
        column
        for column
        in columns
        if column
        in cases.columns
    ]

    view = cases.loc[
        :,
        existing,
    ].copy()

    if "field" in view.columns:

        view[
            "field"
        ] = view[
            "field"
        ].map(
            lambda value:
                _friendly_field(
                    value,
                    locale,
                )
        )

    if "verdict" in view.columns:

        view[
            "verdict"
        ] = view[
            "verdict"
        ].map(
            lambda value:
                translate_value(
                    locale,
                    "verdict",
                    value,
                )
        )

    if "priority" in view.columns:

        view[
            "priority"
        ] = view[
            "priority"
        ].map(
            lambda value:
                translate_value(
                    locale,
                    "priority",
                    value,
                )
        )

    if "pattern_type" in view.columns:

        view[
            "pattern_type"
        ] = view[
            "pattern_type"
        ].map(
            lambda value:
                (
                    _localized_pattern(
                        value,
                        locale,
                    )
                    if not _is_missing(
                        value
                    )
                    else
                    ""
                )
        )

    view[
        "explanation"
    ] = cases.apply(
        lambda case:
            _localized_explanation(
                case,
                locale,
            ),
        axis=1,
    )

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
        height=min(
            500,
            82
            +
            len(
                view
            )
            *
            37,
        ),
    )


# ============================================================
# CASE META CARDS
# ============================================================

def _case_meta_cards(
    case: pd.Series,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    verdict = translate_value(
        locale,
        "verdict",
        str(
            case[
                "verdict"
            ]
        ),
    )

    method = translate_value(
        locale,
        "method",
        str(
            case[
                "decision_method"
            ]
        ),
    )

    priority = translate_value(
        locale,
        "priority",
        str(
            case[
                "priority"
            ]
        ),
    )

    st.markdown(
        (
            '<div class="case-meta-grid">'

            '<div class="case-meta-card">'
            f'<div class="case-meta-label">'
            f'{t("verdict")}'
            '</div>'
            f'<div class="case-meta-value">'
            f'{verdict}'
            '</div>'
            '</div>'

            '<div class="case-meta-card">'
            f'<div class="case-meta-label">'
            f'{t("decision_method")}'
            '</div>'
            f'<div class="case-meta-value">'
            f'{method}'
            '</div>'
            '</div>'

            '<div class="case-meta-card">'
            f'<div class="case-meta-label">'
            f'{t("priority")}'
            '</div>'
            f'<div class="case-meta-value">'
            f'{priority}'
            '</div>'
            '</div>'

            '</div>'
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# STRUCTURAL EVIDENCE
# ============================================================

def _structural_evidence(
    case: pd.Series,
    locale: str,
) -> None:

    comparison_type = _comparison_type(
        case
    )

    source_row = case.get(
        "source_row"
    )

    destination_row = case.get(
        "destination_row"
    )

    source_present = (
        not _is_missing(
            source_row
        )
    )

    destination_present = (
        not _is_missing(
            destination_row
        )
    )

    if locale == "fr":

        system_a = "SYSTÈME A"
        system_b = "SYSTÈME B"

        present_text = "Présente"
        missing_text = "Absente"
        ambiguous_text = "Plusieurs candidates"

        assignment_label = "Type d'affectation"
        row_label = "Ligne"

    else:

        system_a = "SYSTEM A"
        system_b = "SYSTEM B"

        present_text = "Present"
        missing_text = "Missing"
        ambiguous_text = "Multiple candidates"

        assignment_label = "Assignment type"
        row_label = "Row"

    source_column, destination_column = st.columns(
        2
    )

    with source_column:

        st.markdown(
            f"### {system_a}"
        )

        if (
            comparison_type
            ==
            "AMBIGUOUS_ASSIGNMENT_MATCH"
        ):

            st.info(
                ambiguous_text
            )

        elif source_present:

            st.success(
                present_text
            )

        else:

            st.error(
                missing_text
            )

        st.write(
            f"**{assignment_label}:** "
            f"{case.get('assignment_type')}"
        )

        if source_present:

            st.write(
                f"**{row_label}:** "
                f"{int(source_row)}"
            )

    with destination_column:

        st.markdown(
            f"### {system_b}"
        )

        if (
            comparison_type
            ==
            "AMBIGUOUS_ASSIGNMENT_MATCH"
        ):

            st.info(
                ambiguous_text
            )

        elif destination_present:

            st.success(
                present_text
            )

        else:

            st.error(
                missing_text
            )

        st.write(
            f"**{assignment_label}:** "
            f"{case.get('assignment_type')}"
        )

        if destination_present:

            st.write(
                f"**{row_label}:** "
                f"{int(destination_row)}"
            )


# ============================================================
# CASE DETAILS
# ============================================================

def _case_details(
    cases: pd.DataFrame,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("evidence_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("evidence_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    if cases.empty:

        st.info(
            t(
                "empty_evidence"
            )
        )

        return

    choices = {}

    for row in cases.itertuples():

        employee = (
            row.record_identifier
            if row.record_identifier
            else
            t(
                "missing_id"
            )
        )

        field = _friendly_field(
            row.field,
            locale,
        )

        label = (
            f"{row.case_id} | "
            f"{employee} | "
            f"{field}"
        )

        choices[
            label
        ] = row.case_id

    selected_label = st.selectbox(
        t(
            "select_case"
        ),
        list(
            choices
        ),
        label_visibility="collapsed",
    )

    case = cases.loc[
        cases[
            "case_id"
        ].eq(
            choices[
                selected_label
            ]
        )
    ].iloc[
        0
    ]

    _case_meta_cards(
        case,
        locale,
    )

    if (
        str(
            case.get(
                "field"
            )
        )
        ==
        "__ASSIGNMENT__"
    ):

        _structural_evidence(
            case,
            locale,
        )

    else:

        source_column, destination_column = st.columns(
            2
        )

        with source_column:

            st.caption(
                t(
                    "source_evidence"
                )
            )

            st.json(
                {
                    t(
                        "raw"
                    ):
                        _evidence_value(
                            case[
                                "source_value"
                            ]
                        ),

                    t(
                        "normalized"
                    ):
                        _evidence_value(
                            case[
                                "source_normalized_value"
                            ]
                        ),

                    t(
                        "row"
                    ):
                        case[
                            "source_row"
                        ],
                }
            )

        with destination_column:

            st.caption(
                t(
                    "destination_evidence"
                )
            )

            st.json(
                {
                    t(
                        "raw"
                    ):
                        _evidence_value(
                            case[
                                "destination_value"
                            ]
                        ),

                    t(
                        "normalized"
                    ):
                        _evidence_value(
                            case[
                                "destination_normalized_value"
                            ]
                        ),

                    t(
                        "expected"
                    ):
                        _evidence_value(
                            case[
                                "expected_value"
                            ]
                        ),

                    t(
                        "row"
                    ):
                        case[
                            "destination_row"
                        ],
                }
            )

    st.info(
        _localized_explanation(
            case,
            locale,
        )
    )

    with st.expander(
        t(
            "supporting"
        )
    ):

        pattern = (
            None
            if _is_missing(
                case.get(
                    "pattern_type"
                )
            )
            else
            _localized_pattern(
                case.get(
                    "pattern_type"
                ),
                locale,
            )
        )

        st.json(
            {
                t(
                    "rule_ids"
                ):
                    case[
                        "rule_ids"
                    ],

                t(
                    "supporting_records"
                ):
                    _evidence_value(
                        case[
                            "supporting_records"
                        ]
                    ),

                t(
                    "priority"
                ):
                    translate_value(
                        locale,
                        "priority",
                        case[
                            "priority"
                        ],
                    ),

                t(
                    "priority_reason"
                ):
                    _localized_priority_reason(
                        case,
                        locale,
                    ),

                t(
                    "confidence"
                ):
                    case.get(
                        "confidence"
                    ),

                t(
                    "limitation"
                ):
                    case.get(
                        "limitation_code"
                    ),

                t(
                    "pattern"
                ):
                    pattern,

                t(
                    "ai_contributed"
                ):
                    bool(
                        case.get(
                            "ai_contributed",
                            False,
                        )
                    ),

                t(
                    "ai_status"
                ):
                    case.get(
                        "ai_status"
                    ),

                t(
                    "ai_score"
                ):
                    case.get(
                        "ai_score"
                    ),
            }
        )


# ============================================================
# AI ASSIGNMENT ANALYSIS
# ============================================================

def _display_ai_assignment_analysis(
    run: ReconciliationRun,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("ai_matching_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("ai_matching_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    data = run.ai_assignment_analysis.copy()

    if data.empty:

        st.info(
            t(
                "ai_no_ambiguous"
            )
        )

        return

    selected = data.loc[
        data[
            "selected_by_best_matching"
        ].eq(
            True
        )
    ]

    first_row = data.iloc[
        0
    ]

    metric_1, metric_2, metric_3 = st.columns(
        3
    )

    metric_1.metric(
        t(
            "ai_best_score"
        ),
        f"{float(first_row['best_matching_score']):.3f}",
    )

    metric_2.metric(
        t(
            "ai_second_score"
        ),
        f"{float(first_row['second_matching_score']):.3f}",
    )

    metric_3.metric(
        t(
            "ai_confidence"
        ),
        f"{float(first_row['matching_confidence']):.3f}",
    )

    if not selected.empty:

        pair_text = ", ".join(
            (
                f"{int(row.source_row_index)}"
                " → "
                f"{int(row.destination_row_index)}"
            )

            for row
            in selected.itertuples()
        )

        st.success(
            t(
                "ai_proposal",
                pairs=pair_text,
            )
        )

    st.warning(
        t(
            "ai_advisory"
        )
    )

    preferred_columns = [
        "employee_id",
        "assignment_type",
        "source_row_index",
        "destination_row_index",
        "pair_match_score",
        "selected_by_best_matching",
        "matching_confidence",
        "recommendation",
    ]

    columns = [
        column
        for column
        in preferred_columns
        if column
        in data.columns
    ]

    view = data.loc[
        :,
        columns,
    ].copy()

    if "recommendation" in view.columns:

        view[
            "recommendation"
        ] = view[
            "recommendation"
        ].map(
            lambda value:
                _localized_recommendation(
                    value,
                    locale,
                )
        )

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# AI PRIORITIZATION
# ============================================================

def _display_ai_priorities(
    run: ReconciliationRun,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("ai_priority_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("ai_priority_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    data = run.ai_priorities.copy()

    if data.empty:

        st.info(
            t(
                "ai_no_priorities"
            )
        )

        return

    preferred = [
        "employee_id",
        "anomaly_count",
        "ai_anomaly_score",
        "ai_priority",
        "ai_explanation",
    ]

    columns = [
        column
        for column
        in preferred
        if column
        in data.columns
    ]

    view = data.loc[
        :,
        columns,
    ].copy()

    if "ai_priority" in view.columns:

        view[
            "ai_priority"
        ] = view[
            "ai_priority"
        ].map(
            lambda value:
                _localized_ai_priority(
                    value,
                    locale,
                )
        )

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
    )

    if (
        "employee_id"
        in data.columns
        and
        "ai_anomaly_score"
        in data.columns
    ):

        chart = (
            data.loc[
                :,
                [
                    "employee_id",
                    "ai_anomaly_score",
                ],
            ]
            .copy()
            .set_index(
                "employee_id"
            )
        )

        st.caption(
            t(
                "ai_priority_chart"
            )
        )

        st.bar_chart(
            chart
        )


# ============================================================
# AI PATTERNS
# ============================================================

def _display_ai_patterns(
    run: ReconciliationRun,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("ai_pattern_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("ai_pattern_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    data = run.ai_patterns.copy()

    if data.empty:

        st.info(
            t(
                "ai_no_patterns"
            )
        )

        return

    preferred = [
        "field",
        "verdict",
        "affected_employees",
        "employee_prevalence",
        "pattern_type",
        "ai_interpretation",
    ]

    columns = [
        column
        for column
        in preferred
        if column
        in data.columns
    ]

    view = data.loc[
        :,
        columns,
    ].copy()

    if "field" in view.columns:

        view[
            "field"
        ] = view[
            "field"
        ].map(
            lambda value:
                _friendly_field(
                    value,
                    locale,
                )
        )

    if "pattern_type" in view.columns:

        view[
            "pattern_type"
        ] = view[
            "pattern_type"
        ].map(
            lambda value:
                _localized_pattern(
                    value,
                    locale,
                )
        )

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
    )

    if (
        "field"
        in data.columns
        and
        "employee_prevalence"
        in data.columns
    ):

        chart_data = (
            data.loc[
                :,
                [
                    "field",
                    "employee_prevalence",
                ],
            ]
            .groupby(
                "field",
                as_index=False,
            )[
                "employee_prevalence"
            ]
            .max()
        )

        chart_data[
            "field"
        ] = chart_data[
            "field"
        ].map(
            lambda value:
                _friendly_field(
                    value,
                    locale,
                )
        )

        chart_data = (
            chart_data
            .set_index(
                "field"
            )
        )

        st.caption(
            t(
                "ai_pattern_chart"
            )
        )

        st.bar_chart(
            chart_data
        )


# ============================================================
# AI TAB
# ============================================================

def _ai_analysis(
    run: ReconciliationRun,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("ai_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("ai_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="insight-panel">'

            '<div class="insight-orb">'
            'AI'
            '</div>'

            '<div>'

            f'<div class="insight-title">'
            f'{t("ai_intro_title")}'
            '</div>'

            f'<div class="insight-copy">'
            f'{t("ai_intro_copy")}'
            '</div>'

            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    _display_ai_assignment_analysis(
        run,
        locale,
    )

    _display_ai_priorities(
        run,
        locale,
    )

    _display_ai_patterns(
        run,
        locale,
    )


# ============================================================
# EXPORTS
# ============================================================

def _exports(
    run: ReconciliationRun,
    filtered: pd.DataFrame,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("handoff_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("handoff_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    csv_column, excel_column, audit_column = st.columns(
        3
    )

    csv_column.download_button(
        t(
            "download_csv"
        ),
        cases_to_csv(
            filtered
        ),
        "corroboria_cases.csv",
        "text/csv",
        width="stretch",
    )

    excel_column.download_button(
        t(
            "download_excel"
        ),
        run_to_excel(
            run
        ),
        "corroboria_report.xlsx",
        (
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="stretch",
    )

    audit_column.download_button(
        t(
            "download_audit"
        ),
        audit_to_json(
            run
        ),
        "corroboria_run_audit.json",
        "application/json",
        width="stretch",
    )


# ============================================================
# FEEDBACK
# ============================================================

def _feedback(
    cases: pd.DataFrame,
    locale: str,
) -> None:

    t = lambda key, **values: translate(
        locale,
        key,
        **values,
    )

    st.markdown(
        (
            f'<div class="section-kicker">'
            f'{t("governance_kicker")}'
            '</div>'

            f'<h2 class="section-title">'
            f'{t("governance_title")}'
            '</h2>'
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        t(
            "feedback_caption"
        )
    )

    with st.form(
        "feedback_form",
        border=False,
    ):

        case_id = st.selectbox(
            t(
                "case"
            ),
            cases[
                "case_id"
            ].tolist(),
        )

        reviewer_verdict = st.selectbox(
            t(
                "reviewer_verdict"
            ),
            [
                "Match",
                "Justified difference",
                "Actual anomaly",
                "Needs review",
            ],
            format_func=lambda value:
                translate_value(
                    locale,
                    "verdict",
                    value,
                ),
        )

        reason = st.text_area(
            t(
                "feedback_reason"
            ),
            placeholder=t(
                "feedback_placeholder"
            ),
        )

        submitted = st.form_submit_button(
            t(
                "save_feedback"
            )
        )

    if submitted:

        if not reason.strip():

            st.warning(
                t(
                    "reason_required"
                )
            )

            return

        original = (
            cases.loc[
                cases[
                    "case_id"
                ].eq(
                    case_id
                ),
                "verdict",
            ]
            .iloc[
                0
            ]
        )

        st.session_state.feedback.append(
            {
                "case_id":
                    case_id,

                "original_verdict":
                    original,

                "reviewer_verdict":
                    reviewer_verdict,

                "reason":
                    reason.strip(),
            }
        )

        st.success(
            t(
                "feedback_saved"
            )
        )

    if st.session_state.feedback:

        feedback = pd.DataFrame(
            st.session_state.feedback
        )

        st.dataframe(
            feedback,
            width="stretch",
            hide_index=True,
        )

        st.download_button(
            t(
                "download_feedback"
            ),
            feedback.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            ),
            "corroboria_feedback.csv",
            "text/csv",
        )


# ============================================================
# GOVERNANCE AUDIT
# ============================================================

def _display_governance_audit(
    run: ReconciliationRun,
    locale: str,
) -> None:

    audit = run.audit

    if locale == "fr":

        title = "Résumé de l'audit"

        rows_label = (
            "Lignes du rapport"
        )

        ai_queue_label = (
            "Cas transmis à l'IA"
        )

        candidate_label = (
            "Paires candidates IA"
        )

        pattern_label = (
            "Tendances détectées"
        )

        readonly_message = (
            "Les fichiers sources sont traités "
            "en lecture seule."
        )

        fingerprint_title = (
            "Empreintes des fichiers d'entrée"
        )

        full_audit_title = (
            "Audit technique complet"
        )

    else:

        title = "Audit summary"

        rows_label = (
            "Report rows"
        )

        ai_queue_label = (
            "Cases sent to AI"
        )

        candidate_label = (
            "AI candidate pairs"
        )

        pattern_label = (
            "Patterns detected"
        )

        readonly_message = (
            "Source files are treated as read-only."
        )

        fingerprint_title = (
            "Input file fingerprints"
        )

        full_audit_title = (
            "Full technical audit"
        )

    st.markdown(
        f"## {title}"
    )

    one, two, three, four = st.columns(
        4
    )

    one.metric(
        rows_label,
        audit.get(
            "report_row_count",
            0,
        ),
    )

    two.metric(
        ai_queue_label,
        audit.get(
            "ai_queue_rows",
            0,
        ),
    )

    three.metric(
        candidate_label,
        audit.get(
            "ai_assignment_candidate_rows",
            0,
        ),
    )

    four.metric(
        pattern_label,
        audit.get(
            "ai_pattern_rows",
            0,
        ),
    )

    if audit.get(
        "source_files_read_only"
    ):

        st.success(
            readonly_message
        )

    fingerprints = audit.get(
        "input_sha256",
        {},
    )

    if fingerprints:

        st.markdown(
            f"### {fingerprint_title}"
        )

        fingerprint_rows = []

        for name, digest in fingerprints.items():

            fingerprint_rows.append(
                {
                    "file":
                        name,

                    "sha256":
                        str(
                            digest
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                fingerprint_rows
            ),
            width="stretch",
            hide_index=True,
        )

    with st.expander(
        full_audit_title
    ):

        st.json(
            audit
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    st.set_page_config(
        page_title="CorroborIA",
        page_icon="C",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    locale, theme = _initialise_preferences()

    _inject_theme(
        theme
    )

    if "run" not in st.session_state:
        st.session_state.run = None

    if "feedback" not in st.session_state:
        st.session_state.feedback = []

    inputs = _sidebar(
        locale,
        theme,
    )

    run: ReconciliationRun | None = (
        st.session_state.run
    )

    _hero(
        locale,
        run,
    )

    _workflow(
        locale,
        run,
    )

    run_column, privacy_column = st.columns(
        [
            1,
            2,
        ]
    )

    with run_column:

        start = st.button(
            translate(
                locale,
                "run",
            ),
            type="primary",
            disabled=(
                inputs
                is None
            ),
            width="stretch",
        )

    with privacy_column:

        st.caption(
            translate(
                locale,
                "local_first",
            )
        )

    if start:

        try:

            with st.spinner(
                translate(
                    locale,
                    "running",
                )
            ):

                st.session_state.run = (
                    run_reconciliation(
                        inputs
                    )
                )

                st.session_state.feedback = []

            st.rerun()

        except InputValidationError as error:

            st.error(
                translate(
                    locale,
                    "validation_stopped",
                )
            )

            st.code(
                "\n".join(
                    error.issues
                )
            )

        except Exception as error:

            st.exception(
                error
            )

    run = st.session_state.run

    if run is None:

        st.markdown(
            (
                '<div class="insight-panel">'

                '<div class="insight-orb">'
                'C'
                '</div>'

                '<div>'

                f'<div class="insight-title">'
                f'{translate(locale, "ready_title")}'
                '</div>'

                f'<div class="insight-copy">'
                f'{translate(locale, "ready_copy")}'
                '</div>'

                '</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        return

    (
        overview_tab,
        queue_tab,
        ai_tab,
        governance_tab,
    ) = st.tabs(
        [
            translate(
                locale,
                "tab_overview",
            ),

            translate(
                locale,
                "tab_queue",
            ),

            translate(
                locale,
                "tab_ai",
            ),

            translate(
                locale,
                "tab_governance",
            ),
        ]
    )

    # ========================================================
    # OVERVIEW
    # ========================================================

    with overview_tab:

        _display_summary(
            run,
            locale,
        )

    # ========================================================
    # REVIEW QUEUE
    # ========================================================

    with queue_tab:

        filtered = _filter_cases(
            run.cases,
            locale,
        )

        _queue_table(
            filtered,
            locale,
        )

        _case_details(
            filtered,
            locale,
        )

        _exports(
            run,
            filtered,
            locale,
        )

    # ========================================================
    # AI
    # ========================================================

    with ai_tab:

        _ai_analysis(
            run,
            locale,
        )

    # ========================================================
    # GOVERNANCE
    # ========================================================

    with governance_tab:

        _feedback(
            run.cases,
            locale,
        )

        with st.expander(
            translate(
                locale,
                "mapping_evidence",
            )
        ):

            st.dataframe(
                run.mapping,
                width="stretch",
                hide_index=True,
            )

        _display_governance_audit(
            run,
            locale,
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()