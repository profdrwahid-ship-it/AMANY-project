# pages/5_Financial_Data.py
# Financial dashboard with:
# - Page-wide header (AMANY + full name + current datetime)
# - Robust header resolution (row2 -> row1 -> row3 -> Unnamed, unique)
# - Month index from column A (m/YYYY)
# - KPIs computed up to previous month end (exclude current/future months)
# - Safe PNG export (on-click, guarded)
# - Optional OLS trendline (only if statsmodels available)
# - Excel export with engine auto-detect; CSV ZIP fallback

import time
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import traceback

# Optional PNG export
try:
    import kaleido  # noqa: F401
    KALEIDO = True
except Exception:
    KALEIDO = False

# Optional OLS dependency
try:
    import statsmodels.api as sm  # noqa: F401
    HAS_SM = True
except Exception:
    HAS_SM = False

# Optional Cairo timezone
try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
except Exception:
    CAIRO_TZ = None

# ---------------- Page config ----------------
st.set_page_config(page_title="AMANY - لوحة البيانات المالية", layout="wide", page_icon="💡")

st.markdown("""
<style>
.stApp { background:#2e5ae8; }
h1,h2,h3 { color:#39ff14; }
.amany-header { text-align:center; margin: 8px 0 16px 0; }
.amany-title-short { font-size:36px; font-weight:900; letter-spacing:2px; color:#39ff14; }
.amany-title-full { font-size:18px; color:#f0f8ff; margin-top:4px; }
.amany-datetime { font-size:14px; color:#ddd; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers ----------------
def now_cairo():
    return datetime.now(CAIRO_TZ) if CAIRO_TZ else datetime.now()

def month_start(dt: datetime) -> pd.Timestamp:
    return pd.Timestamp(year=dt.year, month=dt.month, day=1)

def prev_month_start(dt: datetime) -> pd.Timestamp:
    m = dt.month - 1 or 12
    y = dt.year if dt.month > 1 else dt.year - 1
    return pd.Timestamp(year=y, month=m, day=1)

def prev_month_end(dt: datetime) -> pd.Timestamp:
    pms = prev_month_start(dt)
    return pms + pd.offsets.MonthEnd(0)

def with_backoff(func, *args, **kwargs):
    for d in [0.5, 1, 2, 4, 8]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                time.sleep(d); continue
            raise
    raise RuntimeError("Backoff retries exceeded.")

# ---------------- Spreadsheet ID ----------------
# تحسين التعامل مع Spreadsheet ID
SPREADSHEET_ID = ""
try:
    # محاولة الحصول على ID من الأسرار أولاً
    if "sheets" in st.secrets and "spreadsheet_id" in st.secrets["sheets"]:
        SPREADSHEET_ID = st.secrets["sheets"]["spreadsheet_id"]
    elif "spreadsheet_id" in st.secrets:
        SPREADSHEET_ID = st.secrets["spreadsheet_id"]
except Exception:
    pass

# إذا لم يتم العثور على ID في الأسرار، نطلب من المستخدم
if not SPREADSHEET_ID:
    SPREADSHEET_ID = st.text_input("أدخل Spreadsheet ID:", value="1lELs2hhkOnFVix8HSE4iHpw8r20RXnEMXK9uzHSbT6Y")

# ---------------- Page-wide header ----------------
_now = now_cairo().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"""
<div class="amany-header">
  <div class="amany-title-short">AMANY</div>
  <div class="amany-title-full">AMANY – Advanced Financial Dashboard</div>
  <div class="amany-datetime">{_now}</div>
</div>
""", unsafe_allow_html=True)

# ---------------- Settings ----------------
CONFIG_SHEET_NAME = "Config"
TOTALS_CONFIG_COLUMN = "Totals_KPIs"
ALERT_THRESHOLD = 20.0

# ---------------- Resources ----------------
@st.cache_resource(ttl=7200)
def get_spreadsheet(spreadsheet_id: str):
    try:
        # التحقق من صحة spreadsheet_id
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            st.error("معرف الملف غير صالح")
            return None
            
        # التحقق من وجود الأسرار
        if "gcp_service_account" not in st.secrets:
            st.error("بيانات الاعتماد غير موجودة في الأسرار")
            return None
            
        creds_dict = st.secrets["gcp_service_account"]
        
        # التأكد من أن creds_dict هو قاموس
        if not isinstance(creds_dict, dict):
            st.error("بيانات الاعتماد غير صالحة")
            return None
            
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        client = gspread.authorize(creds)
        return with_backoff(client.open_by_key, spreadsheet_id)
    except Exception as e:
        st.error(f"خطأ في المصادقة: {e}")
        st.error(traceback.format_exc())
        return None

@st.cache_data(ttl=900)
def list_worksheets(spreadsheet_id: str):
    if not spreadsheet_id:
        return []
        
    sh = get_spreadsheet(spreadsheet_id)
    if sh is None:
        return []
        
    try:
        return [ws.title for ws in with_backoff(sh.worksheets)]
    except Exception as e:
        st.error(f"خطأ في جلب قائمة الأوراق: {e}")
        return []

@st.cache_data(ttl=900)
def get_all_values(spreadsheet_id: str, worksheet_name: str):
    if not spreadsheet_id or not worksheet_name:
        return []
        
    sh = get_spreadsheet(spreadsheet_id)
    if sh is None:
        return []
        
    try:
        ws = with_backoff(sh.worksheet, worksheet_name.strip())
        return with_backoff(ws.get_all_values)
    except Exception as e:
        st.error(f"خطأ في جلب البيانات من {worksheet_name}: {e}")
        return []

@st.cache_data(ttl=900)
def read_totals_list(spreadsheet_id: str):
    try:
        vals = get_all_values(spreadsheet_id, CONFIG_SHEET_NAME)
        if len(vals) < 2:
            return []
        header = [str(h).strip() for h in vals[0]]
        cfg = pd.DataFrame(vals[1:], columns=header)
        if TOTALS_CONFIG_COLUMN not in cfg.columns:
            return []
        return cfg[TOTALS_CONFIG_COLUMN].dropna().astype(str).str.strip().tolist()
    except Exception:
        return []

# ---------------- Header resolving ----------------
def make_headers_unique(headers: list) -> list:
    seen = {}
    out = []
    for h in headers:
        h = str(h)
        if h not in seen:
            seen[h] = 0
            out.append(h)
        else:
            seen[h] += 1
            out.append(f"{h}.{seen[h]}")
    return out

def resolve_headers_merged(row1: list, row2: list, row3: list) -> list:
    L = max(len(row1), len(row2), len(row3))
    tmp = []
    for j in range(L):
        a = str(row2[j]).strip() if j < len(row2) else ""
        b = str(row1[j]).strip() if j < len(row1) else ""
        c = str(row3[j]).strip() if j < len(row3) else ""
        if a:
            tmp.append(a)
        elif b:
            tmp.append(b)
        elif c:
            tmp.append(c)
        else:
            tmp.append("Unnamed")
    return make_headers_unique(tmp)

# ---------------- Parsing ----------------
def _clean_numeric(s: pd.Series) -> pd.Series:
    s = (s.astype(str)
         .str.replace(',', '', regex=False)
         .str.replace('%', '', regex=False)
         .replace(['', '-', '—'], '0'))
    return pd.to_numeric(s, errors='coerce').fillna(0)

def parse_sheet(all_values):
    if not all_values or len(all_values) < 3:
        return pd.DataFrame(), [], []

    row1 = all_values[0]
    row2 = all_values[1]
    row3 = all_values[2]
    headers_resolved = resolve_headers_merged(row1, row2, row3)
    rows = all_values[2:]

    raw_df = pd.DataFrame(rows, columns=headers_resolved)
    if raw_df.shape[1] == 0:
        return pd.DataFrame(), row2, rows

    raw_df = raw_df.loc[:, ~(raw_df.columns.astype(str).str.strip() == "")]

    first_col_name = str(raw_df.columns[0])
    month_series = raw_df.iloc[:, 0].astype(str).str.strip()

    dates = pd.to_datetime(month_series, errors="coerce")
    mask = dates.isna()
    if mask.any():
        dates.loc[mask] = pd.to_datetime(month_series[mask], format="%m/%Y", errors="coerce")
    dates = dates.dt.to_period("M").dt.to_timestamp()

    proc = raw_df.copy()
    proc["__MonthDate__"] = dates
    proc["Month"] = month_series
    proc = proc.dropna(subset=["__MonthDate__"]).set_index("__MonthDate__").sort_index()

    for c in proc.columns:
        c_str = str(c)
        if c_str == "Month" or c_str == first_col_name:
            continue
        proc[c] = (proc[c].astype(str)
                     .str.replace(",", "", regex=False)
                     .str.replace("%", "", regex=False)
                     .replace(["", "-", "—"], "0"))
        proc[c] = pd.to_numeric(proc[c], errors="coerce").fillna(0)

    return proc, row2, rows

@st.cache_data(ttl=900)
def get_df(spreadsheet_id: str, worksheet_name: str):
    vals = get_all_values(spreadsheet_id, worksheet_name)
    return parse_sheet(vals)

# ---------------- AI Summary ----------------
def ai_summary(df: pd.DataFrame):
    try:
        base = df.drop(columns=["Month"], errors="ignore")
        if len(base) < 2:
            return "البيانات غير كافية."
        last, prev = base.iloc[-1], base.iloc[-2]
        rev = [c for c in base.columns if c.lower().startswith("total revenues")]
        exp = [c for c in base.columns if c.lower().startswith("total expenses")]
        lines = []
        if rev and prev[rev[0]] != 0:
            change_rev = (last[rev].iloc[0] - prev[rev].iloc[0]) / prev[rev].iloc[0] * 100
            lines.append(f"- الإيرادات: {change_rev:+.1f}%.")
        if exp and prev[exp].iloc[0] != 0:
            change_exp = (last[exp].iloc[0] - prev[exp].iloc[0]) / prev[exp].iloc[0] * 100
            lines.append(f"- المصروفات: {change_exp:+.1f}%.")
        best = base.pct_change().mean(numeric_only=True).idxmax()
        lines.append(f"- أبرز نمو: {best}.")
        return "\n".join(lines)
    except Exception:
        return "تعذر إنشاء الملخص."

# ---------------- UI ----------------
st.markdown("## 💡 لوحة البيانات المالية")

# اختبار الاتصال أولاً
if not SPREADSHEET_ID:
    st.warning("يرجى إدخال Spreadsheet ID للمتابعة")
    st.stop()

try:
    ws_list = list_worksheets(SPREADSHEET_ID)
    if not ws_list:
        st.warning("لا توجد أوراق في الملف أو لا يمكن الوصول إلى الملف")
        st.stop()
except Exception as e:
    st.error(f"تعذر فتح الملف: {e}")
    st.error("تفاصيل الخطأ:")
    st.code(traceback.format_exc())
    st.stop()

sheet_name = st.selectbox("اختر الورقة:", ws_list)

try:
    df_full, header_raw, rows_raw = get_df(SPREADSHEET_ID, sheet_name)
    if df_full.empty:
        st.warning(f"لا بيانات صالحة في الورقة: {sheet_name}")
        st.stop()
except Exception as e:
    st.error(f"خطأ في تحميل البيانات: {e}")
    st.stop()

# باقي الكود يبقى كما هو...
min_d, max_d = df_full.index.min().date(), df_full.index.max().date()
start_d, end_d = st.date_input("النطاق الزمني:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
df_f = df_full.loc[pd.to_datetime(start_d):pd.to_datetime(end_d)].copy()
if df_f.empty:
    st.warning("لا توجد بيانات ضمن النطاق الزمني المحدد.")
    st.stop()

now_dt = now_cairo()
pm_end = prev_month_end(now_dt)

tab_raw, tab_proc = st.tabs(["📄 Raw as-is", "📊 Processed + KPIs"])

with tab_raw:
    all_vals = get_all_values(SPREADSHEET_ID, sheet_name)
    if all_vals:
        row1 = all_vals[0] if len(all_vals) > 0 else []
        row2 = all_vals[1] if len(all_vals) > 1 else []
        row3 = all_vals[2] if len(all_vals) > 2 else []
        safe_cols = resolve_headers_merged(row1, row2, row3)
        st.dataframe(pd.DataFrame(rows_raw, columns=safe_cols))
    else:
        st.warning("لا توجد بيانات خام لعرضها")

with tab_proc:
    st.caption(f"الحسابات أدناه حتى نهاية: {pm_end.strftime('%b %Y')}")
    kpi_base = df_f.loc[:pm_end] if not df_f.loc[:pm_end].empty else df_f.copy()
    st.info(ai_summary(kpi_base))

    display_df = df_f.loc[:pm_end].reset_index().rename(columns={"__MonthDate__": "Date"})
    if display_df.empty:
        display_df = df_f.reset_index().rename(columns={"__MonthDate__": "Date"})
    display_df = display_df[["Month"] + [c for c in display_df.columns if c != "Month"]]
    st.dataframe(display_df)

    totals_cfg = read_totals_list(SPREADSHEET_ID)
    all_cols = [c for c in df_f.columns if c != "Month"]
    totals = [c for c in all_cols if c in totals_cfg]
    avgs = [c for c in all_cols if c not in totals_cfg]

    df_kpi = kpi_base

    def render_kpi_cards(cols, title, is_avg):
        if not cols:
            return
        st.subheader(title)
        cols_area = st.columns(4)
        for i, c in enumerate(cols):
            s = df_kpi[c]
            if s.empty:
                continue
            main_val = s.mean() if is_avg else s.sum()
            max_val, min_val = s.max(), s.min()
            try:
                max_dt = s.idxmax().strftime('%b %Y')
                min_dt = s.idxmin().strftime('%b %Y')
            except Exception:
                max_dt, min_dt = "-", "-"
            avg_val = s.mean()
            last_val = s.iloc[-1]
            growth = ((last_val - avg_val) / avg_val * 100) if avg_val else 0.0
            up = last_val > avg_val
            arrow = "↑" if up else "↓"
            color = "#00ff00" if up else "#ff4136"
            highlight = ("border:2px solid #00ff00" if abs(growth) >= ALERT_THRESHOLD and up
                         else "border:2px solid #ff4136" if abs(growth) >= ALERT_THRESHOLD else "")
            with cols_area[i % 4]:
                st.markdown(f"""
                <div style="background:#111;padding:10px;border-radius:10px;{highlight}">
                  <div style="color:#39ff14;font-weight:bold;text-align:center">{c}</div>
                  <div style="color:#39ff14;font-size:22px;font-weight:bold;text-align:center">{main_val:,.2f}</div>
                  <div style="color:#ddd;text-align:center">أعلى: {max_dt} ({max_val:,.2f})</div>
                  <div style="color:#ddd;text-align:center">أقل: {min_dt} ({min_val:,.2f})</div>
                </div>
                <div style="background:#1a1a1a;padding:8px;border-radius:8px;margin-top:6px;text-align:center">
                  <span style="color:{color};font-weight:bold">{last_val:,.2f}</span>
                  <span style="color:{color};font-weight:bold">{arrow}</span>
                  <span style="color:#ccc">{avg_val:,.2f}</span>
                  <div style="color:{color}">({growth:+.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)

    render_kpi_cards(totals, "إجماليات (Sum)", is_avg=False)
    render_kpi_cards(avgs, "متوسطات (Average)", is_avg=True)

# ... باقي الكود يبقى كما هو (المقارنات، التصدير، إلخ)
