# app.py — لوحة تحليل البيانات الصحية مع التنسيق الفوسفوري
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from collections.abc import Mapping
import time
import pytz
import json

# ============ إعداد الصفحة والستايل ============
st.set_page_config(
    page_title="AMANY - لوحة التحكم المتقدمة", 
    layout="wide", 
    page_icon="🏥"
)

# ============ توقيت القاهرة ============
def get_cairo_time():
    """الحصول على الوقت الحالي بتوقيت القاهرة"""
    cairo_tz = pytz.timezone('Africa/Cairo')
    return datetime.now(cairo_tz)

# ============ التنسيق الفوسفوري المتكامل ============
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
    background: linear-gradient(135deg, #0b1020, #1a1f38);
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

/* الشريط الجانبي الفوسفوري */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f38, #0b1020) !important;
    border-right: 3px solid var(--neon-green) !important;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-weight: 500;
}

.sidebar-header {
    color: var(--neon-green) !important;
    font-weight: bold;
    font-size: 22px;
    margin-bottom: 20px;
    text-shadow: 0 0 8px rgba(57, 255, 20, 0.6);
    text-align: center;
}

.sidebar-section {
    background: rgba(21, 34, 64, 0.9);
    padding: 15px;
    border-radius: 12px;
    margin: 15px 0;
    border: 1px solid var(--neon-blue);
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
}

/* تنسيق عناصر الشريط الجانبي */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    background: rgba(41, 57, 92, 0.8) !important;
    border: 1px solid var(--neon-purple) !important;
    border-radius: 10px;
    padding: 10px;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
    background: rgba(41, 57, 92, 0.8) !important;
    border: 1px solid var(--neon-orange) !important;
    border-radius: 8px;
}

[data-testid="stSidebar"] .stSlider [role="slider"] {
    background: var(--neon-green) !important;
}

[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(45deg, var(--neon-green), var(--neon-blue)) !important;
    color: #000 !important;
    font-weight: bold;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 0 12px rgba(57, 255, 20, 0.5);
}

[data-testid="stSidebar"] .stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(57, 255, 20, 0.8);
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

/* تنسيق البيانات والجداول */
.stDataFrame {
    border: 1px solid var(--neon-blue) !important;
    border-radius: 10px !important;
}

