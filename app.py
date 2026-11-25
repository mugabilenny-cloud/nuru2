import base64, hashlib, html, io, os, re
from urllib.parse import quote
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import db
import importer
import icons
from icons import svg as ic

st.set_page_config(page_title="Nuru - Find your next opportunity", page_icon=":material/lightbulb:", layout="wide")
db.init()

PURPLE = "#6200B3"
def _cfg(name, default):
    v = os.environ.get(name, "")
    try:
        v = v or st.secrets.get(name, "")
    except Exception:
        pass
    return str(v or default)


WA_NUMBER = _cfg("NURU_WHATSAPP", "256791144968")      # international format, no "+"
WA_DISPLAY = "0791 144 968"


def wa_link(text="Hello Nuru, I need help.", number=None):
    return f"https://wa.me/{number or WA_NUMBER}?text={quote(text)}"


CATEGORY_FALLBACK = ["Banks & Finance", "Medical", "Schools & Education", "NGOs & Development",
                     "Engineering & Construction", "ICT & Tech", "Agriculture", "Internships", "Other"]

# ------------------------------------------------------------------ styling
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {{ font-family: 'Poppins', sans-serif !important; }}
#MainMenu, footer, header[data-testid="stHeader"] {{ display: none; }}
.block-container {{ padding-top: 1rem; max-width: 1180px; }}
.logo {{ font-size: 1.5rem; font-weight: 700; color: {PURPLE}; padding-top: .35rem; }}
.hero {{ background: linear-gradient(135deg,#F3EAFF 0%,#FFFFFF 100%); border-radius: 18px; padding: 3rem 2.5rem 2rem; margin: .8rem 0 1.5rem; }}
.hero h1 {{ font-size: 2.4rem; font-weight: 600; color:#2B2B2B; line-height:1.25; margin:0 0 .4rem; }}
.hero p {{ color:#666; margin:0; }}
.sec-title {{ text-align:center; font-weight:600; font-size:1.8rem; margin:2rem 0 .2rem; }}
.sec-sub {{ text-align:center; color:#666; margin-bottom:1.2rem; }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.jobcard) {{ background:#F6EFFF; border:1px solid #E6D8F7; border-radius:10px; }}
.jobcard .t {{ font-weight:500; font-size:1.02rem; color:#2B2B2B; }}
.jobcard .m {{ font-size:.78rem; color:#777; margin:.15rem 0; }}
.jobcard .c {{ font-size:.85rem; color:#444; margin-top:.4rem; }}
.badge {{ display:inline-block; font-size:.66rem; font-weight:600; padding:1px 8px; border-radius:4px; margin-right:6px; letter-spacing:.3px; }}
.b-Full-time {{ background:#E6D8F7; color:{PURPLE}; }} .b-Part-time {{ background:#D8F5DF; color:#13813A; }}
.b-Internship {{ background:#FFF1D1; color:#9A6200; }} .b-Contract {{ background:#D9ECFF; color:#0B5CAD; }}
.b-Scholarship {{ background:#FFE0EC; color:#B0124F; }} .b-closed {{ background:#FDE0E0; color:#B00020; }}
.chip {{ display:inline-block; background:#fff; border:1px solid #E6D8F7; border-radius:20px; padding:4px 14px; margin:3px; font-size:.85rem; color:#444; }}
.stButton > button, .stFormSubmitButton > button, .stLinkButton > a {{ border-radius:6px; font-weight:500; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background:{PURPLE}; border-color:{PURPLE}; color:#fff; }}
.stButton > button[kind="secondary"] {{ border-color:{PURPLE}; color:{PURPLE}; background:#fff; }}
.footer {{ background:#F3EAFF; border-radius:14px; padding:1.6rem 2rem; margin-top:3rem; color:#555; font-size:.85rem; }}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ design system v2 (images + icons)
STATIC = Path(__file__).parent / "static"
HERO = ["clipboard", "tablet", "jobs", "office"]
P = "#6200B3"


def extra_css():
    slides = "".join(f".hero2 .s{i}{{background-image:url(/app/static/{n}.jpg);animation-delay:{i*6}s}}"
                     f".hero2 .d{i}{{animation-delay:{i*6}s}}" for i, n in enumerate(HERO))
    ib = [("nav_home", "house"), ("nav_find", "briefcase-business"), ("nav_post", "circle-plus"),
          ("nav_dash", "layout-dashboard"), ("nav_about", "info"), ("nav_reg", "user-plus"),
          ("nav_login", "log-in"), ("nav_logout", "log-out"), ("find_btn", "search"), ("search_btn", "search"),
          ("viewall_btn", "arrow-right"), ("goto_dash", "layout-dashboard"), ("firstjob", "circle-plus"),
          ("login_post", "log-in"), ("login_dash", "log-in"), ("dl_tpl", "download"), ("dl_export", "download"), ("dl_hub", "file-spreadsheet"),
          ("import_btn", "upload")]
    icon_css = "".join(icons.mask_rule(f".st-key-{k} button", n) for k, n in ib)
    icon_css += icons.mask_rule('[class*="st-key-v_"] button', "eye")
    icon_css += icons.mask_rule('[class*="st-key-a_"] button', "send")
    icon_css += icons.mask_rule('[class*="st-key-close_"] button', "circle-x")
    icon_css += icons.mask_rule('[class*="st-key-reopen_"] button', "rotate-ccw")
    icon_css += icons.mask_rule('[class*="st-key-del_"] button', "trash-2")
    for i, n in enumerate(["clipboard-list", "inbox", "upload"], start=1):
        icon_css += icons.mask_rule(f'div[data-baseweb="tab-list"] button:nth-of-type({i})', n)
    return f"""<style>
.logo{{display:flex;align-items:center;gap:.5rem;padding-top:.15rem;letter-spacing:-.3px}}
.logo .tile{{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#8A2BE2,#4A0090);color:#fff;display:grid;place-items:center}}
.hero2{{position:relative;overflow:hidden;border-radius:20px;min-height:380px;background:#2A0058;margin:.6rem 0 0;color:#fff}}
.hero2 .slide{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;animation:nuruFade 24s infinite}}
.hero2::before{{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,rgba(38,0,80,.92) 0%,rgba(60,0,120,.62) 52%,rgba(60,0,120,.25) 100%)}}
.hero2 .hero-in{{position:relative;z-index:2;padding:3.2rem 3rem 5.2rem;max-width:720px}}
.hero2 h1{{font-size:2.6rem;font-weight:600;line-height:1.2;margin:.9rem 0 .7rem;color:#fff}}
.hero2 p{{color:rgba(255,255,255,.88);font-size:1.02rem;margin:0}}
.eyebrow{{display:inline-flex;align-items:center;gap:.45rem;background:rgba(255,255,255,.16);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.28);padding:.3rem .8rem;border-radius:99px;font-size:.78rem;font-weight:500}}
.hero2 .dots{{position:absolute;z-index:2;right:1.6rem;bottom:3.4rem;display:flex;gap:6px}}
.hero2 .dots i{{width:22px;height:4px;border-radius:4px;background:rgba(255,255,255,.35);animation:nuruDot 24s infinite}}
@keyframes nuruFade{{0%{{opacity:0;transform:scale(1)}}4%{{opacity:1}}25%{{opacity:1}}29%{{opacity:0;transform:scale(1.07)}}100%{{opacity:0}}}}
@keyframes nuruDot{{0%{{background:#fff;width:34px}}25%{{background:#fff;width:34px}}29%,100%{{background:rgba(255,255,255,.35);width:22px}}}}
{slides}
@media (prefers-reduced-motion:reduce){{.hero2 .slide,.hero2 .dots i{{animation:none}}.hero2 .s0{{opacity:1}}}}
@media (max-width:640px){{.hero2 .hero-in{{padding:2rem 1.3rem 4.6rem}}.hero2 h1{{font-size:1.8rem}}}}
.st-key-heroSearch{{margin:-3rem 1.6rem 1rem;background:#fff;border-radius:16px;padding:.9rem 1rem .4rem;box-shadow:0 16px 40px rgba(60,0,110,.20);position:relative;z-index:3}}
.banner{{position:relative;overflow:hidden;border-radius:16px;padding:2rem 2.2rem;margin:.2rem 0 1.4rem;color:#fff;background-size:cover;background-position:center 30%;background-color:#2A0058}}
.banner::before{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(38,0,80,.9),rgba(60,0,120,.45))}}
.banner>*{{position:relative}}
.banner h2{{color:#fff;margin:0;font-size:1.9rem;font-weight:600;padding:0}}
.banner p{{margin:.3rem 0 0;color:rgba(255,255,255,.88)}}
.authpanel{{position:relative;overflow:hidden;border-radius:18px;min-height:520px;padding:2rem;color:#fff;display:flex;flex-direction:column;justify-content:flex-end;background-size:cover;background-position:center}}
.authpanel::before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(38,0,80,.15) 0%,rgba(38,0,80,.92) 100%)}}
.authpanel>*{{position:relative}}
.authpanel h3{{color:#fff;font-size:1.5rem;font-weight:600;margin:0 0 .8rem}}
.authpanel .pt{{display:flex;align-items:center;gap:.6rem;margin:.35rem 0;font-size:.92rem}}
.stat{{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #E6D8F7;border-radius:14px;padding:1rem 1.2rem}}
.stat .ico{{width:46px;height:46px;border-radius:12px;background:#F3EAFF;color:{P};display:grid;place-items:center;flex:none}}
.stat b{{font-size:1.6rem;display:block;line-height:1.1;color:#2B2B2B}}
.stat .l{{color:#666;font-size:.8rem}}
.jobcard .m svg{{color:#8A6BB8;margin-right:2px}}
.jobcard .m .dot{{opacity:.4;margin:0 6px}}
.footer .fl{{display:flex;align-items:center;gap:.5rem;color:{P};font-weight:600;font-size:1rem;margin-bottom:.4rem}}
.st-key-q input,.st-key-loc input{{padding-left:2.6rem !important;background-repeat:no-repeat;background-position:.85rem center;background-size:1.1rem}}
.st-key-q input{{background-image:url({icons.data_uri("search", P)})}}
.st-key-loc input{{background-image:url({icons.data_uri("map-pin", P)})}}
{icon_css}
</style>"""


st.markdown(extra_css(), unsafe_allow_html=True)

def theme_css():
    P = PURPLE
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{{background:#FFFFFF !important;color:#334155}}
html,body,[class*="css"],.stMarkdown,button,input,textarea,select{{font-family:'Inter',system-ui,sans-serif !important}}
h1,h2,h3,.sec-title,.banner h2,.hero2 h1,.logo,.authpanel h3,.jc-t,.stat b{{font-family:'Poppins','Inter',sans-serif !important}}
h1,h2,h3,h4{{color:#0F172A}} p,li,label,.stMarkdown{{color:#334155}}
.block-container{{max-width:1200px;padding-top:.8rem}}
.sec-title{{color:#0F172A;font-size:1.9rem;margin:3rem 0 .3rem}}
.sec-title::after{{content:"";display:block;width:56px;height:4px;border-radius:4px;margin:.6rem auto 0;background:linear-gradient(90deg,{P},#F59E0B)}}
.sec-sub{{color:#475569;font-size:1rem;margin-bottom:1.4rem}}
hr{{border-color:#E2E8F0 !important}}

/* ---- job card */
[class*="st-key-card_"]{{background:#fff;border:1px solid #E2E8F0;border-radius:18px;padding:1.15rem 1.2rem 1rem;position:relative;overflow:hidden;
  box-shadow:0 1px 2px rgba(15,23,42,.05);transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease}}
[class*="st-key-card_"]::before{{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,{P},#A855F7)}}
[class*="st-key-card_"]:has(.jc.sch)::before{{background:linear-gradient(90deg,#DB2777,#F59E0B)}}
[class*="st-key-card_"]:hover{{transform:translateY(-4px);border-color:#C4B5FD;box-shadow:0 18px 40px rgba(98,0,179,.16)}}
.jc-top{{display:flex;gap:12px;align-items:flex-start}}
.av{{width:48px;height:48px;border-radius:14px;color:#fff;display:grid;place-items:center;font-weight:700;font-size:1rem;flex:none;letter-spacing:.5px;box-shadow:0 6px 14px rgba(15,23,42,.18)}}
.jc-h{{flex:1;min-width:0}}
.jc-t{{font-weight:600;font-size:1.08rem;line-height:1.3;color:#0F172A;margin:0}}
.jc-c{{font-size:.88rem;color:#475569;margin-top:3px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center}}
.jc-c svg{{color:{P};margin-right:3px}}
.pill{{flex:none;font-size:.7rem;font-weight:700;padding:4px 10px;border-radius:99px;letter-spacing:.3px;text-transform:uppercase}}
.jc-d{{color:#1E293B;font-size:.93rem;line-height:1.6;margin:.85rem 0 .7rem;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;min-height:4.4em}}
.jc-sal{{display:inline-flex;align-items:center;gap:6px;font-weight:600;color:#065F46;background:#ECFDF5;border:1px solid #A7F3D0;padding:4px 10px;border-radius:10px;font-size:.84rem;margin-bottom:.55rem}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:.8rem}}
.tag{{display:inline-flex;align-items:center;gap:5px;font-size:.78rem;font-weight:500;padding:4px 10px;border-radius:99px;background:#F1F5F9;color:#334155;border:1px solid #E2E8F0}}
.tag.ok{{background:#ECFDF5;color:#065F46;border-color:#A7F3D0}} .tag.warn{{background:#FFFBEB;color:#92400E;border-color:#FDE68A}}
.tag.bad{{background:#FEF2F2;color:#991B1B;border-color:#FECACA}} .tag.new{{background:{P};color:#fff;border-color:{P}}}
.p-Full-time{{background:#EDE9FE;color:#5B21B6}} .p-Part-time{{background:#DCFCE7;color:#166534}} .p-Internship{{background:#FEF3C7;color:#92400E}}
.p-Contract{{background:#DBEAFE;color:#1E40AF}} .p-Scholarship{{background:#FCE7F3;color:#9D174D}}

/* ---- dialog facts */
.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:1rem 0}}
.fact{{border:1px solid #E2E8F0;border-radius:14px;padding:.7rem .9rem;background:#fff}}
.fact .k{{display:flex;align-items:center;gap:6px;font-size:.72rem;text-transform:uppercase;letter-spacing:.6px;color:#64748B;font-weight:600}}
.fact .k svg{{color:{P}}} .fact .v{{font-weight:600;color:#0F172A;margin-top:3px;font-size:.95rem}}
.desc-list{{margin:.4rem 0 1rem;padding-left:1.2rem}} .desc-list li{{color:#1E293B;line-height:1.7;margin:.2rem 0;font-size:.97rem}}
.desc-list li::marker{{color:{P}}}
h5.sub{{display:flex;align-items:center;gap:8px;margin:1rem 0 .2rem;color:#0F172A;font-size:1rem;font-weight:600}}

/* ---- panels, inputs, buttons */
.st-key-filterpanel{{background:#fff;border:1px solid #E2E8F0;border-radius:18px;padding:1.1rem 1.1rem .6rem;box-shadow:0 1px 2px rgba(15,23,42,.05)}}
.fp-h{{display:flex;align-items:center;gap:8px;font-weight:600;color:#0F172A;font-size:1.02rem}} .fp-h svg{{color:{P}}}
.res-h{{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:.2rem 0 1rem}}
.res-h b{{font-family:'Poppins';font-size:1.35rem;color:#0F172A;margin-right:6px}}
.chip-x{{display:inline-flex;align-items:center;gap:5px;background:#F5F3FF;color:#5B21B6;border:1px solid #DDD6FE;border-radius:99px;padding:3px 10px;font-size:.78rem;font-weight:500}}
div[data-baseweb="input"],div[data-baseweb="select"]>div,div[data-baseweb="textarea"],[data-testid="stDateInput"] div[data-baseweb="input"]{{background-color:#fff !important;border:1px solid #CBD5E1 !important;border-radius:12px !important}}
div[data-baseweb="input"] input,div[data-baseweb="textarea"] textarea{{background-color:transparent !important;color:#0F172A !important}}
div[data-baseweb="input"]:focus-within,div[data-baseweb="select"]>div:focus-within,div[data-baseweb="textarea"]:focus-within{{border-color:{P} !important;box-shadow:0 0 0 3px rgba(98,0,179,.18) !important}}
input::placeholder,textarea::placeholder{{color:#64748B !important;opacity:1 !important}}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,.stLinkButton>a{{border-radius:12px !important;min-height:42px;font-weight:600 !important;transition:transform .15s ease,box-shadow .15s ease,background .15s ease}}
.stButton>button:hover,.stFormSubmitButton>button:hover{{transform:translateY(-1px);box-shadow:0 8px 18px rgba(98,0,179,.22)}}
.stButton>button:focus-visible,.stFormSubmitButton>button:focus-visible{{outline:3px solid rgba(98,0,179,.35);outline-offset:2px}}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],.stLinkButton>a[kind="primary"],[data-testid="stBaseButton-primary"]{{background:linear-gradient(135deg,#7C2AE8,#5B00A8) !important;border:0 !important;color:#fff !important}}
.stButton>button[kind="secondary"],[data-testid="stBaseButton-secondary"]{{background:#fff !important;border:1.5px solid #D8C8F0 !important;color:#5B21B6 !important}}
.stButton>button[kind="secondary"]:hover,[data-testid="stBaseButton-secondary"]:hover{{border-color:{P} !important;background:#FAF5FF !important}}
[data-testid="stMetric"]{{background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:.9rem 1.1rem;box-shadow:0 1px 2px rgba(15,23,42,.05)}}
[data-testid="stMetricLabel"] p{{color:#475569 !important;font-weight:500}} [data-testid="stMetricValue"]{{color:#0F172A}}
button[role="tab"] p{{font-weight:600}} button[role="tab"][aria-selected="true"]{{color:{P}}}
.chip{{background:#fff;border:1px solid #E2E8F0;color:#334155;font-weight:500;box-shadow:0 1px 2px rgba(15,23,42,.04)}}
.stat{{border-color:#E2E8F0;box-shadow:0 1px 2px rgba(15,23,42,.05)}} .stat .ico{{background:#F5F3FF}} .stat .l{{color:#475569}}

/* ---- category tiles */
[class*="st-key-cat_"] button{{justify-content:flex-start;text-align:left;min-height:64px;border-radius:16px !important;padding:.6rem 1rem !important;width:100%}}
[class*="st-key-cat_"] button p{{font-size:.95rem;color:#0F172A;font-weight:600}}
[class*="st-key-cat_"] button p::before{{width:1.5em !important;height:1.5em !important;color:{P}}}

/* ---- footer + banner tweaks */
.footer{{background:#0F172A;color:#CBD5E1;border-radius:20px;padding:2rem 2.2rem;margin-top:3.5rem;font-size:.88rem;line-height:1.8}}
.footer .fl{{color:#fff;font-size:1.15rem}} .footer svg{{color:#C4B5FD}}
.banner.tall{{padding-bottom:4.2rem}}
.banner p{{color:rgba(255,255,255,.92)}}
</style>"""


st.markdown(theme_css(), unsafe_allow_html=True)

def wa_css():
    return """<style>
.wa-fab{position:fixed;right:20px;bottom:calc(20px + env(safe-area-inset-bottom,0px));z-index:999;display:flex;align-items:center;gap:8px;
 background:#128C7E;color:#fff !important;text-decoration:none !important;font-weight:600;font-size:.9rem;padding:12px 18px;border-radius:99px;
 box-shadow:0 10px 28px rgba(18,140,126,.45);transition:transform .2s,box-shadow .2s}
.wa-fab:hover{transform:translateY(-3px);box-shadow:0 14px 32px rgba(18,140,126,.55)}
.wa-fab:focus-visible,.wa-btn:focus-visible{outline:3px solid #0B5D53;outline-offset:3px}
.wa-fab svg{color:#fff}
@media (max-width:640px){.wa-fab span{display:none}.wa-fab{padding:14px}}
.wa-row{display:flex;flex-wrap:wrap;gap:10px;margin:.4rem 0 1rem}
.wa-btn{display:inline-flex;align-items:center;gap:8px;text-decoration:none !important;font-weight:600;font-size:.9rem;padding:10px 16px;border-radius:12px;
 border:1.5px solid #128C7E;color:#0B5D53 !important;background:#fff;transition:background .15s}
.wa-btn:hover{background:#ECFDF5}.wa-btn.solid{background:#128C7E;color:#fff !important}.wa-btn.solid:hover{background:#0F766E}
.wa-btn.solid svg,.wa-btn svg{color:currentColor}
</style>"""


st.markdown(wa_css(), unsafe_allow_html=True)


def wa_buttons(listing=None):
    if listing:
        who = f' at {listing["company"]}' if listing["company"] else ""
        ask = wa_link(f'Hello Nuru, I am interested in "{listing["title"]}"{who} (listing #{listing["id"]}). Please help.')
        share = "https://wa.me/?text=" + quote(f'{listing["title"]}{who} - {listing["url"] or "found on Nuru"}')
        return (f'<div class="wa-row"><a class="wa-btn solid" href="{ask}" target="_blank" rel="noopener">{ic("message-circle", 18)} Ask on WhatsApp</a>'
                f'<a class="wa-btn" href="{share}" target="_blank" rel="noopener">{ic("share-2", 18)} Share on WhatsApp</a></div>')
    return (f'<div class="wa-row"><a class="wa-btn solid" href="{wa_link()}" target="_blank" rel="noopener">'
            f'{ic("message-circle", 18)} Chat on WhatsApp · {WA_DISPLAY}</a></div>')


def wa_fab():
    st.markdown(f'<a class="wa-fab" href="{wa_link()}" target="_blank" rel="noopener" aria-label="Chat with Nuru on WhatsApp">'
                f'{ic("message-circle", 22)}<span>Chat on WhatsApp</span></a>', unsafe_allow_html=True)


# ------------------------------------------------------------------ state / auth helpers
ss = st.session_state
ss.setdefault("page", "Home")
ss.setdefault("user", None)
ss.setdefault("limit", 8)


def go(page):
    ss.page = page


def admin_emails():
    raw = os.environ.get("NURU_ADMIN_EMAILS", "")
    try:
        raw = raw or st.secrets.get("ADMIN_EMAILS", "")
    except Exception:
        pass
    return {e.strip().lower() for e in str(raw).split(",") if e.strip()}


def is_admin():
    return bool(ss.user and ss.user["role"] == "admin")


def login_user(u):
    if u["email"] in admin_emails() and u["role"] != "admin":
        db.set_role(u["email"], "admin")
        u["role"] = "admin"
    ss.user = {k: u[k] for k in ("email", "name", "role")}


def banner(title, subtitle, img, tall=False):
    st.markdown(f'<div class="banner{" tall" if tall else ""}" style="background-image:url(/app/static/{img}.jpg)"><h2>{esc(title)}</h2>'
                f'<p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x or ""))


def fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return ""


def is_closed(row):
    if row["status"] == "closed":
        return True
    d = row["deadline"]
    return bool(d) and not pd.isna(d) and d < date.today().isoformat()


def salary_text(row):
    lo, hi, cur = row["salary_min"], row["salary_max"], row["currency"] or "UGX"
    lo = None if pd.isna(lo) else lo
    hi = None if pd.isna(hi) else hi
    if lo and hi:
        return f"{cur} {lo:,.0f} - {hi:,.0f}"
    if lo or hi:
        return f"{cur} {(lo or hi):,.0f}"
    return ""


# ------------------------------------------------------------------ shared UI
def navbar():
    items = [("Home", "nav_home"), ("Find Jobs", "nav_find"), ("Post a Job", "nav_post"),
             ("Dashboard", "nav_dash"), ("About", "nav_about")]
    cols = st.columns([1.5] + [1.1] * len(items) + [1.1, 1.1])
    cols[0].markdown(f'<div class="logo"><span class="tile">{ic("sparkles", 18, "#fff")}</span>Nuru</div>',
                     unsafe_allow_html=True)
    for i, (p, k) in enumerate(items, start=1):
        cols[i].button(p, key=k, on_click=go, args=(p,), use_container_width=True,
                       type="primary" if ss.page == p else "secondary")
    if ss.user:
        cols[-2].caption(f"Hi, {ss.user['name'].split()[0]}")
        if cols[-1].button("Logout", key="nav_logout", use_container_width=True):
            ss.user = None
            ss.page = "Home"
            st.rerun()
    else:
        cols[-2].button("Register", key="nav_reg", on_click=go, args=("Register",), use_container_width=True)
        cols[-1].button("Login", key="nav_login", on_click=go, args=("Login",), use_container_width=True, type="primary")
    st.divider()


def footer():
    st.markdown(f"""<div class="footer"><div class="fl">{ic("sparkles", 18, P)} Nuru</div>
    Jobs, internships and scholarships for Ugandans.<br>
    {ic("map-pin", 13)} Kampala, Uganda &nbsp;|&nbsp; {ic("message-circle", 13)} <a href="{wa_link()}" target="_blank" rel="noopener" style="color:#fff">WhatsApp {WA_DISPLAY}</a> &nbsp;|&nbsp; Always confirm deadlines and requirements on the official listing before applying.<br>
    © 2026 Nuru. All rights reserved.</div>""", unsafe_allow_html=True)


GRADS = [("#7C3AED", "#4C1D95"), ("#0284C7", "#0C4A6E"), ("#059669", "#064E3B"),
         ("#D97706", "#78350F"), ("#DB2777", "#831843"), ("#4F46E5", "#312E81")]


def initials(r):
    words = re.findall(r"[A-Za-z0-9]+", r["company"] or r["title"])
    return ("".join(w[0] for w in words[:2]) or "N").upper()


def avatar(r):
    a, b = GRADS[int(hashlib.md5((r["company"] or r["title"]).encode()).hexdigest(), 16) % len(GRADS)]
    return f'<div class="av" style="background:linear-gradient(135deg,{a},{b})">{esc(initials(r))}</div>'


def days_left(r):
    d = r["deadline"]
    if not d or pd.isna(d):
        return None
    try:
        return (datetime.strptime(d, "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None


def deadline_tag(r):
    n = days_left(r)
    if r["status"] == "closed" or (n is not None and n < 0):
        return f'<span class="tag bad">{ic("circle-x", 13)} Closed</span>'
    if n is None:
        return f'<span class="tag">{ic("calendar", 13)} No deadline stated</span>'
    if n == 0:
        return f'<span class="tag warn">{ic("flame", 13)} Closes today</span>'
    if n <= 7:
        return f'<span class="tag warn">{ic("hourglass", 13)} {n} day{"s" if n != 1 else ""} left</span>'
    return f'<span class="tag ok">{ic("calendar", 13)} Closes {fmt_date(r["deadline"])}</span>'


def sentences(r):
    """Description split into readable sentences, minus the location/deadline boilerplate shown elsewhere."""
    txt = (r["description"] or "").strip()
    out = []
    for p in re.split(r"(?<=[.!?])\s+", txt):
        p = p.strip()
        low = p.lower().rstrip(".")
        if not p or re.match(r"(closes|deadline|no closing)", low):
            continue
        if low == str(r["location"] or "").lower().rstrip("."):
            continue
        out.append(p)
    return out


def excerpt(r, n=240):
    t = " ".join(sentences(r)) or "Full requirements and how to apply are on the listing page."
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def card_html(r):
    kind_cls = "sch" if r["kind"] == "Scholarship" else ""
    org = esc(r["company"]) or ("Scholarship provider" if r["kind"] == "Scholarship" else "Employer")
    sal = salary_text(r)
    new = ""
    try:
        if r["source"] == "form" and (datetime.utcnow() - datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")).days < 7:
            new = '<span class="tag new">New</span>'
    except Exception:
        pass
    tags = f'{new}{deadline_tag(r)}<span class="tag">{ic("tag", 13)} {esc(r["category"])}</span>'
    if r["kind"] == "Job" and r["work_mode"] and r["work_mode"] != "n/a":
        tags += f'<span class="tag">{ic("laptop", 13)} {esc(r["work_mode"])}</span>'
    if r["applicants"]:
        tags += f'<span class="tag">{ic("users", 13)} {int(r["applicants"])} applicant(s)</span>'
    salhtml = f'<div class="jc-sal">{ic("banknote", 15)} {esc(sal)}</div>' if sal else ""
    return (f'<div class="jc {kind_cls}"><div class="jc-top">{avatar(r)}<div class="jc-h">'
            f'<div class="jc-t">{esc(r["title"])}</div>'
            f'<div class="jc-c"><span>{org}</span><span>{ic("map-pin", 13)}{esc(r["location"] or "Uganda")}</span></div></div>'
            f'<span class="pill p-{esc(r["job_type"])}">{esc(r["job_type"])}</span></div>'
            f'<div class="jc-d">{esc(excerpt(r))}</div>{salhtml}<div class="tags">{tags}</div></div>')


@st.dialog("Opportunity details", width="large")
def detail_dialog(lid):
    r = db.get_listing(lid)
    if not r:
        st.error("Listing not found.")
        return
    row = pd.Series(r)
    row["applicants"] = 0
    org = esc(r["company"]) or ("Scholarship provider" if r["kind"] == "Scholarship" else "Employer")
    sal = salary_text(row)
    facts = [("map-pin", "Location", r["location"] or "Uganda"), ("briefcase", "Type", r["job_type"])]
    if r["kind"] == "Job":
        facts.append(("laptop", "Work mode", r["work_mode"]))
    facts.append(("calendar", "Deadline", fmt_date(r["deadline"]) or "Not stated"))
    if sal:
        facts.append(("banknote", "Salary", sal))
    st.markdown(f'<div class="jc-top">{avatar(row)}<div class="jc-h"><div class="jc-t" style="font-size:1.35rem">{esc(r["title"])}</div>'
                f'<div class="jc-c"><span>{org}</span><span>{deadline_tag(row)}</span></div></div></div>'
                f'<div class="facts">' + "".join(
                    f'<div class="fact"><div class="k">{ic(i, 14)} {k}</div><div class="v">{esc(v)}</div></div>' for i, k, v in facts)
                + "</div>", unsafe_allow_html=True)
    items = sentences(row)
    st.markdown(f'<h5 class="sub">{ic("file-text", 18, PURPLE)} About this opportunity</h5>', unsafe_allow_html=True)
    if items:
        st.markdown('<ul class="desc-list">' + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>", unsafe_allow_html=True)
    else:
        st.write("Full requirements and how to apply are on the listing page.")
    if is_closed(row):
        st.warning("This listing is closed or past its deadline. Check the official page in case it was extended.")
    if r["url"]:
        st.link_button("Open official listing / apply", r["url"], type="primary")
    if r["apply_email"]:
        st.markdown(f"Or email your CV to **{r['apply_email']}**")
    st.markdown(wa_buttons(r), unsafe_allow_html=True)
    if r["source"] == "form" and r["status"] == "active":
        st.markdown("#### Apply on Nuru")
        u = ss.user or {}
        with st.form(f"apply_{lid}", clear_on_submit=True):
            name = st.text_input("Full name", value=u.get("name", ""))
            email = st.text_input("Email", value=u.get("email", ""))
            phone = st.text_input("Phone")
            msg = st.text_area("Cover note")
            if st.form_submit_button("Submit application", type="primary"):
                if not (name.strip() and "@" in email):
                    st.error("Name and a valid email are required.")
                else:
                    db.add_application(lid, name, email, phone, msg)
                    st.success("Application sent. The employer will see it on their dashboard.")


def listing_grid(df, ctx, ncols=2):
    for i in range(0, len(df), ncols):
        cols = st.columns(ncols, gap="medium")
        for col, (_, r) in zip(cols, df.iloc[i:i + ncols].iterrows()):
            with col, st.container(key=f"card_{ctx}_{r['id']}"):
                st.markdown(card_html(r), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("View details", key=f"v_{ctx}_{r['id']}", use_container_width=True):
                    detail_dialog(int(r["id"]))
                if b2.button("Apply now", key=f"a_{ctx}_{r['id']}", use_container_width=True, type="primary"):
                    detail_dialog(int(r["id"]))


SLIDES = [
    ("clipboard", "Apply with confidence", "Review requirements, deadlines and how to apply before you submit."),
    ("tablet", "Careers in every sector", "Finance, health, ICT, engineering, development and more."),
    ("jobs", "Employers, hire faster", "Post a vacancy in minutes and manage applicants from one dashboard."),
    ("office", "Never miss a deadline", "Track closing dates across jobs, internships and scholarships."),
]


@st.cache_data(show_spinner=False)
def carousel_html():
    def b64(n):
        return base64.b64encode((STATIC / f"{n}_sm.jpg").read_bytes()).decode()
    slides = "".join(
        f'<figure class="sl{" on" if i == 0 else ""}" style="background-image:url(data:image/jpeg;base64,{b64(n)})" '
        f'role="group" aria-roledescription="slide" aria-label="{i+1} of {len(SLIDES)}">'
        f'<figcaption><h3>{t}</h3><p>{d}</p></figcaption></figure>' for i, (n, t, d) in enumerate(SLIDES))
    dots = "".join(f'<button class="dot{" on" if i == 0 else ""}" aria-label="Go to slide {i+1}"></button>'
                   for i in range(len(SLIDES)))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');
*{{box-sizing:border-box}} body{{margin:0;font-family:'Poppins',sans-serif}}
.car{{position:relative;height:400px;border-radius:18px;overflow:hidden;background:#2A0058;outline-offset:3px}}
.sl{{position:absolute;inset:0;margin:0;background-size:cover;background-position:center;opacity:0;transition:opacity .8s ease;display:flex;align-items:flex-end}}
.sl.on{{opacity:1}}
.sl::before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(38,0,80,0) 35%,rgba(38,0,80,.9) 100%)}}
figcaption{{position:relative;color:#fff;padding:0 2.2rem 3.2rem;max-width:620px}}
figcaption h3{{margin:0 0 .3rem;font-size:1.6rem;font-weight:600}} figcaption p{{margin:0;opacity:.9;font-size:.95rem}}
.nav{{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;border-radius:50%;border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.16);backdrop-filter:blur(6px);color:#fff;display:grid;place-items:center;cursor:pointer;transition:background .2s}}
.nav:hover,.nav:focus-visible{{background:rgba(255,255,255,.34)}} .prev{{left:14px}} .next{{right:14px}}
.dots{{position:absolute;left:2.2rem;bottom:1.3rem;display:flex;gap:8px}}
.dot{{width:22px;height:4px;border:0;border-radius:4px;background:rgba(255,255,255,.4);cursor:pointer;padding:0;transition:all .3s}}
.dot.on{{width:38px;background:#fff}}
@media (prefers-reduced-motion:reduce){{.sl{{transition:none}}}}
@media (max-width:560px){{.car{{height:340px}}figcaption{{padding:0 1.2rem 3rem}}.dots{{left:1.2rem}}}}
</style></head><body>
<div class="car" tabindex="0" role="region" aria-roledescription="carousel" aria-label="Why Nuru">
{slides}
<button class="nav prev" aria-label="Previous slide">{ic("chevron-left", 22, "#fff")}</button>
<button class="nav next" aria-label="Next slide">{ic("chevron-right", 22, "#fff")}</button>
<div class="dots">{dots}</div></div>
<script>
const car=document.querySelector('.car'),sl=[...car.querySelectorAll('.sl')],dt=[...car.querySelectorAll('.dot')];
let i=0,t=null;const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function show(n){{i=(n+sl.length)%sl.length;sl.forEach((e,k)=>e.classList.toggle('on',k===i));
 dt.forEach((e,k)=>{{e.classList.toggle('on',k===i);k===i?e.setAttribute('aria-current','true'):e.removeAttribute('aria-current')}})}}
function play(){{if(!reduce&&!t)t=setInterval(()=>show(i+1),5500)}} function stop(){{clearInterval(t);t=null}}
car.querySelector('.prev').onclick=()=>show(i-1);car.querySelector('.next').onclick=()=>show(i+1);
dt.forEach((e,k)=>e.onclick=()=>show(k));
car.addEventListener('mouseenter',stop);car.addEventListener('mouseleave',play);
car.addEventListener('focusin',stop);car.addEventListener('focusout',play);
car.addEventListener('keydown',e=>{{if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1)}});
let x0=null;car.addEventListener('touchstart',e=>x0=e.touches[0].clientX,{{passive:true}});
car.addEventListener('touchend',e=>{{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>40)show(i+(d<0?1:-1));x0=null}});
play();
</script></body></html>"""


def render_carousel():
    page = carousel_html()
    if hasattr(st, "iframe"):          # Streamlit >= 1.5x
        st.iframe(page, height=410)
    else:                              # older Streamlit
        components.html(page, height=410)


CAT_ICONS = [("financ", "landmark"), ("bank", "landmark"), ("medic", "stethoscope"), ("health", "stethoscope"),
             ("educat", "school"), ("school", "school"), ("ngo", "heart-handshake"), ("develop", "heart-handshake"),
             ("engineer", "hard-hat"), ("construct", "hard-hat"), ("ict", "cpu"), ("tech", "cpu"),
             ("agric", "sprout"), ("intern", "graduation-cap")]


def cat_icon(name):
    low = name.lower()
    return next((i for k, i in CAT_ICONS if k in low), "briefcase")


def pick_category(cat, kind):
    for k in ("q", "loc", "f_type", "f_mode", "f_hide"):
        ss.pop(k, None)
    ss.f_kind = kind
    ss.f_cat = [] if kind == "Scholarship" else [cat]
    ss.limit = 8
    ss.page = "Find Jobs"


def cat_tiles(jobs, df):
    st.markdown('<div class="sec-title">Browse by category</div><div class="sec-sub">Jump straight to the work you do.</div>',
                unsafe_allow_html=True)
    top = [(c, int(n), "Job") for c, n in jobs.category.value_counts().head(7).items()]
    top.append(("Scholarships", int((df.kind == "Scholarship").sum()), "Scholarship"))
    css = "".join(icons.mask_rule(f".st-key-cat_{i} button", "award" if k == "Scholarship" else cat_icon(c))
                  for i, (c, n, k) in enumerate(top))
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    for r in range(0, len(top), 4):
        for col, (i, (c, n, k)) in zip(st.columns(4), list(enumerate(top))[r:r + 4]):
            col.button(f"{c}  ·  {n}", key=f"cat_{i}", on_click=pick_category, args=(c, k), use_container_width=True)


def search_to_jobs():
    ss.page = "Find Jobs"
    ss.limit = 8


# ------------------------------------------------------------------ pages
def page_home():
    df = db.listings_df()
    jobs = df[df.kind == "Job"]
    n = len(HERO)
    slides = "".join(f'<div class="slide s{i}"></div>' for i in range(n))
    dots = "".join(f'<i class="d{i}"></i>' for i in range(n))
    st.markdown(f"""<div class="hero2">{slides}<div class="hero-in">
    <span class="eyebrow">{ic("sparkles", 14)} Jobs · Internships · Scholarships</span>
    <h1>Find an opportunity that fits<br>your interests and skills</h1>
    <p>Jobs, internships and scholarships in Uganda and beyond, all in one place.</p></div>
    <div class="dots">{dots}</div></div>""", unsafe_allow_html=True)
    with st.container(key="heroSearch"):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.text_input("Job title, keyword...", key="q", label_visibility="collapsed", placeholder="Job title, keyword...")
        c2.text_input("Location", key="loc", label_visibility="collapsed", placeholder="Location")
        c3.button("Find Job", key="find_btn", type="primary", use_container_width=True, on_click=search_to_jobs)
    st.caption("Suggestion: Accountant, Nurse, Engineer, Scholarship, Internship")

    st.markdown('<div class="sec-title">Featured Jobs</div><div class="sec-sub">Choose from top employers and apply.</div>',
                unsafe_allow_html=True)
    live = jobs[~jobs.apply(is_closed, axis=1)] if len(jobs) else jobs
    feat = (live if len(live) >= 3 else jobs).head(3)
    if len(feat):
        listing_grid(feat, "home", ncols=3)
    st.button("View all", key="viewall_btn", on_click=search_to_jobs)

    cat_tiles(jobs, df)
    st.markdown('<div class="sec-title">Built for every step of your career</div>'
                '<div class="sec-sub">From first application to final offer.</div>', unsafe_allow_html=True)
    render_carousel()

    top = jobs[jobs.company != ""].company.value_counts().head(10).index.tolist()
    if top:
        st.markdown('<div class="sec-sub" style="margin-top:2rem">Top organisations hiring now</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center">' + "".join(f'<span class="chip">{esc(t)}</span>' for t in top) + "</div>",
                    unsafe_allow_html=True)
    st.write("")
    sch = df[df.kind == "Scholarship"]
    n_open = lambda x: int((~x.apply(is_closed, axis=1)).sum()) if len(x) else 0
    stats = [("briefcase", len(jobs), f"Jobs & internships · {n_open(jobs)} open"),
             ("graduation-cap", len(sch), f"Scholarships · {n_open(sch)} open"),
             ("building-2", int(df.company.replace("", pd.NA).nunique()), "Organisations")]
    for col, (icn, val, lab) in zip(st.columns(3), stats):
        col.markdown(f'<div class="stat"><div class="ico">{ic(icn, 22, PURPLE)}</div><div><b>{val}</b>'
                     f'<span class="l">{lab}</span></div></div>', unsafe_allow_html=True)
    footer()


def page_find():
    df = db.listings_df()
    banner("Job Search", "Search for your desired job matching your skills", "jobs", tall=True)
    with st.container(key="heroSearch"):
        c1, c2, c3 = st.columns([3, 2, 1])
        q = c1.text_input("Job title / keyword", key="q", placeholder="Job title, keyword...", label_visibility="collapsed")
        loc = c2.text_input("Location", key="loc", placeholder="Location", label_visibility="collapsed")
        c3.button("Search", key="search_btn", type="primary", use_container_width=True)

    left, right = st.columns([1, 2.7], gap="large")
    with left, st.container(key="filterpanel"):
        h1, h2 = st.columns([1.3, 1])
        h1.markdown(f'<div class="fp-h">{ic("sliders-horizontal", 18)} Filters</div>', unsafe_allow_html=True)
        if h2.button("Clear all", key="clear_btn"):
            for k in ("q", "loc", "f_kind", "f_type", "f_mode", "f_cat", "f_hide"):
                ss.pop(k, None)
            st.rerun()
        kind = st.radio("Show", ["All", "Job", "Scholarship"], key="f_kind", horizontal=True,
                        format_func=lambda x: {"All": "All", "Job": "Jobs", "Scholarship": "Scholarships"}[x])
        base = df if kind == "All" else df[df.kind == kind]
        jt = st.multiselect("Job type", sorted(base.job_type.unique()), key="f_type")
        wm = st.multiselect("Work mode", [m for m in importer.WORK_MODES if m in set(base.work_mode)], key="f_mode")
        cats = base.category.value_counts()
        cat = st.multiselect("Category", list(cats.index), key="f_cat", format_func=lambda c: f"{c} ({cats[c]})")
        hide = st.checkbox("Hide closed / expired", key="f_hide")
        with st.expander("Salary range (UGX)"):
            smin = st.number_input("Min", min_value=0, step=100000, value=0)
            smax = st.number_input("Max", min_value=0, step=100000, value=0)

    f = base
    if q:
        blob = (f.title + " " + f.company + " " + f.description + " " + f.category).str.lower()
        for w in q.lower().split():
            f = f[blob.loc[f.index].str.contains(w, regex=False)]
    if loc:
        f = f[f.location.str.lower().str.contains(loc.lower(), regex=False)]
    if jt:
        f = f[f.job_type.isin(jt)]
    if wm:
        f = f[f.work_mode.isin(wm)]
    if cat:
        f = f[f.category.isin(cat)]
    if hide and len(f):
        f = f[~f.apply(is_closed, axis=1)]
    if smin:
        f = f[f.salary_max.fillna(f.salary_min).fillna(0) >= smin]
    if smax:
        f = f[f.salary_min.fillna(f.salary_max).fillna(0).le(smax) | f.salary_min.isna() & f.salary_max.isna()]

    with right:
        t1, t2 = st.columns([3, 1])
        chips = [x for x in [q, loc] if x] + list(jt) + list(wm) + list(cat) + (["Hiding closed"] if hide else [])
        t1.markdown(f'<div class="res-h"><b>{len(f)} opportunities</b>'
                    + "".join(f'<span class="chip-x">{esc(c)}</span>' for c in chips) + "</div>", unsafe_allow_html=True)
        sort = t2.selectbox("Sort", ["Latest", "Deadline soon", "Most applied"], label_visibility="collapsed")
        if sort == "Deadline soon":
            f = f.assign(_d=f.deadline.fillna("9999")).sort_values("_d")
        elif sort == "Most applied":
            f = f.sort_values("applicants", ascending=False)
        if f.empty:
            st.info("No listings match your filters.")
        else:
            listing_grid(f.head(ss.limit), "find")
            if len(f) > ss.limit:
                st.button("View more", on_click=lambda: ss.update(limit=ss.limit + 8))
    footer()


def page_post():
    banner("Post a job", "Find the best talent for your company", "tablet")
    if not ss.user:
        st.info("Please log in or register as an employer to post a job.")
        st.button("Login", key="login_post", on_click=go, args=("Login",), type="primary")
        return
    existing = db.listings_df()
    cats = sorted(set(existing.category) | set(CATEGORY_FALLBACK))
    with st.form("post_job", clear_on_submit=True):
        title = st.text_input("Job title*", placeholder="e.g. Senior Accountant")
        company = st.text_input("Company / organisation*", value=ss.user["name"])
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category*", cats)
        job_type = c2.selectbox("Job type", ["Full-time", "Part-time", "Internship", "Contract"])
        c3, c4 = st.columns(2)
        work_mode = c3.selectbox("Work mode", importer.WORK_MODES)
        location = c4.text_input("Location*", value="Kampala")
        s1, s2, s3 = st.columns(3)
        currency = s1.selectbox("Currency", ["UGX", "USD", "KES", "EUR"])
        smin = s2.number_input("Min salary", min_value=0, step=100000)
        smax = s3.number_input("Max salary", min_value=0, step=100000)
        d1, d2 = st.columns(2)
        deadline = d1.date_input("Application deadline", value=None, min_value=date.today())
        apply_email = d2.text_input("Application email or URL (optional)")
        desc = st.text_area("Job description*", height=180, placeholder="Responsibilities, requirements, how to apply...")
        ok = st.form_submit_button("Post Job", type="primary")
    if ok:
        if not (title.strip() and company.strip() and location.strip() and desc.strip()):
            st.error("Title, company, location and description are required.")
        else:
            is_url = apply_email.strip().lower().startswith("http")
            db.post_job(dict(kind="Job", title=title.strip(), company=company.strip(), category=category,
                             job_type=job_type, work_mode=work_mode, location=location.strip(),
                             salary_min=smin or None, salary_max=smax or None, currency=currency,
                             deadline=deadline.isoformat() if deadline else None, description=desc.strip(),
                             url=apply_email.strip() if is_url else "",
                             apply_email="" if is_url else apply_email.strip()), ss.user["email"])
            st.success("Job posted. It is now live on Find Jobs and listed on your dashboard.")
            st.button("Go to dashboard", key="goto_dash", on_click=go, args=("Dashboard",), type="primary")


def bulk_upload_ui(owner):
    st.markdown("#### Bulk upload from Excel / CSV")
    st.caption("Use the same layout as hub_repo.xlsx: **path, title, url, details**. "
               "Duplicates (same URL) are skipped automatically.")
    tpl = pd.DataFrame([{"path": "Jobs/Banks & Finance", "title": "Example Bank - Credit Officer",
                         "url": "https://example.com/job/1",
                         "details": "Kampala. Closes 30 Dec 2026. Degree in Finance, 2 yrs experience. Email CV to hr@example.com"}])
    buf = io.BytesIO()
    tpl.to_excel(buf, index=False)
    st.download_button("Download template", buf.getvalue(), "nuru_template.xlsx", key="dl_tpl")
    up = st.file_uploader("Upload .xlsx or .csv", type=["xlsx", "csv"])
    if up:
        try:
            items = importer.parse_dataframe(importer.read_file(up))
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return
        prev = pd.DataFrame(items)[["kind", "title", "company", "category", "location", "deadline"]]
        st.write(f"{len(items)} rows parsed. Preview:")
        st.dataframe(prev, use_container_width=True, hide_index=True)
        if st.button(f"Import {len(items)} listings", key="import_btn", type="primary"):
            added, skipped = db.bulk_add(items, source="excel", owner=owner)
            st.success(f"Added {added}. Skipped {skipped} duplicate(s).")
            st.rerun()


def page_dashboard():
    banner("Dashboard", "Manage your listings, applications and uploads", "office")
    if not ss.user:
        st.info("Log in to see your dashboard.")
        st.button("Login", key="login_dash", on_click=go, args=("Login",), type="primary")
        return
    admin = is_admin()
    owner = ss.user["email"]
    scope_all = admin and st.toggle("Admin view: show every listing", value=True)
    mine = db.listings_df(None if scope_all else owner)
    apps = db.applications_df(None if scope_all else owner)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total listings", len(mine))
    m2.metric("Active", int((~mine.apply(is_closed, axis=1)).sum()) if len(mine) else 0)
    m3.metric("Applications received", len(apps))

    t1, t2, t3 = st.tabs(["Posted jobs", "Applications", "Bulk upload & export"])
    with t1:
        if mine.empty:
            st.info("Nothing posted yet.")
            st.button("Post your first job", key="firstjob", on_click=go, args=("Post a Job",), type="primary")
        else:
            q = st.text_input("Filter this list", placeholder="Search title, company, category...")
            lst = mine
            if q:
                blob = (mine.title + " " + mine.company + " " + mine.category).str.lower()
                lst = mine[blob.str.contains(q.lower(), regex=False)]
            page_size = 15
            pages = max(1, -(-len(lst) // page_size))
            pg = st.number_input("Page", 1, pages, 1) if pages > 1 else 1
            for _, r in lst.iloc[(pg - 1) * page_size: pg * page_size].iterrows():
                with st.container(border=True):
                    a, b, c, d = st.columns([5, 1.4, 1.2, 1.2])
                    a.markdown(card_html(r), unsafe_allow_html=True)
                    a.caption(f"Posted {r['created_at'][:10]} · {r['source']}")
                    b.metric("Applicants", int(r["applicants"]))
                    if r["status"] == "active":
                        c.button("Close", key=f"close_{r['id']}", on_click=db.set_status, args=(int(r["id"]), "closed"),
                                 use_container_width=True)
                    else:
                        c.button("Reopen", key=f"reopen_{r['id']}", on_click=db.set_status, args=(int(r["id"]), "active"),
                                 use_container_width=True)
                    d.button("Delete", key=f"del_{r['id']}", on_click=db.delete_listing, args=(int(r["id"]),),
                             use_container_width=True)
    with t2:
        if apps.empty:
            st.info("No applications yet.")
        else:
            st.dataframe(apps, use_container_width=True, hide_index=True)
    with t3:
        bulk_upload_ui(owner)
        st.divider()
        st.markdown("#### Export (backup)")
        out = mine.drop(columns=["dedupe_key"], errors="ignore")
        buf = io.BytesIO()
        out.to_excel(buf, index=False)
        st.download_button("Download listings (.xlsx)", buf.getvalue(), "nuru_listings.xlsx", key="dl_export")
        hub = io.BytesIO()
        importer.to_hub_frame(mine).to_excel(hub, index=False)
        st.download_button("Export in hub_repo.xlsx format", hub.getvalue(), "hub_repo.xlsx", key="dl_hub",
                           help="Same columns as your hub_repo sheet (path, title, url, details), including jobs posted here.")


def auth_form(register):
    left, mid = st.columns([1.05, 1], gap="large")
    img = "tablet" if register else "clipboard"
    pts = (["Post jobs and manage applicants", "Bulk-upload vacancies from Excel", "Track everything on one dashboard"]
           if register else ["Pick up where you left off", "Track your postings and applications", "Secure sign-in"])
    ptic = ["briefcase-business", "file-spreadsheet", "layout-dashboard"] if register else ["clock", "list-checks", "shield-check"]
    with left:
        st.markdown(f'<div class="authpanel" style="background-image:url(/app/static/{img}.jpg)">'
                    f'<h3>{"Join Nuru today" if register else "Welcome back"}</h3>'
                    + "".join(f'<div class="pt">{ic(i, 18)} {esc(p)}</div>' for i, p in zip(ptic, pts))
                    + "</div>", unsafe_allow_html=True)
    with mid:
        st.markdown(f"## {'Create your account' if register else 'Login to your account'}")
        with st.form("auth"):
            if register:
                name = st.text_input("Full name*")
            email = st.text_input("Email ID*")
            if register:
                phone = st.text_input("Mobile number*", placeholder="+256 ...")
                role = st.radio("I am a", ["candidate", "employer"], horizontal=True,
                                format_func=lambda x: x.title())
            pw = st.text_input("Password*" + (" (min 6 characters)" if register else ""), type="password")
            ok = st.form_submit_button("Register now" if register else "Login", type="primary", use_container_width=True)
        if ok:
            if register:
                if not (name.strip() and "@" in email and phone.strip() and len(pw) >= 6):
                    st.error("Fill every field. Password needs at least 6 characters.")
                else:
                    role = "admin" if email.strip().lower() in admin_emails() else role
                    if db.create_user(email, name, phone, pw, role):
                        login_user(db.verify_user(email, pw))
                        ss.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("That email is already registered.")
            else:
                u = db.verify_user(email, pw)
                if u:
                    login_user(u)
                    ss.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Wrong email or password.")
        if register:
            st.button("Already have an account? Login", on_click=go, args=("Login",))
        else:
            st.button("Don't have an account? Register", on_click=go, args=("Register",))


def page_about():
    banner("About Nuru", "Light for your next step", "jobs")
    st.write("Nuru (Luganda/Swahili for *light*) helps Ugandans find jobs, internships and scholarships in one place, "
             "and lets employers post vacancies and manage applications.")
    st.markdown(f"{ic('map-pin', 15)} &nbsp;**Contact:** Kampala, Uganda", unsafe_allow_html=True)
    st.markdown(wa_buttons(), unsafe_allow_html=True)
    footer()


navbar()
{"Home": page_home, "Find Jobs": page_find, "Post a Job": page_post, "Dashboard": page_dashboard,
 "About": page_about, "Login": lambda: auth_form(False), "Register": lambda: auth_form(True)}[ss.page]()
wa_fab()
