import base64
from pathlib import Path
import re
import streamlit as st


def get_image_base64(image_path: str) -> str:
    """Return a base64 data URI string for a local image file, or empty string if missing."""
    path = Path(image_path)
    if not path.exists():
        return ""
    suffix = path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{mime};base64,{data}"


def render_html(html: str) -> None:
    """Render HTML via st.markdown after stripping leading line indentation to avoid Markdown code blocks."""
    cleaned = re.sub(r"^[ \t]+", "", html.strip(), flags=re.MULTILINE)
    st.markdown(cleaned, unsafe_allow_html=True)


SVG_ICONS = {
    "logo": (
        '<svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="hsLogoGrad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">'
        '<stop offset="0%" stop-color="#2DD4BF"/><stop offset="100%" stop-color="#0D9488"/>'
        '</linearGradient></defs>'
        '<rect width="36" height="36" rx="10" fill="url(#hsLogoGrad)"/>'
        '<path d="M8 18.5H12.5L15.2 12L19.2 24L22.2 16.2L24.5 18.5H28" stroke="#081424" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    ),
    "patients": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
    ),
    "ai": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 2a4 4 0 0 1 4 4v1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3v1a4 4 0 0 1-8 0v-1a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3V6a4 4 0 0 1 4-4z"/>'
        '<path d="M9 10h.01"/><path d="M15 10h.01"/><path d="M9.5 14a3.5 3.5 0 0 0 5 0"/></svg>'
    ),
    "records": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
    ),
    "pulse": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
    ),
    "database": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
    ),
    "insights": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>'
    ),
    "calendar": (
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
    ),
}


def inject_design_system(hero_bg_data_uri: str = "") -> None:
    """Inject the complete HealthSync AI SaaS CSS design system."""
    hero_bg_rule = (
        f"background-image: linear-gradient(96deg, rgba(8, 20, 38, 0.94) 0%, "
        f"rgba(11, 28, 50, 0.85) 48%, rgba(13, 148, 136, 0.28) 100%), "
        f"url('{hero_bg_data_uri}');"
        if hero_bg_data_uri
        else "background: linear-gradient(120deg, #091628 0%, #0F2942 55%, #0D6E6E 100%);"
    )

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {{
    --hs-navy-950: #081424;
    --hs-navy-900: #0B192C;
    --hs-navy-800: #112540;
    --hs-teal-600: #0D9488;
    --hs-teal-700: #0F766E;
    --hs-aqua-400: #2DD4BF;
    --hs-mint-50: #F0FDFA;
    --hs-mint-100: #CCFBF1;
    --hs-bg: #F4F7FA;
    --hs-surface: #FFFFFF;
    --hs-text: #0F172A;
    --hs-muted: #64748B;
    --hs-border: #E2E8F0;
}}

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--hs-text);
}}

h1, h2, h3, .hs-display {{
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    letter-spacing: -0.02em;
}}

/* Hide default Streamlit white top bar & chrome while keeping sidebar expand button usable */
header[data-testid="stHeader"] {{
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: visible !important;
    pointer-events: none !important;
}}
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer {{
    display: none !important;
    visibility: hidden !important;
}}
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {{
    pointer-events: auto !important;
    top: 0.85rem !important;
    left: 0.85rem !important;
    z-index: 1000 !important;
    background: #FFFFFF !important;
    border: 1px solid var(--hs-border) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08) !important;
}}

/* Main App Canvas */
.stApp {{
    background:
        radial-gradient(circle at 92% 6%, rgba(45, 212, 191, 0.09) 0%, transparent 32%),
        radial-gradient(circle at 12% 90%, rgba(13, 148, 136, 0.06) 0%, transparent 36%),
        #F4F7FA;
}}

.block-container {{
    padding-top: 1.35rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 1440px !important;
}}

/* ---------------- SIDEBAR ---------------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #081424 0%, #0D1E36 58%, #09182C 100%) !important;
    border-right: 1px solid rgba(45, 212, 191, 0.12) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.4rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(148, 163, 184, 0.16) !important;
    margin: 1rem 0 !important;
}}

.hs-sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 4px 10px 4px;
}}
.hs-sidebar-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 19px;
    font-weight: 800;
    color: #F8FAFC !important;
    letter-spacing: -0.02em;
    line-height: 1.15;
}}
.hs-sidebar-title span {{
    color: #2DD4BF !important;
}}
.hs-sidebar-tagline {{
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7FA3C4 !important;
    margin-top: 2px;
}}
.hs-nav-label {{
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: #6482A1 !important;
    padding: 4px 8px 8px 8px;
}}

/* Sidebar Navigation Buttons */
[data-testid="stSidebar"] .stButton > button {{
    width: 100%;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 11px !important;
    padding: 0.65rem 0.95rem !important;
    min-height: 44px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin-bottom: 4px !important;
}}
[data-testid="stSidebar"] .stButton > button > div {{
    justify-content: flex-start !important;
    width: 100%;
    gap: 10px;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #CBD5E1 !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
    background: rgba(255, 255, 255, 0.06) !important;
    border-color: rgba(148, 163, 184, 0.16) !important;
    color: #FFFFFF !important;
    transform: translateX(2px);
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: linear-gradient(90deg, rgba(20, 184, 166, 0.22) 0%, rgba(13, 148, 136, 0.08) 100%) !important;
    border: 1px solid rgba(45, 212, 191, 0.35) !important;
    border-left: 3.5px solid #2DD4BF !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 18px rgba(45, 212, 191, 0.14) !important;
}}

