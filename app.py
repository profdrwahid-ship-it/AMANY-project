# app.py — لوحة تحليل البيانات الصحية مع توقيت القاهرة وتنسيق فوسفوري
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

# ============ التنسيق الفوسفوري ============
st.markdown("""
<style>
:root {
    --neon-green: #39ff14;
    --neon-blue: #00ffff;
    --neon-pink: #ff00ff;
    --neon-orange: #ff8c00;
    --neon-yellow: #ffff00;
    --bg-dark: #0b1020;
    --card-bg: #152240;
    --border-glow: #5a7ff0;
}

/* الخلفية الرئيسية */
.stApp {
    background: linear-gradient(135deg, #0b1020, #1a1f38);
}

/* الهيدر الرئيسي */
.main-header {
    background: linear-gradient(90deg, #152240, #2c4ba0);
    padding: 25px;
    text-align: center;
    border-radius: 15px;
    margin-bottom: 20px;
    border: 2px solid var(--neon-green);
    box-shadow: 0 0 20px rgba(57, 255, 20, 0.3);
}

.main-title {
    font-size: 48px;
    font-weight: 900;
    color: var(--neon-green);
    text-shadow: 0 0 10px rgba(57, 255, 20, 0.7);
    letter-spacing: 3px;
    margin: 0;
}

.sub-title {
    font-size: 20px;
    color: var(--neon-blue);
    margin: 10px 0;
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}

/* شريط الوقت */
.time-display {
    background: rgba(21, 34, 64, 0.8);
    padding: 15px;
    text-align: center;
    border-radius: 10px;
    margin: 15px 0;
    border: 1px solid var(--neon-green);
    box-shadow: 0 0 15px rgba(57, 255, 20, 0.2);
}

.time-text {
    font-size: 24px;
    font-weight: bold;
    color: var(--neon-green);
    text-shadow: 0 0 8px rgba(57, 255, 20, 0.6);
}

/* الكروت */
.kpi-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    border: 1px solid var(--border-glow);
    box-shadow: 0 0 15px rgba(90, 127, 240, 0.2);
    text-align: center;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 20px rgba(57, 255, 20, 0.4);
}

.kpi-title {
    color: var(--neon-blue) !important;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
    text-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
}

.kpi-value {
    color: var(--neon-green) !important;
    font-size: 32px;
    font-weight: 900;
    text-shadow: 0 0 8px rgba(57, 255, 20, 0.5);
}

/* الشريط الجانبي */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f38, #0b1020) !important;
    border-right: 2px solid var(--neon-green) !important;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

.sidebar-section {
    background: rgba(21, 34, 64, 0.8);
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    border: 1px solid var(--neon-blue);
}

/* العناوين */
h1, h2, h3, h4, h5, h6 {
    color: var(--neon-green) !important;
    text-shadow: 0 0 5px rgba(57, 255, 20, 0.3);
}

/* الأزرار */
.stButton button {
    background: linear-gradient(45deg, var(--neon-green), var(--neon-blue)) !important;
    color: #000 !important;
    font-weight: bold;
    border: none !important;
    border-radius: 8px !important;
    transition: all 0.3s ease;
}

.stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
}

/* تنسيق النصوص */
.section-title {
    color: var(--neon-green) !important;
    font-size: 28px;
    font-weight: bold;
    text-align: center;
    margin: 25px 0;
    padding: 10px;
    border-bottom: 2px solid var(--neon-blue);
}

.feature-card {
    background: var(--card-bg);
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
    border: 1px solid var(--neon-blue);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

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
        # التحقق من وجود secrets
        if "gcp_service_account" not in st.secrets:
            st.error("❌ لم يتم إعداد مفاتيح الخدمة في Streamlit Cloud")
            return None
            
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
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
            st.error("❌ تعذر الاتصال بملف البيانات")
            return []
        titles = [ws.title for ws in with_backoff(sh.worksheets)]
        # استبعاد الأوراق غير المرغوبة
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
        ws = with_backoff(sh.worksheet, worksheet_name.strip())
        vals = with_backoff(ws.get_all_values)
        
        if not vals:
            st.warning(f"⚠️ الورقة '{worksheet_name}' فارغة")
            return pd.DataFrame()
            
        # معالجة الرأس
        header = [str(h).strip() for h in vals[0]]
        cols = pd.Series(header, dtype=str)
        
        # معالجة الأعمدة المكررة
        for dup in cols[cols.duplicated()].unique():
            idxs = list(cols[cols == dup].index)
            for i, idx in enumerate(idxs):
                cols.iloc[idx] = dup if i == 0 else f"{dup}.{i}"
                
        df = pd.DataFrame(vals[1:], columns=cols)
        st.success(f"✅ تم تحميل {len(df)} صف من '{worksheet_name}'")
        return df
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الورقة '{worksheet_name}': {e}")
        return pd.DataFrame()

# ============ الألوان الفوسفورية للرسوم ============
NEON_COLORS = [
    "#39ff14",  # أخضر فوسفوري
    "#00ffff",  # أزرق فوسفوري
    "#ff00ff",  # وردي فوسفوري
    "#ffff00",  # أصفر فوسفوري
    "#ff8c00",  # برتقالي فوسفوري
    "#ff1493",  # وردي غامق
]

# ============ تنسيق الرسوم البيانية ============
def apply_neon_layout(fig, title: str = "", height: int = 600):
    """تطبيق التنسيق الفوسفوري على الرسم البياني"""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=28, color="#39ff14", family="Arial, bold"),
            x=0.5,
            xanchor="center"
        ),
        height=height,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font=dict(color="#ffffff", size=16, family="Arial"),
        legend=dict(
            font=dict(size=16, color="#ffffff"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="#39ff14",
            borderwidth=1
        ),
        xaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=20, color="#00ffff"),
            tickfont=dict(size=16, color="#ffffff"),
            linecolor="#39ff14",
            linewidth=2
        ),
        yaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=20, color="#00ffff"),
            tickfont=dict(size=16, color="#ffffff"),
            linecolor="#39ff14",
            linewidth=2
        ),
        margin=dict(l=50, r=30, t=80, b=50),
        hoverlabel=dict(
            bgcolor="#152240",
            font_size=16,
            font_color="#ffffff"
        )
    )
    return fig

# ============ تحليل البيانات ============
def style_dataframe(df: pd.DataFrame):
    """تنسيق الجداول"""
    if df.empty:
        return df
        
    # تحويل الأعمدة الرقمية
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
    """تحليل التواريخ بطرق متعددة"""
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
    
    # محاولة تنسيقات إضافية
    mask_na = dt.isna()
    if mask_na.any():
        s2 = pd.Series(s[mask_na]).astype(str).str.strip()
        m1 = pd.to_datetime(s2, format="%m/%Y", errors="coerce")
        m2 = pd.to_datetime(s2, format="%m-%Y", errors="coerce")
        m3 = pd.to_datetime(s2, format="%Y-%m", errors="coerce")
        merged = m1.fillna(m2).fillna(m3)
        dt.loc[mask_na] = merged
        
    return dt

# ============ الصفحة الرئيسية ============
def show_main_dashboard():
    """عرض الصفحة الرئيسية"""
    
    # الهيدر الرئيسي
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🏥 AMANY</div>
        <div class="sub-title">Advanced Medical Analytics Networking Yielding</div>
        <div class="sub-title">منصة التحليل المتقدم للرعاية الصحية الأولية - فرع جنوب سيناء</div>
    </div>
    """, unsafe_allow_html=True)

    # عرض وقت القاهرة
    cairo_time = get_cairo_time()
    st.markdown(f"""
    <div class="time-display">
        <div class="time-text">⏰ توقيت القاهرة: {cairo_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

    # الميزات الرئيسية
    st.markdown('<div class="section-title">🎯 الميزات الرئيسية</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 تحليل البيانات</h3>
            <p>عرض وتحليل المؤشرات الصحية الشاملة</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🏭 إدارة المنشآت</h3>
            <p>متابعة أداء المنشآت الصحية المختلفة</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 التقارير</h3>
            <p>تقارير تفصيلية ورسوم بيانية متقدمة</p>
        </div>
        """, unsafe_allow_html=True)

    # البيانات السريعة - تحميل تلقائي للبيانات
    st.markdown('<div class="section-title">🚀 تحميل البيانات</div>', unsafe_allow_html=True)
    
    # زر تحميل البيانات
    if st.button("🔄 تحميل البيانات من Google Sheets", type="primary"):
        with st.spinner("جاري تحميل البيانات..."):
            try:
                # تحميل البيانات الرئيسية تلقائياً
                df_main = get_df_from_sheet(PHC_SPREADSHEET_ID, "PHC Dashboard")
                
                if not df_main.empty:
                    st.success(f"✅ تم تحميل {len(df_main)} صف من البيانات بنجاح")
                    
                    # عرض بعض الإحصائيات
                    numeric_cols = df_main.select_dtypes(include=np.number).columns
                    if len(numeric_cols) > 0:
                        st.markdown("### 📊 الإحصائيات السريعة")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_sum = df_main[numeric_cols].sum().sum()
                            st.metric("إجمالي النشاط", f"{total_sum:,.0f}")
                            
                        with col2:
                            avg_per_col = df_main[numeric_cols].mean().mean()
                            st.metric("متوسط النشاط", f"{avg_per_col:,.0f}")
                            
                        with col3:
                            max_value = df_main[numeric_cols].max().max()
                            st.metric("أعلى قيمة", f"{max_value:,.0f}")
                            
                        with col4:
                            facilities_count = len(list_facility_sheets(PHC_SPREADSHEET_ID))
                            st.metric("عدد المنشآت", facilities_count)
                        
                        # عرض عينة من البيانات
                        st.markdown("### 📋 عينة من البيانات")
                        st.dataframe(df_main.head(10), use_container_width=True)
                    else:
                        st.warning("⚠️ لا توجد أعمدة رقمية في البيانات")
                else:
                    st.error("❌ لم يتم تحميل أي بيانات")
                    
            except Exception as e:
                st.error(f"❌ خطأ في تحميل البيانات: {e}")
    else:
        st.info("💡 انقر فوق زر 'تحميل البيانات' لاستيراد البيانات من Google Sheets")

