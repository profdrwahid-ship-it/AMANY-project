# pages/5_Financial_Data.py
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
import json

# ============ استيراد آمن لجميع المكتبات ============
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
    PYTZ_AVAILABLE = True
except ImportError:
    CAIRO_TZ = None
    PYTZ_AVAILABLE = False

# ============ التنسيق الفوسفوري المتكامل ============
st.set_page_config(
    page_title="AMANY - لوحة البيانات المالية", 
    layout="wide", 
    page_icon="💰"
)

st.markdown("""
<style>
:root {
    --neon-green: #39ff14;
    --neon-blue: #00ffff;
    --neon-pink: #ff00ff;
    --neon-orange: #ff8c00;
    --neon-yellow: #ffff00;
    --neon-purple: #da70d6;
    --bg-dark: #0b1020;
    --card: #152240;
    --border: #5a7ff0;
}

.stApp { 
    background: linear-gradient(135deg, #0b1020, #1a1f38) !important;
}

.main-header {
    text-align: center;
    padding: 25px;
    background: linear-gradient(135deg, #152240, #2c4ba0);
    border-radius: 15px;
    margin-bottom: 20px;
    border: 2px solid var(--neon-green);
    box-shadow: 0 0 25px rgba(57, 255, 20, 0.4);
}

.main-title {
    font-size: 52px;
    font-weight: 900;
    color: var(--neon-green);
    text-shadow: 0 0 15px rgba(57, 255, 20, 0.8);
    letter-spacing: 3px;
    margin: 0;
}

.sub-title {
    color: var(--neon-blue);
    font-size: 20px;
    margin: 8px 0;
    text-shadow: 0 0 8px rgba(0, 255, 255, 0.6);
}

.time-display {
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    color: var(--neon-green);
    background: rgba(21, 34, 64, 0.9);
    padding: 15px;
    border-radius: 10px;
    margin: 20px 0;
    border: 1px solid var(--neon-green);
    box-shadow: 0 0 20px rgba(57, 255, 20, 0.3);
}

/* الكروت الفوسفورية */
.kpi-card {
    border-radius: 15px;
    background: var(--card);
    padding: 20px 15px;
    margin-bottom: 15px;
    box-shadow: 0 0 20px rgba(90, 127, 240, 0.3);
    text-align: center;
    min-height: 130px;
    border: 2px solid var(--neon-green);
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.3s ease;
    background: linear-gradient(135deg, #152240, #1e2f5a);
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 30px rgba(57, 255, 20, 0.6);
    border-color: var(--neon-blue);
}

.kpi-title {
    color: var(--neon-blue) !important;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.4);
}

.kpi-value {
    color: var(--neon-green) !important;
    font-size: 32px;
    font-weight: 900;
    text-shadow: 0 0 10px rgba(57, 255, 20, 0.7);
}

/* العناوين الفوسفورية */
h1, h2, h3, h4, h5, h6 {
    color: var(--neon-green) !important;
    text-shadow: 0 0 8px rgba(57, 255, 20, 0.5) !important;
}

.subtitle {
    color: var(--neon-green) !important;
    font-weight: bold;
    text-align: center;
    margin: 20px 0;
    border-bottom: 3px solid var(--neon-blue);
    padding-bottom: 10px;
    text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);
    font-size: 28px;
}

/* الأزرار الفوسفورية */
.stButton button {
    background: linear-gradient(45deg, var(--neon-green), var(--neon-blue)) !important;
    color: #000 !important;
    font-weight: bold;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
    transition: all 0.3s ease;
}

.stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(57, 255, 20, 0.8);
}

/* الرسائل والإشعارات */
.stSuccess {
    background: linear-gradient(45deg, rgba(57, 255, 20, 0.2), rgba(0, 255, 255, 0.2)) !important;
    border: 1px solid var(--neon-green) !important;
    color: var(--neon-green) !important;
}

.stInfo {
    background: linear-gradient(45deg, rgba(0, 255, 255, 0.2), rgba(255, 0, 255, 0.2)) !important;
    border: 1px solid var(--neon-blue) !important;
    color: var(--neon-blue) !important;
}

.stWarning {
    background: linear-gradient(45deg, rgba(255, 140, 0, 0.2), rgba(255, 255, 0, 0.2)) !important;
    border: 1px solid var(--neon-orange) !important;
    color: var(--neon-orange) !important;
}

.stError {
    background: linear-gradient(45deg, rgba(255, 0, 0, 0.2), rgba(255, 0, 255, 0.2)) !important;
    border: 1px solid var(--neon-pink) !important;
    color: var(--neon-pink) !important;
}

/* تحسينات إضافية */
.stDataFrame {
    border: 1px solid var(--neon-blue) !important;
    border-radius: 10px !important;
}

.stSelectbox [data-baseweb="select"] {
    border: 1px solid var(--neon-orange) !important;
    border-radius: 8px !important;
}

.stRadio [role="radiogroup"] {
    border: 1px solid var(--neon-purple) !important;
    border-radius: 10px !important;
    padding: 10px !important;
    background: rgba(41, 57, 92, 0.8) !important;
}
</style>
""", unsafe_allow_html=True)