.stDataFrame [data-testid="stDataFrame"] {
    background: rgba(21, 34, 64, 0.9) !important;
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

/* الشرائح والأدوات */
.stSlider [role="slider"] {
    background: var(--neon-green) !important;
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
</style>
""", unsafe_allow_html=True)

# ============ إصلاح مشكلة Secrets ============
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

# ============ معرف ملف البيانات ============
PHC_SPREADSHEET_ID = "1ptbPIJ9Z0k92SFcXNqAeC61SXNpamCm-dXPb97cPT_4"

# ============ الدوال المساعدة للاتصال ============
def with_backoff(func, *args, **kwargs):
    """إعادة المحاولة مع فترات انتظار"""
    for delay in [0.5, 1, 2, 4, 8]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("فشلت جميع محاولات إعادة الاتصال")

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
def list_facility_sheets(spreadsheet_id: str):
    """الحصول على قائمة المنشآت"""
    try:
        sh = get_spreadsheet(spreadsheet_id)
        if not sh:
            return []
        titles = [ws.title for ws in sh.worksheets()]
        blacklist = {"config", "config!", "readme", "financial", "kpi", "test"}
        facilities = [t for t in titles if t.strip().lower() not in blacklist]
        return facilities
    except Exception as e:
        st.error(f"❌ خطأ في قراءة قائمة المنشآت: {e}")
        return []

@st.cache_data(ttl=900)
def get_df_from_sheet(spreadsheet_id: str, worksheet_name: str) -> pd.DataFrame:
    """قراءة البيانات من الورقة"""
    try:
        sh = get_spreadsheet(spreadsheet_id)
        if not sh:
            return pd.DataFrame()
        ws = sh.worksheet(worksheet_name.strip())
        vals = ws.get_all_values()
        
        if not vals:
            return pd.DataFrame()
            
        header = [str(h).strip() for h in vals[0]]
        cols = pd.Series(header, dtype=str)
        
        for dup in cols[cols.duplicated()].unique():
            idxs = list(cols[cols == dup].index)
            for i, idx in enumerate(idxs):
                cols.iloc[idx] = dup if i == 0 else f"{dup}.{i}"
                
        return pd.DataFrame(vals[1:], columns=cols)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الورقة '{worksheet_name}': {e}")
        return pd.DataFrame()

# ============ الألوان الفوسفورية للرسوم البيانية ============
NEON_COLORS = [
    "#39ff14",  # أخضر فوسفوري
    "#00ffff",  # أزرق فوسفوري
    "#ff00ff",  # وردي فوسفوري
    "#ffff00",  # أصفر فوسفوري
    "#ff8c00",  # برتقالي فوسفوري
    "#da70d6",  # بنفسجي فوسفوري
    "#00ff7f",  # أخضر ربيعي
    "#1e90ff",  # أزرق دودجر
]

def apply_neon_chart_layout(fig, title: str = "", height: int = 600):
    """تطبيق التنسيق الفوسفوري على الرسم البياني"""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=26, color="#39ff14", family="Arial, bold"),
            x=0.5,
            xanchor="center"
        ),
        height=height,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font=dict(color="#ffffff", size=14),
        legend=dict(
            font=dict(size=16, color="#39ff14", family="Arial, bold"),
            bgcolor="rgba(21, 34, 64, 0.9)",
            bordercolor="#00ffff",
            borderwidth=2,
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top"
        ),
        xaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=18, color="#00ffff", family="Arial, bold"),
            tickfont=dict(size=14, color="#ffffff", family="Arial"),
            linecolor="#39ff14",
            linewidth=2
        ),
        yaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=18, color="#00ffff", family="Arial, bold"),
            tickfont=dict(size=14, color="#ffffff", family="Arial"),
            linecolor="#39ff14",
            linewidth=2
        ),
        margin=dict(l=60, r=30, t=80, b=60),
        hoverlabel=dict(
            bgcolor="#152240",
            font_size=16,
            font_color="#ffffff",
            bordercolor="#39ff14"
        )
    )
    return fig

# ============ أدوات الرسم البياني ============
def style_dataframe(df: pd.DataFrame):
    if df.empty:
        return df
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="ignore")
    numeric_cols = df.select_dtypes(include=np.number).columns
    fmt = {col: "{:,.0f}" for col in numeric_cols}
    return df.style.format(fmt).set_properties(**{
        "font-size": "16px", 
        "border": "1px solid #5a7ff0",
        "background-color": "#152240",
        "color": "#ffffff"
    })

def robust_parse_date(series: pd.Series) -> pd.Series:
    s = series.astype(object)
    def map_to_ts(v):
        try:
            if isinstance(v, Mapping):
                y = v.get("year") or v.get("Year")
                m = v.get("month") or v.get("Month")
                d = v.get("day") or v.get("Day") or 1
                if y and m:
                    return pd.Timestamp(int(y), int(m), int(d))
            return v
        except Exception:
            return v
    s = s.map(map_to_ts)
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
    mask_na = dt.isna()
    if mask_na.any():
        s2 = pd.Series(s[mask_na]).astype(str).str.strip()
        m1 = pd.to_datetime(s2, format="%m/%Y", errors="coerce")
        m2 = pd.to_datetime(s2, format="%m-%Y", errors="coerce")
        m3 = pd.to_datetime(s2, format="%Y-%m", errors="coerce")
        merged = m1.fillna(m2).fillna(m3)
        dt.loc[mask_na] = merged
    mask_na = dt.isna()
    if mask_na.any():
        def as_serial(v):
            try: return pd.to_datetime(float(v), unit="d", origin="1899-12-30")
            except Exception: return pd.NaT
        dt.loc[mask_na] = pd.Series(s[mask_na]).map(as_serial)
    return dt

def display_trend_analysis(df: pd.DataFrame, date_col: str, service_col: str):
    data = df[[date_col, service_col]].copy()
    data = data.dropna(subset=[date_col])
    if data.empty or len(data) < 2:
        st.info("لا توجد بيانات كافية لعرض خط الاتجاه.")
        return
    data["day_num"] = (data[date_col] - data[date_col].min()).dt.days
    y = pd.to_numeric(data[service_col], errors="coerce").fillna(0)
    if y.nunique() == 0:
        st.info("لا توجد تغييرات كافية لعرض الاتجاه.")
        return
    z = np.polyfit(data["day_num"], y, 1)
    p = np.poly1d(z)
    trend = p(data["day_num"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data[date_col], y=y, mode="lines+markers", name="القيم الفعلية",
        line=dict(color=NEON_COLORS[0], width=4),
        marker=dict(size=8, color=NEON_COLORS[1])
    ))
    fig.add_trace(go.Scatter(
        x=data[date_col], y=trend, mode="lines", name="خط الاتجاه",
        line=dict(color=NEON_COLORS[2], dash="dash", width=3)
    ))
    apply_neon_chart_layout(fig, f"📈 تحليل الاتجاه: {service_col}", height=650)
    st.plotly_chart(fig, use_container_width=True)

# ============ فلتر تاريخ موحد ============
def get_date_filter_keys(prefix: str):
    return f"{prefix}_range", f"{prefix}_start", f"{prefix}_end"

def apply_date_filter(df: pd.DataFrame, date_col: str, prefix: str):
    key_range, key_start, key_end = get_date_filter_keys(prefix)
    
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-header">⏰ فلتر التواريخ</div>', unsafe_allow_html=True)
    
    time_range = st.sidebar.selectbox(
        "اختر النطاق الزمني:",
        ("آخر 7 أيام", "آخر 30 يومًا", "هذا الشهر", "كل الوقت", "نطاق مخصص"),
        key=key_range
    )
    
    today = datetime.now()
    if time_range == "آخر 7 أيام":
        result = df[df[date_col] >= (today - timedelta(days=7))]
    elif time_range == "آخر 30 يومًا":
        result = df[df[date_col] >= (today - timedelta(days=30))]
    elif time_range == "هذا الشهر":
        result = df[df[date_col].dt.month == today.month]
    elif time_range == "نطاق مخصص":
        start_date = st.sidebar.date_input("📅 من تاريخ", df[date_col].min().date(), key=key_start)
        end_date = st.sidebar.date_input("📅 إلى تاريخ", df[date_col].max().date(), key=key_end)
        result = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]
    else:
        result = df
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    return result

# ============ عرض منشأة مع تحسينات ============
def display_facility_dashboard(df: pd.DataFrame, facility_name: str, range_prefix: str):
    if df.empty or len(df.columns) == 0:
        st.info("📭 لا توجد بيانات لعرضها.")
        return
        
    date_col = df.columns[0]
    df = df.copy()
    df[date_col] = robust_parse_date(df[date_col])
    df = df.dropna(subset=[date_col])
    
    if df.empty or df[date_col].nunique() < 2:
        st.markdown(f'<div class="subtitle">📊 عرض البيانات: {facility_name}</div>', unsafe_allow_html=True)
        st.dataframe(style_dataframe(df.copy()), use_container_width=True, height=520)
        return
        
    for col in df.columns:
        if col != date_col:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    st.markdown(f'<div class="subtitle">🏥 لوحة المنشأة: {facility_name}</div>', unsafe_allow_html=True)

    df_filtered = apply_date_filter(df, date_col, prefix=range_prefix)
    if df_filtered.empty:
        st.warning("⚠️ لا توجد بيانات في النطاق الزمني المحدد.")
        return

    # ============ تحسينات جديدة للعرض ============
    
    # 1. نظرة سريعة على البيانات
    st.markdown('<div class="subtitle">🚀 نظرة سريعة</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(df_filtered)
        st.metric("📈 عدد السجلات", f"{total_records:,}")
    
    with col2:
        date_range = f"{df_filtered[date_col].min().strftime('%Y-%m-%d')} إلى {df_filtered[date_col].max().strftime('%Y-%m-%d')}"
        st.metric("📅 النطاق الزمني", date_range)
    
    with col3:
        numeric_cols = df_filtered.select_dtypes(include=np.number).columns
        total_values = df_filtered[numeric_cols].sum().sum()
        st.metric("💰 إجمالي القيم", f"{total_values:,.0f}")
    
    with col4:
        avg_per_day = total_values / max(1, len(df_filtered))
        st.metric("📊 متوسط يومي", f"{avg_per_day:,.0f}")

    # 2. الملخص الإجمالي للخدمات
    st.markdown('<div class="subtitle">📋 الملخص الإجمالي للخدمات</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    clinic_cols = [col for col in df_filtered.columns[1:7] if col in df_filtered.columns]
    dental_cols = [col for col in df_filtered.columns[8:15] if col in df_filtered.columns]

    with c1:
        st.markdown("#### 🏥 تردد العيادات")
        clinic_totals = df_filtered[clinic_cols].sum(numeric_only=True)
        if len(clinic_totals):
            fig_pie = px.pie(
                values=clinic_totals.values, 
                names=clinic_totals.index, 
                hole=0.4,
                color_discrete_sequence=NEON_COLORS
            )
            fig_pie.update_traces(
                textposition="inside", 
                textinfo="percent+label",
                textfont=dict(size=14, color="#ffffff", family="Arial, bold"),
                pull=[0.05] * len(clinic_totals),
                marker=dict(line=dict(color="#ffffff", width=2))
            )
            apply_neon_chart_layout(fig_pie, "نسبة تردد العيادات", height=500)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("ℹ️ لا توجد أعمدة تردد العيادات")

    with c2:
        st.markdown("#### 🦷 خدمات الأسنان")
        dental_totals = df_filtered[dental_cols].sum(numeric_only=True)
        if len(dental_totals):
            fig_bar = px.bar(
                y=dental_totals.index, 
                x=dental_totals.values, 
                orientation="h",
                labels={"y": "الخدمة", "x": "الإجمالي"}, 
                text_auto=True,
                color_discrete_sequence=NEON_COLORS
            )
            fig_bar.update_traces(
                textfont=dict(size=14, color="#ffffff", family="Arial, bold"),
                marker_line_width=1.5, 
                marker_line_color="#ffffff"
            )
            apply_neon_chart_layout(fig_bar, "إجمالي خدمات الأسنان", height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("ℹ️ لا توجد أعمدة خدمات الأسنان")

    # 3. مؤشرات الأداء الرئيسية (الكروت الفوسفورية)
    st.markdown('<div class="subtitle">📊 مؤشرات الأداء الرئيسية</div>', unsafe_allow_html=True)
    
    pharmacy_cols = [col for col in df_filtered.columns[15:17] if col in df_filtered.columns]
    all_chart_cols = clinic_cols + dental_cols + pharmacy_cols
    kpi_card_cols = [col for col in df_filtered.columns if col not in all_chart_cols and col != date_col]
    all_kpi_cols = pharmacy_cols + kpi_card_cols
    
    if all_kpi_cols:
        top_n = st.slider(
            "🎚️ عدد الكروت المعروضة:", 
            4, max(4, len(all_kpi_cols)), 
            value=min(8, len(all_kpi_cols)), 
            key=f"topn_{range_prefix}"
        )
        
        totals = pd.Series({k: pd.to_numeric(df_filtered[k], errors="coerce").sum() for k in all_kpi_cols})
        totals = totals.sort_values(ascending=False).head(top_n)
        
        num_cols = min(len(totals), 4)
        grid = st.columns(num_cols if num_cols else 1)
        
        for i, (kpi, total) in enumerate(totals.items()):
            with grid[i % max(1, num_cols)]:
                st.markdown(f'''
                <div class="kpi-card">
                    <div class="kpi-title">{kpi}</div>
                    <div class="kpi-value">{int(total):,}</div>
                </div>
                ''', unsafe_allow_html=True)

    # 4. تحليل ومقارنة أداء الخدمات
    st.markdown('<div class="subtitle">📈 تحليل ومقارنة أداء الخدمات</div>', unsafe_allow_html=True)
    
    all_services = df_filtered.columns.drop(date_col)
    selected = st.multiselect(
        "🔍 اختر خدمة أو أكثر لعرضها:", 
        options=all_services, 
        key=f"multi_{range_prefix}",
        max_selections=5
    )
    
    chart_kind_local = st.radio(
        "📊 نوع الرسم:", 
        ["📈 Line", "📊 Bar"], 
        key=f"kind_{range_prefix}", 
        horizontal=True
    )
    
    if selected:
        if len(selected) > 1:
            if chart_kind_local == "📈 Line":
                fig_line = px.line(
                    df_filtered, 
                    x=date_col, 
                    y=selected, 
                    markers=True,
                    title="مقارنة أداء الخدمات المختارة",
                    color_discrete_sequence=NEON_COLORS
                )
                apply_neon_chart_layout(fig_line, "مقارنة أداء الخدمات المختارة", height=650)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                fig_bar2 = px.bar(
                    df_filtered, 
                    x=date_col, 
                    y=selected, 
                    barmode="group",
                    title="مقارنة أداء الخدمات المختارة",
                    color_discrete_sequence=NEON_COLORS
                )
                apply_neon_chart_layout(fig_bar2, "مقارنة أداء الخدمات المختارة", height=650)
                st.plotly_chart(fig_bar2, use_container_width=True)
        else:
            display_trend_analysis(df_filtered, date_col, selected[0])

    # 5. البيانات التفصيلية
    st.markdown('<div class="subtitle">📋 البيانات التفصيلية</div>', unsafe_allow_html=True)
    st.dataframe(style_dataframe(df_filtered.copy()), use_container_width=True, height=500)

# ============ مقارنة منشآت محسنة ============
def compare_facilities():
    st.markdown('<div class="subtitle">⚖️ مقارنة المنشآت</div>', unsafe_allow_html=True)
    
    try:
        ws_list = list_facility_sheets(PHC_SPREADSHEET_ID)
    except Exception as e:
        st.error(f"❌ تعذر قراءة قائمة الأوراق: {e}")
        return
        
    if not ws_list:
        st.info("📭 لا توجد منشآت متاحة.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        sel_facilities = st.multiselect(
            "🏭 اختر المنشآت للمقارنة:",
            ws_list,
            key="fac_multi",
            max_selections=6
        )
    
    with col2:
        chart_kind = st.radio(
            "📊 نوع الرسم البياني:",
            ["📈 Line", "📊 Bar"],
            horizontal=True,
            key="fac_kind"
        )

    if not sel_facilities:
        st.info("💡 يرجى اختيار منشآت للمقارنة")
        return

    # تحميل ومعالجة البيانات
    data_map = {}
    common_cols = None
    
    with st.spinner("🔄 جاري تحميل بيانات المنشآت..."):
        for w in sel_facilities:
            dfw = get_df_from_sheet(PHC_SPREADSHEET_ID, w).copy()
            if dfw.empty or len(dfw.columns) < 2:
                continue
                
            dcol = dfw.columns[0]
            dfw[dcol] = robust_parse_date(dfw[dcol])
            dfw = dfw.dropna(subset=[dcol]).sort_values(dcol)
            
            for c in dfw.columns:
                if c != dcol:
                    dfw[c] = pd.to_numeric(dfw[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
                    
            data_map[w] = (dcol, dfw)
            cols = set([c for c in dfw.columns if c != dcol])
            common_cols = cols if common_cols is None else (common_cols & cols)

    if not data_map:
        st.info("📊 لا توجد بيانات صالحة للمنشآت المختارة.")
        return
        
    if not common_cols:
        st.info("🔍 لا يوجد مؤشر مشترك بين كل المنشآت المختارة.")
        return

    # اختيار المؤشر للمقارنة
    kpi = st.selectbox(
        "📈 اختر المؤشر للمقارنة:",
        sorted(list(common_cols)),
        key="fac_kpi"
    )

    if not kpi:
        return

    # تطبيق الفلتر الزمني
    all_dates = []
    for _, (dc, dfw) in data_map.items():
        all_dates.append(dfw[[dc]].rename(columns={dc: "Date"}))
        
    union_dates = pd.concat(all_dates, ignore_index=True).dropna()
    if union_dates.empty:
        st.info("📅 لا توجد تواريخ متاحة للمقارنة.")
        return

    min_dt = pd.to_datetime(union_dates["Date"].min()).normalize()
    max_dt = pd.to_datetime(union_dates["Date"].max()).normalize()

    df_range = pd.DataFrame({"Date": pd.date_range(min_dt, max_dt, freq="D")})
    df_range_filtered = apply_date_filter(df_range, "Date", prefix="cmp")
    
    if df_range_filtered.empty:
        start_sel, end_sel = min_dt, max_dt
    else:
        start_sel = pd.to_datetime(df_range_filtered["Date"].min()).normalize()
        end_sel = pd.to_datetime(df_range_filtered["Date"].max()).normalize()

    # إنشاء الرسم البياني للمقارنة
    fig = go.Figure()
    
    for i, (w, (dcol, dfw)) in enumerate(data_map.items()):
        seg = dfw[(dfw[dcol] >= start_sel) & (dfw[dcol] <= end_sel)].copy()
        if seg.empty or kpi not in seg.columns:
            continue
            
        seg[dcol] = pd.to_datetime(seg[dcol]).dt.normalize()
        
        if chart_kind == "📈 Line":
            fig.add_trace(go.Scatter(
                x=seg[dcol], 
                y=seg[kpi], 
                mode="lines+markers",
                name=w,
                line=dict(width=3, color=NEON_COLORS[i % len(NEON_COLORS)]),
                marker=dict(size=6)
            ))
        else:
            fig.add_trace(go.Bar(
                x=seg[dcol], 
                y=seg[kpi], 
                name=w,
                marker_color=NEON_COLORS[i % len(NEON_COLORS)],
                marker_line_width=1.5,
                marker_line_color="#ffffff"
            ))

    apply_neon_chart_layout(fig, f"📊 مقارنة {kpi} عبر المنشآت", height=700)
    
    days_span = (end_sel - start_sel).days
    if days_span > 90:
        fig.update_xaxes(tickformat="%Y-%m", dtick="M1")
    else:
        fig.update_xaxes(tickformat="%Y-%m-%d", dtick="D1")
        
    st.plotly_chart(fig, use_container_width=True)

    # إحصائيات سريعة للمقارنة
    st.markdown("### 📋 ملخص المقارنة")
    comp_data = []
    for w, (dcol, dfw) in data_map.items():
        seg = dfw[(dfw[dcol] >= start_sel) & (dfw[dcol] <= end_sel)]
        if kpi in seg.columns:
            total = seg[kpi].sum()
            avg = seg[kpi].mean()
            comp_data.append({
                "المنشأة": w,
                "الإجمالي": f"{total:,.0f}",
                "المتوسط": f"{avg:,.1f}",
                "عدد الأيام": len(seg)
            })
    
    if comp_data:
        comp_df = pd.DataFrame(comp_data)
        st.dataframe(comp_df, use_container_width=True)

# ============ الواجهة الرئيسية المحسنة ============
def main():
    # الهيدر الرئيسي
    st.markdown(
        """
<div class="main-header">
  <div class="main-title">🏥 AMANY</div>
  <div class="sub-title">Advanced Medical Analytics Networking Yielding</div>
  <div class="sub-title">منصة التحليل المتقدم للرعاية الصحية الأولية - فرع جنوب سيناء</div>
</div>
""",
        unsafe_allow_html=True,
    )
    
    # توقيت القاهرة
    cairo_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {cairo_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)

    # الشريط الجانبي المحسن
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🎛️ لوحة التحكم</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        app_mode = st.radio(
            "📊 اختر طريقة العرض:",
            ("🏠 الإجماليات", "🏭 حسب المنشأة", "⚖️ مقارنة المنشآت"),
            key="mode"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">📁 التطبيقات</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="padding: 10px;">
            <p>• 🤖 ASK AMANY</p>
            <p>• 📦 Inventory</p>
            <p>• 📈 Monthly Indicators</p>
            <p>• 💰 Financial Data</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # زر تحديث البيانات
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # المحتوى الرئيسي
    if app_mode == "🏠 الإجماليات":
        st.header("📊 لوحة التحكم الرئيسية (الإجماليات)")
        df_phc = get_df_from_sheet(PHC_SPREADSHEET_ID, "PHC Dashboard")
        if not df_phc.empty:
            display_facility_dashboard(df_phc, "PHC Dashboard", range_prefix="main")
        else:
            st.info("📭 لم يتم العثور على بيانات صالحة في PHC Dashboard.")
            
    elif app_mode == "🏭 حسب المنشأة":
        st.header("🏭 عرض البيانات حسب المنشأة")
        try:
            ws_list = list_facility_sheets(PHC_SPREADSHEET_ID)
        except Exception as e:
            st.error(f"❌ تعذر قراءة قائمة الأوراق: {e}")
            return
            
        if not ws_list:
            st.info("📭 لا توجد منشآت متاحة.")
            return
            
        selected_ws = st.selectbox("🔍 اختر المنشأة:", ws_list, index=0, key="fac_sel")
        df_sel = get_df_from_sheet(PHC_SPREADSHEET_ID, selected_ws)
        
        if df_sel.empty:
            st.info("📭 لا توجد بيانات في الورقة المحددة.")
            return
            
        display_facility_dashboard(df_sel, selected_ws, range_prefix="fac")
        
    else:
        compare_facilities()

    # التذييل
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>⏰ يتم عرض الوقت حسب توقيت القاهرة</p>
        <p>🏥 AMANY Dashboard v4.0 - منصة التحليل المتقدم للرعاية الصحية</p>
        <p style='font-size: 12px;'>© 2024 الهيئة العامة للرعاية الصحية - فرع جنوب سيناء</p>
    </div>
    """, unsafe_allow_html=True)

# تشغيل التطبيق
if __name__ == "__main__":
    main()
