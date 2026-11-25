from datetime import date, datetime
import time
import altair as alt
import pandas as pd
import streamlit as st

from ai_service import generate_health_insights, is_ai_configured
from config import APP_NAME, APP_VERSION
from database import (
    create_patient,
    delete_patient,
    get_ai_analyses_for_patient,
    get_all_patients,
    get_patient_by_id,
    get_patient_count,
    get_total_ai_analyses_count,
    has_assignment_dataset,
    import_assignment_records,
    initialize_database,
    save_ai_analysis,
    update_patient,
    update_patient_validation,
)
from styles import SVG_ICONS, get_image_base64, inject_design_system, render_html
from validators import (
    ASSIGNMENT_DATASET,
    analyze_name_and_email_duplicates,
    compute_duplicate_keys,
    evaluate_record_quality,
    validate_blood_values,
    validate_dob,
    validate_email_address,
    validate_name,
    validate_patient,
)


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()

if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"
if "add_form_nonce" not in st.session_state:
    st.session_state.add_form_nonce = 0
if "records_subview" not in st.session_state:
    st.session_state.records_subview = "Registry & CRUD"


def navigate_to(page_name: str, subview: str | None = None) -> None:
    """Update the active workspace page and rerun."""
    st.session_state.current_page = page_name
    if subview:
        st.session_state.records_subview = subview
    st.rerun()


def refresh_all_quality() -> list[dict]:
    """Re-evaluate data quality and duplicate status across all SQLite patient records."""
    records = get_all_patients()
    dup_keys = compute_duplicate_keys(records)
    for rec in records:
        status, reasons = evaluate_record_quality(rec, dup_keys)
        reasons_str = "; ".join(reasons)
        if rec.get("validation_status") != status or (rec.get("validation_errors") or "") != reasons_str:
            update_patient_validation(rec["id"], status, reasons_str)
            rec["validation_status"] = status
            rec["validation_errors"] = reasons_str
    return records


# ---------------- DESIGN SYSTEM ----------------

hero_bg_uri = get_image_base64("assets/hero_health_ai.jpg")
inject_design_system(hero_bg_uri)


# ---------------- STARTUP INTRO SPLASH (2.6s) ----------------

if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = True
    splash = st.empty()
    with splash.container():
        render_html(
            f"""
            <div class="hs-splash-overlay">
                <div class="hs-splash-logo">
                    <svg width="44" height="44" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5 18.5H11.5L14.8 10L19.5 26L23 15.5L25.5 18.5H31" stroke="#061220" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="hs-splash-title">{APP_NAME.replace(' AI', '')}<span> AI</span></div>
                <div class="hs-splash-sub">Intelligent Health Management</div>
                <div class="hs-splash-bar-wrap">
                    <div class="hs-splash-bar-fill"></div>
                </div>
            </div>
            """
        )
    time.sleep(2.6)
    splash.empty()


# ---------------- SIDEBAR ----------------

NAV_ITEMS = [
    ("Overview", ":material/dashboard:"),
    ("Patient Records", ":material/group:"),
    ("Add Patient", ":material/person_add:"),
    ("AI Health Insights", ":material/neurology:"),
]