# ============ الدوال المساعدة ============
def get_google_credentials():
    """الحصول على بيانات الاعتماد من Secrets بشكل آمن"""
    try:
        if 'gcp_service_account' in st.secrets:
            if isinstance(st.secrets['gcp_service_account'], str):
                return json.loads(st.secrets['gcp_service_account'])
            else:
                return dict(st.secrets['gcp_service_account'])
        else:
            st.error("❌ لم يتم العثور على إعدادات Google Service Account في Secrets")
            return None
    except Exception as e:
        st.error(f"❌ خطأ في تحميل إعدادات Google: {e}")
        return None

def now_cairo():
    if PYTZ_AVAILABLE and CAIRO_TZ:
        return datetime.now(CAIRO_TZ)
    return datetime.now()

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
                time.sleep(d)
                continue
            raise
    raise RuntimeError("فشلت جميع محاولات إعادة الاتصال")

# ============ معرف ملف البيانات ============
PHC_SPREADSHEET_ID = "1ptbPIJ9Z0k92SFcXNqAeC61SXNpamCm-dXPb97cPT_4"

# ============ الهيدر الرئيسي ============
_now = now_cairo().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"""
<div class="main-header">
  <div class="main-title">💰 AMANY</div>
  <div class="sub-title">Advanced Financial Dashboard - لوحة البيانات المالية المتقدمة</div>
  <div class="sub-title">منصة التحليل المالي المتقدم - فرع جنوب سيناء</div>
  <div class="time-display">⏰ الوقت الحالي بتوقيت القاهرة: {_now}</div>
</div>
""", unsafe_allow_html=True)

# ============ الإعدادات ============
CONFIG_SHEET_NAME = "Config"
TOTALS_CONFIG_COLUMN = "Totals_KPIs"
ALERT_THRESHOLD = 20.0

# ============ الدوال الأساسية ============
@st.cache_resource(ttl=7200)
def get_spreadsheet(spreadsheet_id: str):
    """الاتصال بملف Google Sheets"""
    try:
        credentials_dict = get_google_credentials()
        if not credentials_dict:
            return None
            
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return with_backoff(client.open_by_key, spreadsheet_id)
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بجوجل شيتس: {e}")
        return None

@st.cache_data(ttl=900)
def list_worksheets(spreadsheet_id: str):
    try:
        sh = get_spreadsheet(spreadsheet_id)
        if not sh:
            return []
        return [ws.title for ws in with_backoff(sh.worksheets)]
    except Exception as e:
        st.error(f"❌ خطأ في قراءة قائمة الأوراق: {e}")
        return []

@st.cache_data(ttl=900)
def get_all_values(spreadsheet_id: str, worksheet_name: str):
    try:
        sh = get_spreadsheet(spreadsheet_id)
        if not sh:
            return []
        ws = with_backoff(sh.worksheet, worksheet_name.strip())
        return with_backoff(ws.get_all_values)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الورقة '{worksheet_name}': {e}")
        return []

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