.hs-sidebar-footer {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 14px;
    padding: 14px 14px;
    margin-top: 8px;
}}
.hs-status-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #E2E8F0 !important;
    font-size: 13px;
    font-weight: 600;
    margin-top: 6px;
}}
.hs-dot-green {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.22);
    display: inline-block;
    flex-shrink: 0;
}}
.hs-version-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(148, 163, 184, 0.14);
    font-size: 11.5px;
    color: #8BA4BF !important;
}}

/* ---------------- CUSTOM TOP HEADER ---------------- */
.hs-topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(240, 253, 250, 0.88) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 16px;
    padding: 13px 22px;
    margin-bottom: 22px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
}}
.hs-topbar-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}
.hs-topbar-brand {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: #0B192C;
    line-height: 1.15;
}}
.hs-topbar-brand span {{
    color: #0D9488;
}}
.hs-topbar-sub {{
    font-size: 12.5px;
    color: #64748B;
    font-weight: 500;
    margin-top: 1px;
}}
.hs-topbar-right {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}}
.hs-pill {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 13px;
    border-radius: 999px;
    font-size: 12.5px;
    font-weight: 600;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    color: #334155;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
}}
.hs-pill-status {{
    background: #ECFDF5;
    border-color: #A7F3D0;
    color: #065F46;
}}

/* ---------------- HERO SECTION ---------------- */
.hs-hero {{
    {hero_bg_rule}
    background-size: cover;
    background-position: center right;
    border-radius: 20px;
    padding: 36px 38px;
    margin-bottom: 16px;
    border: 1px solid rgba(45, 212, 191, 0.22);
    box-shadow: 0 16px 38px rgba(8, 20, 36, 0.14);
    position: relative;
    overflow: hidden;
}}
.hs-hero-content {{
    max-width: 620px;
    position: relative;
    z-index: 2;
}}
.hs-hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(45, 212, 191, 0.14);
    border: 1px solid rgba(45, 212, 191, 0.35);
    color: #5EEAD4 !important;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 999px;
    margin-bottom: 14px;
}}
.hs-hero .hs-hero-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 33px;
    font-weight: 800;
    color: #FFFFFF !important;
    line-height: 1.18;
    letter-spacing: -0.025em;
    margin: 0 0 10px 0;
}}
.hs-hero .hs-hero-desc {{
    font-size: 15px;
    line-height: 1.6;
    color: #E2E8F0 !important;
    margin: 0;
}}

/* ---------------- METRIC CARDS ---------------- */
.hs-metric-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.035);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    height: 100%;
    position: relative;
    overflow: hidden;
}}
.hs-metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    border-color: rgba(13, 148, 136, 0.35);
}}
.hs-metric-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}}
.hs-metric-label {{
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
}}
.hs-icon-badge {{
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}
.hs-badge-teal {{ background: #F0FDFA; color: #0D9488; border: 1px solid #CCFBF1; }}
.hs-badge-aqua {{ background: #ECFEFF; color: #0891B2; border: 1px solid #CFFAFE; }}
.hs-badge-navy {{ background: #F1F5F9; color: #1E3A5F; border: 1px solid #CBD5E1; }}
.hs-badge-mint {{ background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }}

.hs-metric-value {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 30px;
    font-weight: 800;
    color: #0B192C;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    margin-bottom: 8px;
}}
.hs-metric-foot {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
}}
.hs-trend-pill {{
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
}}
.hs-trend-teal {{ background: #F0FDFA; color: #0F766E; }}
.hs-trend-green {{ background: #ECFDF5; color: #047857; }}
.hs-trend-slate {{ background: #F1F5F9; color: #475569; }}

/* ---------------- SECTION TITLES ---------------- */
.hs-section-header {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin: 26px 0 14px 0;
}}
.hs-section-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 19px;
    font-weight: 700;
    color: #0B192C;
    margin: 0;
}}
.hs-section-sub {{
    font-size: 13px;
    color: #64748B;
}}

/* ---------------- WORKSPACE FEATURE CARDS ---------------- */
.hs-feature-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 22px 24px 18px 24px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    margin-bottom: 10px;
    position: relative;
}}
.hs-feature-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.075);
    border-color: rgba(13, 148, 136, 0.38);
}}
.hs-feature-head {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}}
.hs-feature-tag {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #0D9488;
    background: #F0FDFA;
    border: 1px solid #CCFBF1;
    padding: 3px 10px;
    border-radius: 999px;
}}
.hs-feature-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 17.5px;
    font-weight: 700;
    color: #0B192C;
    margin-bottom: 6px;
}}
.hs-feature-desc {{
    font-size: 13.5px;
    line-height: 1.55;
    color: #64748B;
    min-height: 42px;
}}