with st.sidebar:
    render_html(
        f"""
        <div class="hs-sidebar-brand">
            {SVG_ICONS["logo"]}
            <div>
                <div class="hs-sidebar-title">Health<span>Sync</span> AI</div>
                <div class="hs-sidebar-tagline">Clinical Intelligence</div>
            </div>
        </div>
        """
    )

    st.markdown("---")
    render_html('<div class="hs-nav-label">Workspace</div>')

    for label, icon in NAV_ITEMS:
        is_active = st.session_state.current_page == label
        if st.button(
            label,
            icon=icon,
            key=f"nav_{label}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            if not is_active:
                navigate_to(label)

    st.markdown("---")

    ai_ready = is_ai_configured()
    ai_status_label = "AI Engine Ready" if ai_ready else "AI Key Not Set"

    render_html(
        f"""
        <div class="hs-sidebar-footer">
            <div class="hs-nav-label" style="padding:0 0 4px 0;">Application Status</div>
            <div class="hs-status-row">
                <span class="hs-dot-green"></span>
                <span>System Ready</span>
            </div>
            <div style="font-size:12px; color:#8BA4BF; margin-top:4px;">
                SQLite Connected · {ai_status_label}
            </div>
            <div class="hs-version-row">
                <span>{APP_NAME}</span>
                <span>v{APP_VERSION}</span>
            </div>
        </div>
        """
    )


# ---------------- CUSTOM APPLICATION HEADER ----------------

formatted_date = datetime.now().strftime("%a, %b %d, %Y")

render_html(
    f"""
    <div class="hs-topbar">
        <div class="hs-topbar-left">
            {SVG_ICONS["logo"]}
            <div>
                <div class="hs-topbar-brand">Health<span>Sync</span> AI</div>
                <div class="hs-topbar-sub">Intelligent Health Management</div>
            </div>
        </div>
        <div class="hs-topbar-right">
            <div class="hs-pill">
                {SVG_ICONS["calendar"]}
                <span>{formatted_date}</span>
            </div>
            <div class="hs-pill hs-pill-status">
                <span class="hs-dot-green"></span>
                <span>System Operational</span>
            </div>
        </div>
    </div>
    """
)


# ---------------- OVERVIEW ----------------

page = st.session_state.current_page

if page == "Overview":
    patients = refresh_all_quality()
    total_patients = get_patient_count()
    ai_analyses_count = get_total_ai_analyses_count()
    updated_records_count = sum(
        1
        for p in patients
        if p.get("updated_at") and p.get("created_at") and p["updated_at"] != p["created_at"]
    )
    valid_count = sum(1 for p in patients if p.get("validation_status") == "Valid")
    review_count = sum(1 for p in patients if p.get("validation_status") in ("Needs Review", "Invalid"))

    # Hero Section
    render_html(
        """
        <div class="hs-hero">
            <div class="hs-hero-content">
                <div class="hs-hero-badge">
                    <span class="hs-dot-green"></span>
                    AI-Powered Clinical Workspace
                </div>
                <h1 class="hs-hero-title">Welcome to HealthSync AI</h1>
                <p class="hs-hero-desc">
                    Manage patient records, audit clinical data quality, and generate
                    cautious AI-assisted health observations from one unified platform.
                </p>
            </div>
        </div>
        """
    )

    cta_col1, cta_col2, cta_col3, _ = st.columns([1.2, 1.45, 1.45, 2.0])
    with cta_col1:
        if st.button("Add Patient", icon=":material/person_add:", type="primary", use_container_width=True, key="hero_add"):
            navigate_to("Add Patient")
    with cta_col2:
        if st.button("View Patient Records", icon=":material/folder_shared:", type="secondary", use_container_width=True, key="hero_records"):
            navigate_to("Patient Records", "Registry & CRUD")
    with cta_col3:
        if st.button("AI Health Insights", icon=":material/neurology:", type="secondary", use_container_width=True, key="hero_ai"):
            navigate_to("AI Health Insights")

    render_html("<div style='height: 14px;'></div>")

    # 5 Live Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        render_html(
            f"""
            <div class="hs-metric-card">
                <div class="hs-metric-top">
                    <span class="hs-metric-label">Total Patients</span>
                    <span class="hs-icon-badge hs-badge-teal">{SVG_ICONS["patients"]}</span>
                </div>
                <div class="hs-metric-value">{total_patients}</div>
                <div class="hs-metric-foot">
                    <span class="hs-trend-pill hs-trend-teal">Registry</span>
                    <span>Stored in SQLite</span>
                </div>
            </div>
            """
        )

    with m2:
        render_html(
            f"""
            <div class="hs-metric-card">
                <div class="hs-metric-top">
                    <span class="hs-metric-label">AI Analyses</span>
                    <span class="hs-icon-badge hs-badge-aqua">{SVG_ICONS["ai"]}</span>
                </div>
                <div class="hs-metric-value">{ai_analyses_count}</div>
                <div class="hs-metric-foot">
                    <span class="hs-trend-pill hs-trend-teal">Insights</span>
                    <span>Generated total</span>
                </div>
            </div>
            """
        )

    with m3:
        render_html(
            f"""
            <div class="hs-metric-card">
                <div class="hs-metric-top">
                    <span class="hs-metric-label">Records Updated</span>
                    <span class="hs-icon-badge hs-badge-navy">{SVG_ICONS["records"]}</span>
                </div>
                <div class="hs-metric-value">{updated_records_count}</div>
                <div class="hs-metric-foot">
                    <span class="hs-trend-pill hs-trend-slate">Modified</span>
                    <span>Edited or analyzed</span>
                </div>
            </div>
            """
        )

    with m4:
        render_html(
            f"""
            <div class="hs-metric-card">
                <div class="hs-metric-top">
                    <span class="hs-metric-label">Valid Records</span>
                    <span class="hs-icon-badge hs-badge-mint">{SVG_ICONS["pulse"]}</span>
                </div>
                <div class="hs-metric-value">{valid_count}</div>
                <div class="hs-metric-foot">
                    <span class="hs-trend-pill hs-trend-green">Verified</span>
                    <span>Passed all checks</span>
                </div>
            </div>
            """
        )

    with m5:
        render_html(
            f"""
            <div class="hs-metric-card">
                <div class="hs-metric-top">
                    <span class="hs-metric-label">Needs Review</span>
                    <span class="hs-icon-badge hs-badge-navy">{SVG_ICONS["insights"]}</span>
                </div>
                <div class="hs-metric-value">{review_count}</div>
                <div class="hs-metric-foot">
                    <span class="hs-trend-pill hs-trend-slate">Quality</span>
                    <span>Invalid / duplicate</span>
                </div>
            </div>
            """
        )

    # Workspace & Platform Overview
    left_col, right_col = st.columns([1.65, 1], gap="large")

    with left_col:
        render_html(
            """
            <div class="hs-section-header">
                <h2 class="hs-section-title">Workspace</h2>
                <span class="hs-section-sub">Core clinical modules</span>
            </div>
            """
        )

        w1, w2 = st.columns(2)
        with w1:
            render_html(
                f"""
                <div class="hs-feature-card">
                    <div class="hs-feature-head">
                        <span class="hs-icon-badge hs-badge-teal">{SVG_ICONS["patients"]}</span>
                        <span class="hs-feature-tag">Registry</span>
                    </div>
                    <div class="hs-feature-title">Patient Management</div>
                    <div class="hs-feature-desc">
                        Browse, search, filter, edit, and safely delete patient records.
                    </div>
                </div>
                """
            )
            if st.button("Open Patient Records", key="ws_patients", use_container_width=True):
                navigate_to("Patient Records", "Registry & CRUD")

        with w2:
            render_html(
                f"""
                <div class="hs-feature-card">
                    <div class="hs-feature-head">
                        <span class="hs-icon-badge hs-badge-navy">{SVG_ICONS["database"]}</span>
                        <span class="hs-feature-tag">Intake</span>
                    </div>
                    <div class="hs-feature-title">Patient Registration</div>
                    <div class="hs-feature-desc">
                        Register new patients with strict date, email, and lab validation.
                    </div>
                </div>
                """
            )
            if st.button("Register New Patient", key="ws_add", use_container_width=True):
                navigate_to("Add Patient")

        render_html("<div style='height: 10px;'></div>")

        w3, w4 = st.columns(2)
        with w3:
            render_html(
                f"""
                <div class="hs-feature-card">
                    <div class="hs-feature-head">
                        <span class="hs-icon-badge hs-badge-aqua">{SVG_ICONS["ai"]}</span>
                        <span class="hs-feature-tag">AI Engine</span>
                    </div>
                    <div class="hs-feature-title">AI Health Analysis</div>
                    <div class="hs-feature-desc">
                        Generate cautious educational health observations from lab values.
                    </div>
                </div>
                """
            )
            if st.button("Launch AI Insights", key="ws_ai", use_container_width=True):
                navigate_to("AI Health Insights")

        with w4:
            render_html(
                f"""
                <div class="hs-feature-card">
                    <div class="hs-feature-head">
                        <span class="hs-icon-badge hs-badge-mint">{SVG_ICONS["insights"]}</span>
                        <span class="hs-feature-tag">Audit</span>
                    </div>
                    <div class="hs-feature-title">Data Quality & Validation</div>
                    <div class="hs-feature-desc">
                        Inspect validation errors, duplicates, and import assignment data.
                    </div>
                </div>
                """
            )
            if st.button("Open Data Quality", key="ws_quality", use_container_width=True):
                navigate_to("Patient Records", "Data Quality & Assignment Import")

    with right_col:
        render_html(
            """
            <div class="hs-section-header">
                <h2 class="hs-section-title">Recent Activity</h2>
                <span class="hs-section-sub">Latest SQLite records</span>
            </div>
            """
        )

        if not patients:
            render_html(
                """
                <div class="hs-panel-card">
                    <div class="hs-panel-title">No Recent Activity</div>
                    <div style="font-size:13.5px; line-height:1.6; color:#64748B;">
                        Your database is currently empty. Add a patient or import the
                        10-record assignment dataset in <b>Patient Records</b>.
                    </div>
                </div>
                """
            )
        else:
            recent_df = pd.DataFrame(patients[:5])
            recent_display = pd.DataFrame(
                {
                    "ID": recent_df["id"],
                    "Patient": recent_df["full_name"],
                    "Quality": recent_df["validation_status"],
                    "AI": recent_df["remarks"].apply(
                        lambda x: "Analyzed" if str(x or "").strip() else "Pending"
                    ),
                    "Updated": recent_df["updated_at"].astype(str).str.slice(0, 16),
                }
            )
            st.dataframe(recent_display, use_container_width=True, hide_index=True)

        ai_badge = "Configured" if ai_ready else "Awaiting .env Config"
        render_html(
            f"""
            <div class="hs-panel-card" style="margin-top: 14px;">
                <div class="hs-panel-title">Platform Information</div>
                <div class="hs-spec-row">
                    <span class="hs-spec-key">Database</span>
                    <span class="hs-spec-val">SQLite (Persistent)</span>
                </div>
                <div class="hs-spec-row">
                    <span class="hs-spec-key">AI Integration</span>
                    <span class="hs-spec-val">{ai_badge}</span>
                </div>
                <div class="hs-spec-row">
                    <span class="hs-spec-key">Version</span>
                    <span class="hs-spec-val">v{APP_VERSION}</span>
                </div>
            </div>
            """
        )

    # Dashboard Visualizations
    render_html(
        """
        <div class="hs-section-header">
            <h2 class="hs-section-title">Clinical Analytics & Distributions</h2>
            <span class="hs-section-sub">Clear breakdown of data quality, AI coverage, and patient lab values</span>
        </div>
        """
    )

    if not patients:
        st.info("Charts will appear automatically once patient records are registered or imported.")
    else:
        df_all = pd.DataFrame(patients)
        total_n = len(df_all)

        # Row 1: 3 Executive Summary Cards (Quality, AI Coverage, Source)
        def _bar_row(label: str, count: int, total: int, color: str) -> str:
            pct = round((count / total) * 100) if total else 0
            return (
                f'<div style="margin-bottom:12px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px;">'
                f'<span style="color:#334155;font-weight:600;">{label}</span>'
                f'<span style="color:#0B192C;font-weight:700;">{count} <span style="color:#64748B;font-weight:500;">({pct}%)</span></span>'
                f'</div>'
                f'<div style="width:100%;height:8px;background:#F1F5F9;border-radius:999px;overflow:hidden;">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:999px;"></div>'
                f'</div></div>'
            )

        c_left, c_mid, c_right = st.columns(3, gap="medium")

        with c_left:
            n_valid = int((df_all["validation_status"] == "Valid").sum())
            n_review = int((df_all["validation_status"] == "Needs Review").sum())
            n_invalid = int((df_all["validation_status"] == "Invalid").sum())
            render_html(
                f"""
                <div class="hs-panel-card" style="height:100%;">
                    <div class="hs-panel-title" style="margin-bottom:4px;">Data Quality Breakdown</div>
                    <div style="font-size:12.5px;color:#64748B;margin-bottom:16px;">Validation status across {total_n} records</div>
                    {_bar_row("Valid Records", n_valid, total_n, "#10B981")}
                    {_bar_row("Needs Review (Duplicates)", n_review, total_n, "#F59E0B")}
                    {_bar_row("Invalid (Format / Date Errors)", n_invalid, total_n, "#EF4444")}
                </div>
                """
            )

        with c_mid:
            n_analyzed = int(df_all["remarks"].apply(lambda r: bool(str(r or "").strip())).sum())
            n_pending = total_n - n_analyzed
            cov_pct = round((n_analyzed / total_n) * 100) if total_n else 0
            render_html(
                f"""
                <div class="hs-panel-card" style="height:100%;">
                    <div class="hs-panel-title" style="margin-bottom:4px;">AI Analysis Coverage</div>
                    <div style="font-size:12.5px;color:#64748B;margin-bottom:14px;">Patients with AI-generated health remarks</div>
                    <div style="font-size:28px;font-weight:800;color:#0B192C;line-height:1.1;margin-bottom:12px;">
                        {cov_pct}% <span style="font-size:13px;font-weight:500;color:#64748B;">({n_analyzed} of {total_n} analyzed)</span>
                    </div>
                    {_bar_row("AI Remarks Generated", n_analyzed, total_n, "#0D9488")}
                    {_bar_row("Pending Analysis", n_pending, total_n, "#94A3B8")}
                </div>
                """
            )

        with c_right:
            src_series = df_all["record_source"].fillna("Manual")
            n_manual = int((src_series == "Manual").sum())
            n_import = int((src_series == "Assignment Import").sum())
            render_html(
                f"""
                <div class="hs-panel-card" style="height:100%;">
                    <div class="hs-panel-title" style="margin-bottom:4px;">Record Source Overview</div>
                    <div style="font-size:12.5px;color:#64748B;margin-bottom:16px;">Origin of patient entries in SQLite</div>
                    {_bar_row("Manual Registration", n_manual, total_n, "#0D9488")}
                    {_bar_row("Assignment Import", n_import, total_n, "#1E3A5F")}
                    <div style="font-size:12px;color:#64748B;margin-top:8px;">
                        Total active records: <b style="color:#0B192C;">{total_n}</b>
                    </div>
                </div>
                """
            )

        # Duplicate Name & Email Monitor Card + Impact Explanation
        dup_summary = analyze_name_and_email_duplicates(patients)
        dup_n_recs = dup_summary["duplicate_name_records"]
        dup_e_recs = dup_summary["duplicate_email_records"]
        total_flagged_dups = len(dup_summary["flagged_records"])

        render_html("<div style='height: 14px;'></div>")
        dup_col, impact_col = st.columns([1, 1.5], gap="medium")

        with dup_col:
            render_html(
                f"""
                <div class="hs-panel-card" style="height:100%;">
                    <div class="hs-panel-title" style="margin-bottom:4px;">Duplicate Name & Email Monitor</div>
                    <div style="font-size:12.5px;color:#64748B;margin-bottom:14px;">
                        Detects overlapping patient names and email addresses in SQLite
                    </div>
                    <div class="hs-spec-row">
                        <span class="hs-spec-key">Duplicate Name Records</span>
                        <span class="hs-spec-val" style="color:{'#D97706' if dup_n_recs else '#059669'};">{dup_n_recs} record(s)</span>
                    </div>
                    <div class="hs-spec-row">
                        <span class="hs-spec-key">Duplicate Email Records</span>
                        <span class="hs-spec-val" style="color:{'#D97706' if dup_e_recs else '#059669'};">{dup_e_recs} record(s)</span>
                    </div>
                    <div class="hs-spec-row">
                        <span class="hs-spec-key">Total Flagged for Cleanup</span>
                        <span class="hs-spec-val">{total_flagged_dups} record(s)</span>
                    </div>
                </div>
                """
            )
            if st.button("Manage & Delete Duplicates", icon=":material/content_copy:", key="ov_manage_dups", use_container_width=True):
                navigate_to("Patient Records", "Data Quality & Assignment Import")

        with impact_col:
            render_html(
                """
                <div class="hs-panel-card" style="height:100%;">
                    <div class="hs-panel-title" style="margin-bottom:6px;">Why Duplicate & Faulty Values Matter</div>
                    <div style="font-size:13.5px;line-height:1.65;color:#475569;">
                        <ul style="margin:0;padding-left:18px;">
                            <li><b>Clinical Record Mix-Ups:</b> Duplicate names or emails can attach lab values or AI remarks to the wrong patient profile.</li>
                            <li><b>Skewed Analytics:</b> Repeated entries distort average glucose, haemoglobin, and cholesterol metrics.</li>
                            <li><b>Communication Failures:</b> Invalid emails (e.g. <code>hunter@gmail</code>) prevent patient report delivery.</li>
                            <li><b>Unreliable Timelines:</b> Invalid or future dates (e.g. <code>31.11.2001</code>, <code>19.10.2030</code>) corrupt age and risk context.</li>
                        </ul>
                    </div>
                </div>
                """
            )

        render_html("<div style='height: 14px;'></div>")

        # Row 2: 3 Biomarker Distribution Cards (Altair with unique #ID labels — no duplicate stacking)
        chart_df = df_all.sort_values("id").copy()
        chart_df["record_label"] = chart_df.apply(
            lambda r: f"#{r['id']} {str(r['full_name']).split()[0]}", axis=1
        )

        def _biomarker_card(col_container, field: str, title: str, subtitle: str, bar_color: str) -> None:
            with col_container:
                with st.container(border=True):
                    vals = pd.to_numeric(chart_df[field], errors="coerce").dropna()
                    avg_v = f"{vals.mean():.1f}" if len(vals) else "—"
                    min_v = f"{vals.min():.1f}" if len(vals) else "—"
                    max_v = f"{vals.max():.1f}" if len(vals) else "—"

                    render_html(
                        f"""
                        <div style="padding:4px 4px 8px 4px;">
                            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15.5px;font-weight:700;color:#0B192C;">{title}</div>
                            <div style="font-size:12px;color:#64748B;margin-bottom:10px;">{subtitle}</div>
                            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px;">
                                <span class="hs-trend-pill hs-trend-teal">Avg: {avg_v}</span>
                                <span class="hs-trend-pill hs-trend-slate">Min: {min_v}</span>
                                <span class="hs-trend-pill hs-trend-slate">Max: {max_v}</span>
                            </div>
                        </div>
                        """
                    )

                    chart = (
                        alt.Chart(chart_df)
                        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=bar_color)
                        .encode(
                            x=alt.X(
                                "record_label:N",
                                sort=None,
                                title=None,
                                axis=alt.Axis(labelAngle=-35, labelColor="#64748B", labelFontSize=11),
                            ),
                            y=alt.Y(
                                f"{field}:Q",
                                title=None,
                                axis=alt.Axis(gridColor="#F1F5F9", labelColor="#64748B", labelFontSize=11),
                            ),
                            tooltip=[
                                alt.Tooltip("id:O", title="Record ID"),
                                alt.Tooltip("full_name:N", title="Patient"),
                                alt.Tooltip(f"{field}:Q", title=title),
                            ],
                        )
                        .properties(height=210)
                        .configure_view(strokeWidth=0)
                    )
                    st.altair_chart(chart, use_container_width=True)

        b_left, b_mid, b_right = st.columns(3, gap="medium")
        _biomarker_card(b_left, "glucose", "Blood Glucose", "Per-record glucose values", "#0D9488")
        _biomarker_card(b_mid, "haemoglobin", "Haemoglobin", "Per-record haemoglobin values", "#0891B2")
        _biomarker_card(b_right, "cholesterol", "Cholesterol", "Per-record cholesterol values", "#1E3A5F")