def ai_summary(df: pd.DataFrame):
    try:
        base = df.drop(columns=["Month"], errors="ignore")
        if len(base) < 2:
            return "البيانات غير كافية."
        last, prev = base.iloc[-1], base.iloc[-2]
        rev = [c for c in base.columns if "revenue" in c.lower() or "إيراد" in c.lower()]
        exp = [c for c in base.columns if "expense" in c.lower() or "مصروف" in c.lower()]
        lines = []
        if rev and prev[rev[0]] != 0:
            change_rev = (last[rev].iloc[0] - prev[rev].iloc[0]) / prev[rev].iloc[0] * 100
            lines.append(f"- الإيرادات: {change_rev:+.1f}%.")
        if exp and prev[exp].iloc[0] != 0:
            change_exp = (last[exp].iloc[0] - prev[exp].iloc[0]) / prev[exp].iloc[0] * 100
            lines.append(f"- المصروفات: {change_exp:+.1f}%.")
        if base.pct_change().mean(numeric_only=True).notna().any():
            best = base.pct_change().mean(numeric_only=True).idxmax()
            lines.append(f"- أبرز نمو: {best}.")
        return "\n".join(lines) if lines else "لا توجد تغييرات ملحوظة."
    except Exception:
        return "تعذر إنشاء الملخص."

def apply_neon_legend(fig):
    """تطبيق التنسيق الفوسفوري على الليجند فقط"""
    fig.update_layout(
        legend=dict(
            font=dict(size=16, color="#39ff14", family="Arial, bold"),
            bgcolor="rgba(21, 34, 64, 0.9)",
            bordercolor="#00ffff",
            borderwidth=2,
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top"
        )
    )
    return fig

# ============ الواجهة الرئيسية ============
st.markdown("## 💡 لوحة البيانات المالية")

# تحميل قائمة الأوراق
try:
    ws_list = list_worksheets(PHC_SPREADSHEET_ID)
except Exception as e:
    st.error(f"تعذر فتح الملف: {e}")
    st.stop()

if not ws_list:
    st.warning("لا توجد أوراق في الملف.")
    st.stop()

# اختيار الورقة
sheet_name = st.selectbox("اختر الورقة:", ws_list)

# تحميل البيانات
df_full, header_raw, rows_raw = get_df(PHC_SPREADSHEET_ID, sheet_name)
if df_full.empty:
    st.warning(f"لا بيانات صالحة في الورقة: {sheet_name}")
    st.stop()

