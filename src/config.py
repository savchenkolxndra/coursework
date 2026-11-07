"""
config.py — конфігурація, кольори, CSS
"""

# ── Підключення до БД ──────────────────────────────────────────────────────────
LOCAL_DB_PATH = "data/local_grades.db"
LOCAL_DB      = f"sqlite:///{LOCAL_DB_PATH}"
REMOTE_DB = "postgresql+psycopg2://postgres.ammdxorwrqohvlnudhja:OE9C8Q21iL2rAXx1@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

# ── Шрифти для PDF ─────────────────────────────────────────────────────────────
FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_BOLD_PATHS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\Arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# ── Кольорова палітра ──────────────────────────────────────────────────────────
DARK_GREEN  = "#1B5E20"
MID_GREEN   = "#2E7D32"
LIGHT_GREEN = "#388E3C"
BG_GREEN    = "#E8F5E9"
PALE_GREEN  = "#F1F8E9"
GOLD        = "#B8860B"
GOLD_LIGHT  = "#FFF8DC"
GOLD_MID    = "#F5DEB3"
AMBER       = "#F9A825"
RED         = "#E24B4A"
GREEN_CHART = "#2E7D32"

CHART_COLORS = [MID_GREEN, GOLD, LIGHT_GREEN, AMBER, "#5DCAA5", "#D4537E", "#534AB7", "#EF9F27"]
SCALE_GRADE  = [[0, RED], [0.5, AMBER], [1.0, GREEN_CHART]]

CUSTOM_CSS = f"""
<style>
[data-testid="stSidebar"] {{
    background: linear-gradient(170deg, {DARK_GREEN} 0%, {MID_GREEN} 45%, {LIGHT_GREEN} 100%);
}}
[data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.92) !important; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.2) !important; }}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
    display: flex; flex-direction: column; gap: 4px;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
    padding: 8px 12px !important; border-radius: 8px !important;
    transition: background 0.15s !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
    background: rgba(255,255,255,0.15) !important;
}}
h1 {{ color: {DARK_GREEN} !important; }}
h2 {{ color: {GOLD} !important; }}
h3 {{ color: {MID_GREEN} !important; }}
.stButton > button {{
    border-radius: 8px !important;
    background: linear-gradient(135deg, {DARK_GREEN}, {GOLD}) !important;
    color: white !important; border: none !important; font-weight: 500 !important;
}}
.stTabs [aria-selected="true"] {{
    color: {GOLD} !important;
    border-bottom: 2px solid {GOLD} !important;
}}
</style>
"""