# ============ عرض لوحة المنشأة ============
def display_facility_dashboard(df: pd.DataFrame, facility_name: str):
    """عرض لوحة البيانات للمنشأة"""
    if df.empty:
        st.info("📭 لا توجد بيانات لعرضها.")
        return
        
    # معالجة العمود الأول كتاريخ
    date_col = df.columns[0]
    df = df.copy()
    df[date_col] = robust_parse_date(df[date_col])
    df = df.dropna(subset=[date_col])
    
    if df.empty:
        st.info("📅 لا توجد تواريخ صالحة للعرض.")
        return

    # تحويل الأعمدة الرقمية
    for col in df.columns:
        if col != date_col:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    # الهيدر
    st.markdown(f"""
    <div class="main-header">
        <div class="main-title">📊 {facility_name}</div>
        <div class="sub-title">لوحة تحليل البيانات التفصيلية</div>
    </div>
    """, unsafe_allow_html=True)

    # المؤشرات الرئيسية
    st.markdown("### 📈 المؤشرات الرئيسية")
    numeric_cols = df.select_dtypes(include=np.number).columns
    
    if len(numeric_cols) > 0:
        # عرض أهم 6 مؤشرات
        totals = df[numeric_cols].sum().sort_values(ascending=False).head(6)
        cols = st.columns(3)
        
        for i, (kpi, total) in enumerate(totals.items()):
            with cols[i % 3]:
                st.markdown(f'''
                <div class="kpi-card">
                    <div class="kpi-title">{kpi}</div>
                    <div class="kpi-value">{int(total):,}</div>
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.info("🔢 لا توجد أعمدة رقمية للعرض.")

    # الرسوم البيانية
    st.markdown("### 📊 الرسوم البيانية")
    
    if len(numeric_cols) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            # رسم بياني دائري لأعلى 5 قيم
            top_5 = df[numeric_cols].sum().nlargest(5)
            if len(top_5) > 0:
                fig_pie = px.pie(
                    values=top_5.values, 
                    names=top_5.index,
                    title="توزيع أعلى 5 مؤشرات",
                    color_discrete_sequence=NEON_COLORS
                )
                fig_pie.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    textfont=dict(size=14, color="#ffffff"),
                    marker=dict(line=dict(color="#ffffff", width=2))
                )
                apply_neon_layout(fig_pie, "توزيع المؤشرات")
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # رسم بياني عمودي
            if len(numeric_cols) > 0:
                selected_col = st.selectbox("اختر المؤشر:", numeric_cols, key="bar_chart")
                fig_bar = px.bar(
                    df, 
                    x=date_col, 
                    y=selected_col,
                    title=f"تطور {selected_col}",
                    color_discrete_sequence=[NEON_COLORS[1]]
                )
                apply_neon_layout(fig_bar, f"تطور {selected_col}")
                st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("📉 تحتاج إلى عمودين رقميين على الأقل للرسوم البيانية.")

    # الجدول التفصيلي
    st.markdown("### 📋 البيانات التفصيلية")
    st.dataframe(style_dataframe(df), use_container_width=True, height=400)

# ============ الواجهة الرئيسية ============
def main():
    """الواجهة الرئيسية للتطبيق"""

    # الشريط الجانبي
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <h3>🎛️ لوحة التحكم</h3>
            <p>اختر طريقة عرض البيانات</p>
        </div>
        """, unsafe_allow_html=True)
        
        app_mode = st.radio(
            "طريقة العرض:",
            ["الرئيسية", "عرض المنشآت", "مقارنة المنشآت"],
            index=0
        )

    # المحتوى الرئيسي بناء على الاختيار
    if app_mode == "الرئيسية":
        show_main_dashboard()
        
    elif app_mode == "عرض المنشآت":
        st.markdown('<div class="section-title">🏭 عرض البيانات حسب المنشأة</div>', unsafe_allow_html=True)
        
        # تحميل قائمة المنشآت تلقائياً
        with st.spinner("جاري تحميل قائمة المنشآت..."):
            facilities = list_facility_sheets(PHC_SPREADSHEET_ID)
            
        if facilities:
            selected_facility = st.selectbox("اختر المنشأة:", facilities)
            if selected_facility:
                with st.spinner(f"جاري تحميل بيانات {selected_facility}..."):
                    df_facility = get_df_from_sheet(PHC_SPREADSHEET_ID, selected_facility)
                    display_facility_dashboard(df_facility, selected_facility)
        else:
            st.error("❌ لا توجد منشآت متاحة أو تعذر الاتصال بالبيانات")
            
    elif app_mode == "مقارنة المنشآت":
        st.markdown('<div class="section-title">⚖️ مقارنة المنشآت</div>', unsafe_allow_html=True)
        st.info("🔧 هذه الميزة قيد التطوير...")

    # التذييل
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>⏰ يتم عرض الوقت حسب توقيت القاهرة</p>
        <p>🏥 AMANY Dashboard v3.0 - منصة التحليل المتقدم للرعاية الصحية</p>
        <p style='font-size: 12px;'>© 2024 الهيئة العامة للرعاية الصحية - فرع جنوب سيناء</p>
    </div>
    """, unsafe_allow_html=True)

# تشغيل التطبيق
if __name__ == "__main__":
    main()