# فلتر التواريخ
min_d, max_d = df_full.index.min().date(), df_full.index.max().date()
start_d, end_d = st.date_input("النطاق الزمني:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
df_f = df_full.loc[pd.to_datetime(start_d):pd.to_datetime(end_d)].copy()
if df_f.empty:
    st.warning("لا توجد بيانات ضمن النطاق الزمني المحدد.")
    st.stop()

now_dt = now_cairo()
pm_end = prev_month_end(now_dt)

# التبويبات الرئيسية - نفس التبويبات الأصلية
tab_raw, tab_proc = st.tabs(["📄 Raw as-is", "📊 Processed + KPIs"])

with tab_raw:
    all_vals = get_all_values(PHC_SPREADSHEET_ID, sheet_name)
    row1 = all_vals[0] if len(all_vals) > 0 else []
    row2 = all_vals[1] if len(all_vals) > 1 else []
    row3 = all_vals[2] if len(all_vals) > 2 else []
    safe_cols = resolve_headers_merged(row1, row2, row3)
    st.dataframe(pd.DataFrame(rows_raw, columns=safe_cols))

with tab_proc:
    st.caption(f"الحسابات أدناه حتى نهاية: {pm_end.strftime('%b %Y')}")
    kpi_base = df_f.loc[:pm_end] if not df_f.loc[:pm_end].empty else df_f.copy()
    st.info(ai_summary(kpi_base))

    display_df = df_f.loc[:pm_end].reset_index().rename(columns={"__MonthDate__": "Date"})
    if display_df.empty:
        display_df = df_f.reset_index().rename(columns={"__MonthDate__": "Date"})
    display_df = display_df[["Month"] + [c for c in display_df.columns if c != "Month"]]
    
    # إصلاح عرض البيانات - تنسيق الأعمدة الرقمية فقط
    try:
        # نسخ DataFrame لتجنب تعديل الأصل
        display_df_formatted = display_df.copy()
        
        # تحديد الأعمدة الرقمية فقط
        numeric_cols = display_df_formatted.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            # تطبيق التنسيق على الأعمدة الرقمية فقط
            for col in numeric_cols:
                display_df_formatted[col] = display_df_formatted[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
        
        st.dataframe(display_df_formatted, use_container_width=True, height=400)
    except Exception:
        # إذا فشل التنسيق، عرض البيانات بدون تنسيق
        st.dataframe(display_df, use_container_width=True, height=400)

    # مؤشرات الأداء - بنفس الطريقة الأصلية
    all_cols = [c for c in df_f.columns if c != "Month"]
    
    # استخدام Config sheet للحصول على التوتالات
    try:
        totals_cfg = []
        config_vals = get_all_values(PHC_SPREADSHEET_ID, CONFIG_SHEET_NAME)
        if len(config_vals) > 1:
            header = [str(h).strip() for h in config_vals[0]]
            cfg = pd.DataFrame(config_vals[1:], columns=header)
            if TOTALS_CONFIG_COLUMN in cfg.columns:
                totals_cfg = cfg[TOTALS_CONFIG_COLUMN].dropna().astype(str).str.strip().tolist()
    except Exception:
        totals_cfg = []
    
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

# ============ مقارنة داخل نفس الورقة ============
st.markdown("---")
st.subheader("📈 مقارنة مؤشرات داخل نفس الورقة")
available_cols = [c for c in df_f.columns if c != "Month"]
sel_cols = st.multiselect("اختر مؤشرات:", available_cols, default=available_cols[:min(3, len(available_cols))])
chart_type = st.radio("نوع الرسم:", ["Line", "Bar"], horizontal=True, index=0)

fig_same = None
if sel_cols:
    df_plot = df_f.loc[:pm_end].copy()
    if df_plot.empty:
        df_plot = df_f.copy()
    fig_same = go.Figure()
    for c in sel_cols:
        if chart_type == "Line":
            fig_same.add_trace(go.Scatter(x=df_plot.index, y=df_plot[c], mode="lines+markers", name=c))
        else:
            fig_same.add_trace(go.Bar(x=df_plot.index, y=df_plot[c], name=c))
    
    # تطبيق الليجند الفوسفوري فقط
    fig_same = apply_neon_legend(fig_same)
    fig_same.update_layout(
        title=f"داخل نفس الورقة (حتى {pm_end.strftime('%b %Y')})", 
        paper_bgcolor="black", 
        plot_bgcolor="black", 
        font_color="white"
    )
    st.plotly_chart(fig_same, use_container_width=True)

# ============ مقارنة بين أوراق متعددة ============
st.markdown("---")
st.subheader("📊 مقارنة بين أوراق متعددة")
sel_sheets = st.multiselect("اختر أوراق:", ws_list, default=[sheet_name])
common_kpi = None
dfs_map = {}

if sel_sheets:
    common_cols = set(available_cols)
    for ws in sel_sheets:
        d, _, _ = get_df(PHC_SPREADSHEET_ID, ws)
        if not d.empty:
            dfs_map[ws] = d
            common_cols &= set([c for c in d.columns if c != "Month"])
    if common_cols:
        common_kpi = st.selectbox("المؤشر:", sorted(list(common_cols)))

fig_multi = None
if common_kpi:
    fig_multi = go.Figure()
    for ws, d in dfs_map.items():
        seg = d.loc[:pm_end].copy()
        if seg.empty:
            seg = d.copy()
        fig_multi.add_trace(go.Scatter(x=seg.index, y=seg[common_kpi], mode="lines+markers", name=ws))
    
    # تطبيق الليجند الفوسفوري فقط
    fig_multi = apply_neon_legend(fig_multi)
    fig_multi.update_layout(
        title=f"{common_kpi} عبر أوراق متعددة (حتى {pm_end.strftime('%b %Y')})", 
        paper_bgcolor="black", 
        plot_bgcolor="black", 
        font_color="white"
    )
    st.plotly_chart(fig_multi, use_container_width=True)

# ============ التصدير ============
st.markdown("---")
exp_all = df_f.loc[:pm_end].reset_index().rename(columns={"__MonthDate__": "Date"})
if exp_all.empty:
    exp_all = df_f.reset_index().rename(columns={"__MonthDate__": "Date"})
exp_all = exp_all[["Month"] + [c for c in exp_all.columns if c != "Month"]]
st.download_button("📥 تصدير CSV", exp_all.to_csv(index=False).encode("utf-8"), f"{sheet_name}.csv", "text/csv")

# ============ التذييل ============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>⏰ يتم عرض الوقت حسب توقيت القاهرة</p>
    <p>💰 AMANY Financial Dashboard - منصة التحليل المالي المتقدم</p>
    <p style='font-size: 12px;'>© 2024 الهيئة العامة للرعاية الصحية - فرع جنوب سيناء</p>
</div>
""", unsafe_allow_html=True)