# ---------------- ADD PATIENT ----------------

elif page == "Add Patient":
    render_html(
        """
        <div class="hs-page-header">
            <h1 class="hs-page-title">Add Patient</h1>
            <p class="hs-page-sub">Register a new patient profile with strict validation. Date of birth is stored in DD/MM/YYYY format.</p>
        </div>
        """
    )

    nonce = st.session_state.add_form_nonce

    with st.form(f"add_patient_form_{nonce}"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input(
                "Full Name *",
                placeholder="e.g. Aarav Sharma",
                help="Required. Minimum 2 characters.",
            )
            dob_value = st.date_input(
                "Date of Birth (DD/MM/YYYY) *",
                value=date(1992, 1, 15),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                format="DD/MM/YYYY",
                help="Select a valid date in DD/MM/YYYY format (cannot be in the future).",
            )
            email = st.text_input(
                "Email Address *",
                placeholder="e.g. aarav@example.com",
                help="Required. Must be a valid email address.",
            )

        with c2:
            glucose = st.number_input(
                "Glucose *",
                min_value=0.0,
                value=95.0,
                step=0.5,
                help="Numeric value greater than zero.",
            )
            haemoglobin = st.number_input(
                "Haemoglobin *",
                min_value=0.0,
                value=14.0,
                step=0.1,
                help="Numeric value greater than zero.",
            )
            cholesterol = st.number_input(
                "Cholesterol *",
                min_value=0.0,
                value=180.0,
                step=1.0,
                help="Numeric value greater than zero.",
            )

        notes = st.text_area(
            "Initial Clinical Notes (Optional)",
            placeholder="Optional notes...",
            height=85,
        )
        auto_ai = st.checkbox(
            "Generate AI Health Remarks automatically upon registration",
            value=is_ai_configured(),
            help="Calls the configured AI API to populate the Remarks field when registering a valid patient.",
        )

        btn_col1, btn_col2, _ = st.columns([1.3, 1.0, 2.7])
        submitted = btn_col1.form_submit_button("Register Patient", type="primary", use_container_width=True)
        reset_clicked = btn_col2.form_submit_button("Reset Form", use_container_width=True)

        if reset_clicked:
            st.session_state.add_form_nonce += 1
            st.rerun()

        if submitted:
            dob_str = dob_value.strftime("%d/%m/%Y") if dob_value else ""
            patient_data = {
                "full_name": full_name.strip(),
                "dob": dob_str,
                "email": email.strip(),
                "glucose": glucose,
                "haemoglobin": haemoglobin,
                "cholesterol": cholesterol,
                "remarks": notes.strip(),
                "record_source": "Manual",
            }

            is_valid, error = validate_patient(patient_data)
            if not is_valid:
                st.error(f"Validation Error: {error}")
            else:
                existing = get_all_patients()
                email_match = next(
                    (p for p in existing if p["email"].strip().lower() == patient_data["email"].lower()),
                    None,
                )
                name_match = next(
                    (p for p in existing if p["full_name"].strip().lower() == patient_data["full_name"].lower()),
                    None,
                )
                if email_match:
                    st.error(
                        f"This email address (`{patient_data['email']}`) already exists in the registry "
                        f"(Record #{email_match['id']} — {email_match['full_name']}). "
                        "Duplicate emails can cause patient notification mix-ups and fragmented records."
                    )
                elif name_match:
                    st.error(
                        f"A patient with the name `{patient_data['full_name']}` already exists in the registry "
                        f"(Record #{name_match['id']} — {name_match['email']}). "
                        "Duplicate names can cause clinical record confusion and skewed analytics."
                    )
                else:
                    ai_result = None
                    if auto_ai:
                        with st.spinner("Generating AI health remarks..."):
                            ai_result = generate_health_insights(patient_data)
                        if ai_result["ok"]:
                            patient_data["remarks"] = ai_result["content"]

                    new_id = create_patient(patient_data)
                    if ai_result and ai_result["ok"]:
                        save_ai_analysis(new_id, ai_result["content"], ai_result.get("model", ""))
                    elif auto_ai and ai_result and not ai_result["ok"]:
                        st.warning(f"Patient saved, but AI remarks could not be generated: {ai_result['error']}")

                    refresh_all_quality()
                    st.success(
                        f"Patient '{patient_data['full_name']}' registered successfully "
                        f"(Record ID #{new_id}, DOB {dob_str})."
                    )


# ---------------- PATIENT RECORDS ----------------

elif page == "Patient Records":
    render_html(
        """
        <div class="hs-page-header">
            <h1 class="hs-page-title">Patient Records</h1>
            <p class="hs-page-sub">Complete SQLite CRUD management, data quality auditing, and assignment dataset import.</p>
        </div>
        """
    )

    subview = st.radio(
        "Section View",
        ["Registry & CRUD", "Data Quality & Assignment Import"],
        index=0 if st.session_state.records_subview == "Registry & CRUD" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.records_subview = subview

    patients = refresh_all_quality()

    if subview == "Registry & CRUD":
        if not patients:
            st.info("No patient records found in SQLite. Register a patient or switch to 'Data Quality & Assignment Import' to load the 10 assignment records.")
            c1, c2, _ = st.columns([1.2, 1.8, 3.0])
            with c1:
                if st.button("Add Patient", icon=":material/person_add:", type="primary", use_container_width=True):
                    navigate_to("Add Patient")
            with c2:
                if st.button("Go to Assignment Import", icon=":material/upload_file:", use_container_width=True):
                    navigate_to("Patient Records", "Data Quality & Assignment Import")
        else:
            f1, f2, f3, f4, f5 = st.columns([2.2, 1.2, 1.2, 1.2, 0.8])
            with f1:
                search_query = st.text_input(
                    "Search",
                    placeholder="Search by Name, Email, or Record ID...",
                    label_visibility="collapsed",
                )
            with f2:
                quality_filter = st.selectbox(
                    "Quality",
                    ["All Quality", "Valid", "Needs Review", "Invalid"],
                    label_visibility="collapsed",
                )
            with f3:
                source_filter = st.selectbox(
                    "Source",
                    ["All Sources", "Manual", "Assignment Import"],
                    label_visibility="collapsed",
                )
            with f4:
                sort_option = st.selectbox(
                    "Sort",
                    ["Newest First", "Oldest First", "Name (A-Z)", "Glucose (High-Low)", "Cholesterol (High-Low)"],
                    label_visibility="collapsed",
                )
            with f5:
                if st.button("Refresh", icon=":material/refresh:", use_container_width=True):
                    st.rerun()

            q = search_query.strip().lower()
            filtered = []
            for p in patients:
                if q:
                    matches_id = q == str(p["id"]) or f"#{p['id']}" == q
                    matches_text = q in p["full_name"].lower() or q in p["email"].lower()
                    if not (matches_id or matches_text):
                        continue
                if quality_filter != "All Quality" and p.get("validation_status") != quality_filter:
                    continue
                if source_filter != "All Sources" and (p.get("record_source") or "Manual") != source_filter:
                    continue
                filtered.append(p)

            if sort_option == "Oldest First":
                filtered.sort(key=lambda x: x["id"])
            elif sort_option == "Name (A-Z)":
                filtered.sort(key=lambda x: x["full_name"].lower())
            elif sort_option == "Glucose (High-Low)":
                filtered.sort(key=lambda x: float(x["glucose"]), reverse=True)
            elif sort_option == "Cholesterol (High-Low)":
                filtered.sort(key=lambda x: float(x["cholesterol"]), reverse=True)

            st.caption(f"Showing **{len(filtered)}** of **{len(patients)}** total patient record(s).")

            if not filtered:
                st.warning("No patient records match your current search or filter criteria.")
            else:
                table_df = pd.DataFrame(
                    [
                        {
                            "Record ID": p["id"],
                            "Full Name": p["full_name"],
                            "DOB": p["dob"],
                            "Email": p["email"],
                            "Glucose": p["glucose"],
                            "Haemoglobin": p["haemoglobin"],
                            "Cholesterol": p["cholesterol"],
                            "Remarks": (p.get("remarks") or "").strip() or "—",
                            "AI Remarks Status": "Generated" if (p.get("remarks") or "").strip() else "Pending",
                            "Data Quality Status": p.get("validation_status", "Valid"),
                            "Source": p.get("record_source", "Manual"),
                            "Created Date": str(p.get("created_at", ""))[:19],
                        }
                        for p in filtered
                    ]
                )
                st.dataframe(table_df, use_container_width=True, hide_index=True)

                render_html("<div style='height: 12px;'></div>")

                options = {
                    f"#{p['id']} — {p['full_name']} ({p['validation_status']})": p["id"]
                    for p in filtered
                }
                selected_label = st.selectbox("Select Patient Record for Details, Edit, or Delete", list(options.keys()))
                selected_id = options[selected_label]
                patient = get_patient_by_id(selected_id)

                if patient:
                    tab_details, tab_edit, tab_delete = st.tabs(["Patient Details", "Edit Record", "Delete Record"])

                    with tab_details:
                        d_left, d_right = st.columns([1.15, 1])
                        with d_left:
                            render_html(
                                f"""
                                <div class="hs-panel-card">
                                    <div class="hs-panel-title">Profile — #{patient['id']} {patient['full_name']}</div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Full Name</span><span class="hs-spec-val">{patient['full_name']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Date of Birth</span><span class="hs-spec-val">{patient['dob']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Email</span><span class="hs-spec-val">{patient['email']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Record Source</span><span class="hs-spec-val">{patient.get('record_source', 'Manual')}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Created At</span><span class="hs-spec-val">{patient.get('created_at', '')}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Updated At</span><span class="hs-spec-val">{patient.get('updated_at', '')}</span></div>
                                </div>
                                """
                            )
                        with d_right:
                            val_status = patient.get("validation_status", "Valid")
                            val_reasons = patient.get("validation_errors") or "All validation checks passed."
                            render_html(
                                f"""
                                <div class="hs-panel-card">
                                    <div class="hs-panel-title">Biomarkers & Data Quality</div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Glucose</span><span class="hs-spec-val">{patient['glucose']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Haemoglobin</span><span class="hs-spec-val">{patient['haemoglobin']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Cholesterol</span><span class="hs-spec-val">{patient['cholesterol']}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Quality Status</span><span class="hs-spec-val">{val_status}</span></div>
                                    <div class="hs-spec-row"><span class="hs-spec-key">Validation Notes</span><span class="hs-spec-val">{val_reasons}</span></div>
                                </div>
                                """
                            )

                        st.markdown("**Latest AI-Generated Health Remarks**")
                        latest_remarks = (patient.get("remarks") or "").strip()
                        if latest_remarks:
                            st.markdown(latest_remarks)
                        else:
                            st.info("No AI remarks generated for this patient yet. Use AI Health Insights to generate an analysis.")

                        history = get_ai_analyses_for_patient(patient["id"])
                        if history:
                            with st.expander(f"Previous AI Analysis History ({len(history)})"):
                                for item in history:
                                    st.caption(f"Analyzed at {item['created_at']} · Model: {item.get('model_name') or 'Configured API'}")
                                    st.markdown(item["remarks"])
                                    st.markdown("---")

                    with tab_edit:
                        with st.form(f"edit_patient_form_{patient['id']}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                edit_name = st.text_input("Full Name *", value=patient["full_name"])
                                edit_dob = st.text_input(
                                    "Date of Birth (DD/MM/YYYY) *",
                                    value=patient["dob"],
                                    help="Must be a valid date in DD/MM/YYYY format.",
                                )
                                edit_email = st.text_input("Email Address *", value=patient["email"])
                            with ec2:
                                edit_glucose = st.number_input("Glucose *", min_value=0.0, value=float(patient["glucose"]), step=0.5)
                                edit_haemoglobin = st.number_input("Haemoglobin *", min_value=0.0, value=float(patient["haemoglobin"]), step=0.1)
                                edit_cholesterol = st.number_input("Cholesterol *", min_value=0.0, value=float(patient["cholesterol"]), step=1.0)

                            edit_remarks = st.text_area("AI / Clinical Remarks", value=patient.get("remarks", ""), height=120)

                            save_btn = st.form_submit_button("Save Changes", type="primary")
                            if save_btn:
                                updated_data = {
                                    "full_name": edit_name.strip(),
                                    "dob": edit_dob.strip(),
                                    "email": edit_email.strip(),
                                    "glucose": edit_glucose,
                                    "haemoglobin": edit_haemoglobin,
                                    "cholesterol": edit_cholesterol,
                                    "remarks": edit_remarks.strip(),
                                }
                                checks = [
                                    validate_name(updated_data["full_name"]),
                                    validate_email_address(updated_data["email"]),
                                    validate_dob(updated_data["dob"], allow_dot_format=True),
                                    validate_blood_values(
                                        updated_data["glucose"],
                                        updated_data["haemoglobin"],
                                        updated_data["cholesterol"],
                                    ),
                                ]
                                first_error = next((err for ok, err in checks if not ok), None)
                                if first_error:
                                    st.error(f"Validation Error: {first_error}")
                                else:
                                    update_patient(patient["id"], updated_data)
                                    refresh_all_quality()
                                    st.success(f"Record #{patient['id']} ({updated_data['full_name']}) updated successfully.")
                                    st.rerun()

                    with tab_delete:
                        st.warning(
                            f"You are about to permanently delete Record **#{patient['id']} — {patient['full_name']}** "
                            f"(Email: `{patient['email']}`, DOB: `{patient['dob']}`)."
                        )
                        confirm_del = st.checkbox(
                            "I confirm that I want to permanently delete this patient record from SQLite.",
                            key=f"confirm_del_{patient['id']}",
                        )
                        if st.button(
                            "Confirm Delete Record",
                            icon=":material/delete:",
                            type="primary",
                            disabled=not confirm_del,
                            key=f"btn_del_{patient['id']}",
                        ):
                            delete_patient(patient["id"])
                            refresh_all_quality()
                            st.success(f"Patient record #{patient['id']} deleted successfully.")
                            st.rerun()

    else:
        # Data Quality & Assignment Import Subview
        already_imported = has_assignment_dataset()

        render_html(
            """
            <div class="hs-panel-card">
                <div class="hs-panel-title">Assignment Dataset Import (10 Records — Preserved Unchanged)</div>
                <div style="font-size:13.5px; line-height:1.6; color:#475569;">
                    Import the exact 10-record assignment dataset into SQLite without modifying, correcting,
                    or deduplicating any values. Intentionally invalid records (invalid email, invalid calendar date,
                    future DOB, and duplicate records) are preserved and flagged by the Data Quality engine.
                </div>
            </div>
            """
        )

        preview_df = pd.DataFrame(ASSIGNMENT_DATASET)
        with st.expander("Preview Exact 10 Assignment Records", expanded=not already_imported):
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

        if not already_imported:
            confirm_import = st.checkbox(
                "I confirm importing all 10 assignment records unchanged into SQLite.",
                key="confirm_assign_import",
            )
            if st.button(
                "Import Assignment Dataset (10 Records)",
                icon=":material/upload_file:",
                type="primary",
                disabled=not confirm_import,
            ):
                dup_keys = compute_duplicate_keys(ASSIGNMENT_DATASET)
                prepared = []
                for rec in ASSIGNMENT_DATASET:
                    status, reasons = evaluate_record_quality(rec, dup_keys)
                    item = dict(rec)
                    item["validation_status"] = status
                    item["validation_errors"] = "; ".join(reasons)
                    prepared.append(item)
                import_assignment_records(prepared, replace_existing=False)
                refresh_all_quality()
                st.success("Successfully imported all 10 assignment records unchanged.")
                st.rerun()
        else:
            st.success("Assignment dataset (10 records) is already imported in SQLite. Duplicate accidental import is blocked.")
            confirm_reimport = st.checkbox(
                "I confirm resetting and re-importing the 10 assignment records (replaces existing Assignment Import rows).",
                key="confirm_assign_reimport",
            )
            if st.button(
                "Reset & Re-import Assignment Dataset",
                icon=":material/restart_alt:",
                disabled=not confirm_reimport,
            ):
                dup_keys = compute_duplicate_keys(ASSIGNMENT_DATASET)
                prepared = []
                for rec in ASSIGNMENT_DATASET:
                    status, reasons = evaluate_record_quality(rec, dup_keys)
                    item = dict(rec)
                    item["validation_status"] = status
                    item["validation_errors"] = "; ".join(reasons)
                    prepared.append(item)
                import_assignment_records(prepared, replace_existing=True)
                refresh_all_quality()
                st.success("Assignment dataset reset and re-imported cleanly.")
                st.rerun()

        render_html(
            """
            <div class="hs-section-header">
                <h2 class="hs-section-title">Data Quality & Validation Report</h2>
                <span class="hs-section-sub">Detected issues across all SQLite records</span>
            </div>
            """
        )

        if not patients:
            st.info("No records in SQLite yet.")
        else:
            issues = [p for p in patients if p.get("validation_status") in ("Invalid", "Needs Review")]
            if not issues:
                st.success("All patient records currently in SQLite are Valid.")
            else:
                audit_df = pd.DataFrame(
                    [
                        {
                            "Record ID": p["id"],
                            "Full Name": p["full_name"],
                            "DOB": p["dob"],
                            "Email": p["email"],
                            "Source": p.get("record_source", "Manual"),
                            "Status": p.get("validation_status"),
                            "Detected Issues": p.get("validation_errors"),
                        }
                        for p in issues
                    ]
                )
                st.dataframe(audit_df, use_container_width=True, hide_index=True)

        # Duplicate Name & Email Manager (View & Delete)
        render_html(
            """
            <div class="hs-section-header">
                <h2 class="hs-section-title">Duplicate Name & Email Manager</h2>
                <span class="hs-section-sub">Inspect and remove duplicate patient entries</span>
            </div>
            """
        )

        dup_info = analyze_name_and_email_duplicates(patients)
        flagged_dups = dup_info["flagged_records"]

        if not flagged_dups:
            st.success("No duplicate patient names or duplicate email addresses found.")
        else:
            st.warning(
                f"Detected **{dup_info['duplicate_name_records']}** record(s) with duplicate names and "
                f"**{dup_info['duplicate_email_records']}** record(s) with duplicate emails. "
                "Keeping duplicates can cause clinical record mix-ups and distort analytics."
            )
            dup_df = pd.DataFrame(
                [
                    {
                        "Record ID": r["id"],
                        "Full Name": r["full_name"],
                        "Email": r["email"],
                        "DOB": r["dob"],
                        "Source": r.get("record_source", "Manual"),
                        "Duplicate Type": r["duplicate_reason"],
                    }
                    for r in flagged_dups
                ]
            )
            st.dataframe(dup_df, use_container_width=True, hide_index=True)

            dup_options = {
                f"#{r['id']} — {r['full_name']} ({r['email']}) [{r['duplicate_reason']}]": r["id"]
                for r in flagged_dups
            }
            selected_dup_label = st.selectbox(
                "Select Duplicate Record to Delete",
                list(dup_options.keys()),
                key="dup_delete_select",
            )
            selected_dup_id = dup_options[selected_dup_label]
            confirm_dup_del = st.checkbox(
                f"I confirm deleting duplicate Record #{selected_dup_id} from SQLite.",
                key="confirm_dup_del_box",
            )
            if st.button(
                "Delete Selected Duplicate",
                icon=":material/delete:",
                type="primary",
                disabled=not confirm_dup_del,
                key="btn_delete_dup",
            ):
                delete_patient(selected_dup_id)
                refresh_all_quality()
                st.success(f"Duplicate Record #{selected_dup_id} deleted successfully.")
                st.rerun()


# ---------------- AI HEALTH INSIGHTS ----------------

elif page == "AI Health Insights":
    render_html(
        """
        <div class="hs-page-header">
            <h1 class="hs-page-title">AI Health Insights</h1>
            <p class="hs-page-sub">Generate cautious, educational health observations using the configured AI API.</p>
        </div>
        """
    )

    if not is_ai_configured():
        st.warning(
            "AI API configuration is currently incomplete. Set `AI_API_KEY`, `AI_API_URL`, and `AI_MODEL` "
            "in your `.env` file to enable live AI generation. Saved remarks can still be viewed below."
        )

    patients = get_all_patients()

    if not patients:
        st.info("No patients available for analysis. Please register a patient or import the assignment dataset first.")
        c1, c2, _ = st.columns([1.2, 1.8, 3.0])
        with c1:
            if st.button("Add Patient", icon=":material/person_add:", type="primary", use_container_width=True):
                navigate_to("Add Patient")
        with c2:
            if st.button("Import Assignment Data", icon=":material/upload_file:", use_container_width=True):
                navigate_to("Patient Records", "Data Quality & Assignment Import")
    else:
        options = {f"#{p['id']} — {p['full_name']} ({p['email']})": p for p in patients}
        selected_key = st.selectbox("Select Patient", list(options.keys()))
        selected_patient = options[selected_key]

        # Patient Summary + Laboratory Values
        render_html(
            f"""
            <div class="hs-panel-card">
                <div class="hs-panel-title">Patient Summary — #{selected_patient['id']} {selected_patient['full_name']}</div>
                <div class="hs-spec-row"><span class="hs-spec-key">Date of Birth</span><span class="hs-spec-val">{selected_patient['dob']}</span></div>
                <div class="hs-spec-row"><span class="hs-spec-key">Email</span><span class="hs-spec-val">{selected_patient['email']}</span></div>
                <div class="hs-spec-row"><span class="hs-spec-key">Data Quality Status</span><span class="hs-spec-val">{selected_patient.get('validation_status', 'Valid')}</span></div>
                <div class="hs-spec-row"><span class="hs-spec-key">Last AI Analysis</span><span class="hs-spec-val">{selected_patient.get('ai_analyzed_at') or 'Not yet analyzed'}</span></div>
            </div>
            """
        )

        b1, b2, b3 = st.columns(3)
        with b1:
            render_html(
                f"""
                <div class="hs-metric-card">
                    <div class="hs-metric-label">Glucose</div>
                    <div class="hs-metric-value" style="margin-top:8px;">{selected_patient['glucose']}</div>
                    <div class="hs-metric-foot"><span class="hs-trend-pill hs-trend-teal">Lab Value</span><span>Recorded value</span></div>
                </div>
                """
            )
        with b2:
            render_html(
                f"""
                <div class="hs-metric-card">
                    <div class="hs-metric-label">Haemoglobin</div>
                    <div class="hs-metric-value" style="margin-top:8px;">{selected_patient['haemoglobin']}</div>
                    <div class="hs-metric-foot"><span class="hs-trend-pill hs-trend-teal">Lab Value</span><span>Recorded value</span></div>
                </div>
                """
            )
        with b3:
            render_html(
                f"""
                <div class="hs-metric-card">
                    <div class="hs-metric-label">Cholesterol</div>
                    <div class="hs-metric-value" style="margin-top:8px;">{selected_patient['cholesterol']}</div>
                    <div class="hs-metric-foot"><span class="hs-trend-pill hs-trend-teal">Lab Value</span><span>Recorded value</span></div>
                </div>
                """
            )

        render_html("<div style='height: 14px;'></div>")

        if st.button("Generate AI Health Insights", icon=":material/auto_awesome:", type="primary"):
            with st.spinner("Sending laboratory values to configured AI service..."):
                result = generate_health_insights(selected_patient)

            if not result["ok"]:
                st.error(result["error"])
            else:
                save_ai_analysis(selected_patient["id"], result["content"], result.get("model", ""))
                st.success("AI Health Insights generated and saved to SQLite.")
                st.rerun()

        current_remarks = (selected_patient.get("remarks") or "").strip()
        st.markdown("### AI Observation Report")
        if current_remarks:
            st.markdown(current_remarks)
        else:
            st.info(
                "No AI observations saved for this patient yet. Click **Generate AI Health Insights** above "
                "to run an analysis via your configured AI endpoint."
            )

        history = get_ai_analyses_for_patient(selected_patient["id"])
        if history:
            with st.expander(f"Previous Analysis History ({len(history)})"):
                for entry in history:
                    st.caption(f"Timestamp: {entry['created_at']} · Model: {entry.get('model_name') or 'Configured API'}")
                    st.markdown(entry["remarks"])
                    st.markdown("---")

        st.caption(
            "Medical Disclaimer: AI-generated remarks are general educational information only and are not a medical diagnosis. "
            "Laboratory values require proper clinical context; please consult a qualified healthcare professional."
        )