/* ---------------- INFO / SIDE PANEL CARDS ---------------- */
.hs-panel-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
    margin-bottom: 16px;
}}
.hs-panel-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #0B192C;
    margin-bottom: 12px;
}}
.hs-spec-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #F1F5F9;
    font-size: 13.5px;
}}
.hs-spec-row:last-child {{
    border-bottom: none;
    padding-bottom: 0;
}}
.hs-spec-key {{ color: #64748B; font-weight: 500; }}
.hs-spec-val {{ color: #0B192C; font-weight: 600; }}

/* ---------------- NATIVE WIDGET POLISH ---------------- */
div.stButton > button {{
    border-radius: 11px !important;
    min-height: 42px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.18s ease !important;
}}
div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(13, 148, 136, 0.28) !important;
}}
div.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(13, 148, 136, 0.36) !important;
}}
div.stButton > button[kind="secondary"] {{
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
}}
div.stButton > button[kind="secondary"]:hover {{
    border-color: #0D9488 !important;
    color: #0F766E !important;
    background: #F0FDFA !important;
}}

div[data-testid="stForm"] {{
    background: #FFFFFF !important;
    padding: 26px !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.035) !important;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    background: #FFFFFF !important;
}}

[data-testid="stVerticalBlockBorderWrapper"] {{
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px !important;
    padding: 4px 6px !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03) !important;
}}

/* ---------------- STARTUP SPLASH INTRO ---------------- */
.hs-splash-overlay {{
    position: fixed;
    inset: 0;
    z-index: 999999;
    background: radial-gradient(circle at 50% 45%, #0B1B30 0%, #050B14 55%, #000000 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 24px;
    animation: hsSplashFadeIn 0.35s ease-out forwards;
}}
.hs-splash-logo {{
    width: 82px;
    height: 82px;
    border-radius: 22px;
    background: linear-gradient(135deg, #2DD4BF 0%, #0D9488 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 40px rgba(45, 212, 191, 0.38), 0 0 80px rgba(13, 148, 136, 0.22);
    animation: hsLogoPop 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards, hsPulseGlow 2s ease-in-out infinite;
    margin-bottom: 24px;
}}
.hs-splash-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 42px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.03em;
    margin: 0 0 8px 0;
    opacity: 0;
    animation: hsFadeUp 0.65s ease-out 0.18s forwards;
}}
.hs-splash-title span {{
    color: #2DD4BF;
}}
.hs-splash-sub {{
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 30px;
    opacity: 0;
    animation: hsFadeUp 0.65s ease-out 0.32s forwards;
}}
.hs-splash-bar-wrap {{
    width: 240px;
    height: 4px;
    background: rgba(148, 163, 184, 0.18);
    border-radius: 999px;
    overflow: hidden;
    opacity: 0;
    animation: hsFadeUp 0.5s ease-out 0.4s forwards;
}}
.hs-splash-bar-fill {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #0D9488 0%, #2DD4BF 60%, #99F6E4 100%);
    border-radius: 999px;
    animation: hsLoadBar 2.3s cubic-bezier(0.4, 0, 0.2, 1) 0.25s forwards;
}}
@keyframes hsSplashFadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}
@keyframes hsLogoPop {{
    from {{ opacity: 0; transform: scale(0.72); }}
    to {{ opacity: 1; transform: scale(1); }}
}}
@keyframes hsPulseGlow {{
    0%, 100% {{ box-shadow: 0 0 35px rgba(45, 212, 191, 0.35), 0 0 70px rgba(13, 148, 136, 0.2); }}
    50% {{ box-shadow: 0 0 55px rgba(45, 212, 191, 0.6), 0 0 100px rgba(13, 148, 136, 0.35); }}
}}
@keyframes hsFadeUp {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes hsLoadBar {{
    0% {{ width: 0%; }}
    100% {{ width: 100%; }}
}}

/* Page Title Banner for Inner Pages */
.hs-page-header {{
    margin-bottom: 18px;
}}
.hs-page-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: #0B192C;
    margin: 0 0 4px 0;
}}
.hs-page-sub {{
    font-size: 14.5px;
    color: #64748B;
    margin: 0;
}}

@media (max-width: 900px) {{
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    .hs-hero {{
        padding: 24px 22px;
    }}
    .hs-hero .hs-hero-title {{
        font-size: 24px;
    }}
}}
</style>
"""
    render_html(css)
