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

# ============ الواجهة الرئيسية ============
st.markdown('<div class="subtitle">💰 لوحة البيانات المالية المتقدمة</div>', unsafe_allow_html=True)

# تحميل قائمة الأوراق
try:
    ws_list = list_worksheets(PHC_SPREADSHEET_ID)
except Exception as e:
    st.error(f"❌ تعذر فتح الملف: {e}")
    st.stop()

if not ws_list:
    st.warning("📭 لا توجد أوراق في الملف.")
    st.stop()

# اختيار الورقة
sheet_name = st.selectbox("📋 اختر الورقة:", ws_list)

# تحميل البيانات
df_full, header_raw, rows_raw = get_df(PHC_SPREADSHEET_ID, sheet_name)
if df_full.empty:
    st.warning(f"⚠️ لا بيانات صالحة في الورقة: {sheet_name}")
    st.stop()

# فلتر التواريخ
min_d, max_d = df_full.index.min().date(), df_full.index.max().date()
start_d, end_d = st.date_input("📅 النطاق الزمني:", value=(min_d, max_d), min_value=min_d, max_value=max_d)
df_f = df_full.loc[pd.to_datetime(start_d):pd.to_datetime(end_d)].copy()
if df_f.empty:
    st.warning("⚠️ لا توجد بيانات ضمن النطاق الزمني المحدد.")
    st.stop()

now_dt = now_cairo()
pm_end = prev_month_end(now_dt)

# التبويبات الرئيسية
tab1, tab2, tab3, tab4 = st.tabs(["📊 البيانات المعالجة", "📈 التحليلات", "🔄 المقارنات", "📤 التصدير"])

with tab1:
    st.markdown("#### 📋 البيانات المعالجة والمؤشرات")
    st.caption(f"📊 الحسابات أدناه حتى نهاية: {pm_end.strftime('%b %Y')}")
    
    # الملخص الذكي
    kpi_base = df_f.loc[:pm_end] if not df_f.loc[:pm_end].empty else df_f.copy()
    with st.expander("🤖 الملخص الذكي", expanded=True):
        st.info(ai_summary(kpi_base))
    
    # عرض البيانات
    display_df = df_f.loc[:pm_end].reset_index().rename(columns={"__MonthDate__": "Date"})
    if display_df.empty:
        display_df = df_f.reset_index().rename(columns={"__MonthDate__": "Date"})
    display_df = display_df[["Month"] + [c for c in display_df.columns if c not in ["Month", "Date"]]]
    
    st.dataframe(display_df.style.format("{:,.0f}"), use_container_width=True, height=400)

with tab2:
    st.markdown("#### 📈 تحليل المؤشرات الرئيسية")
    
    # مؤشرات الأداء
    all_cols = [c for c in df_f.columns if c != "Month"]
    
    if all_cols:
        st.markdown("##### 📊 مؤشرات الأداء الرئيسية")
        num_cols = min(4, len(all_cols))
        cols_area = st.columns(num_cols)
        
        for i, col in enumerate(all_cols[:num_cols*2]):  # عرض حتى 8 مؤشرات
            s = kpi_base[col]
            if s.empty:
                continue
                
            with cols_area[i % num_cols]:
                current_val = s.iloc[-1]
                avg_val = s.mean()
                growth = ((current_val - avg_val) / avg_val * 100) if avg_val != 0 else 0
                
                st.markdown(f'''
                <div class="kpi-card">
                    <div class="kpi-title">{col}</div>
                    <div class="kpi-value">{current_val:,.0f}</div>
                    <div style="color: {'#39ff14' if growth >= 0 else '#ff4136'}; font-size: 14px; margin-top: 8px;">
                        {f'+{growth:.1f}%' if growth >= 0 else f'{growth:.1f}%'}
                    </div>
                </div>
                ''', unsafe_allow_html=True)

with tab3:
    st.markdown("#### 🔄 مقارنة المؤشرات")
    
    # مقارنة داخل الورقة
    available_cols = [c for c in df_f.columns if c != "Month"]
    sel_cols = st.multiselect("اختر المؤشرات للمقارنة:", available_cols, 
                            default=available_cols[:min(3, len(available_cols))])
    
    if sel_cols:
        df_plot = df_f.loc[:pm_end].copy()
        if df_plot.empty:
            df_plot = df_f.copy()
            
        fig = go.Figure()
        for col in sel_cols:
            fig.add_trace(go.Scatter(
                x=df_plot.index, 
                y=df_plot[col], 
                mode="lines+markers", 
                name=col,
                line=dict(width=3)
            ))
        
        fig.update_layout(
            title=f"مقارنة المؤشرات (حتى {pm_end.strftime('%b %Y')})",
            paper_bgcolor="#0b1020",
            plot_bgcolor="#0b1020", 
            font_color="#ffffff",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("#### 📤 تصدير البيانات")
    
    # تحضير البيانات للتصدير
    export_df = df_f.loc[:pm_end].reset_index().rename(columns={"__MonthDate__": "Date"})
    if export_df.empty:
        export_df = df_f.reset_index().rename(columns={"__MonthDate__": "Date"})
    export_df = export_df[["Month"] + [c for c in export_df.columns if c not in ["Month", "Date"]]]
    
    # تصدير CSV
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 تحميل CSV",
        data=csv_data,
        file_name=f"financial_data_{sheet_name}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # تصدير Excel
    try:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📊 تحميل Excel",
            data=excel_data,
            file_name=f"financial_data_{sheet_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"⚠️ تعذر إنشاء ملف Excel: {e}")

# ============ معلومات المكتبات ============
with st.sidebar:
    st.markdown("### ℹ️ معلومات النظام")
    
    lib_status = {
        "Kaleido (تصدير الصور)": KALEIDO_AVAILABLE,
        "Statsmodels (تحليلات متقدمة)": STATSMODELS_AVAILABLE,
        "Pytz (توقيت القاهرة)": PYTZ_AVAILABLE
    }
    
    for lib, status in lib_status.items():
        if status:
            st.success(f"✅ {lib}")
        else:
            st.warning(f"⚠️ {lib}")

# ============ التذييل ============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>⏰ يتم عرض الوقت حسب توقيت القاهرة</p>
    <p>💰 AMANY Financial Dashboard v2.0 - منصة التحليل المالي المتقدم</p>
    <p style='font-size: 12px;'>© 2024 الهيئة العامة للرعاية الصحية - فرع جنوب سيناء</p>
</div>
""", unsafe_allow_html=True)
