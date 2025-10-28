# app.py — لوحة تحليل البيانات الصحية مع توقيت القاهرة وتنسيق فوسفوري
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
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

.stApp {
    background: linear-gradient(135deg, #0b1020, #1a1f38);
}

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
}

.kpi-title {
    color: var(--neon-blue) !important;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
}

.kpi-value {
    color: var(--neon-green) !important;
    font-size: 32px;
    font-weight: 900;
}

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

h1, h2, h3, h4, h5, h6 {
    color: var(--neon-green) !important;
}

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

# ============ إصلاح مشكلة Secrets ============
def get_google_credentials():
    """الحصول على بيانات الاعتماد من Secrets بشكل آمن"""
    try:
        # الطريقة 1: إذا كان Secrets كـ JSON string
        if 'gcp_service_account' in st.secrets:
            if isinstance(st.secrets['gcp_service_account'], str):
                # إذا كان نص JSON
                return json.loads(st.secrets['gcp_service_account'])
            elif hasattr(st.secrets['gcp_service_account'], 'to_dict'):
                # إذا كان كائن Credentials
                return st.secrets['gcp_service_account']
            else:
                # إذا كان dictionary مباشر
                return dict(st.secrets['gcp_service_account'])
        
        # الطريقة 2: إذا كانت Secrets كـ sections منفصلة
        elif all(key in st.secrets for key in ['type', 'project_id', 'private_key_id']):
            credentials_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"]
            }
            return credentials_dict
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
        ws = sh.worksheet(worksheet_name.strip())
        vals = ws.get_all_values()
        
        if not vals:
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
]

# ============ تنسيق الرسوم البيانية ============
def apply_neon_layout(fig, title: str = "", height: int = 600):
    """تطبيق التنسيق الفوسفوري على الرسم البياني"""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24, color="#39ff14", family="Arial, bold"),
            x=0.5,
            xanchor="center"
        ),
        height=height,
        paper_bgcolor="#0b1020",
        plot_bgcolor="#0b1020",
        font=dict(color="#ffffff", size=14),
        legend=dict(
            font=dict(size=14, color="#ffffff"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="#39ff14",
            borderwidth=1
        ),
        xaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=16, color="#00ffff"),
            tickfont=dict(size=12, color="#ffffff"),
            linecolor="#39ff14",
        ),
        yaxis=dict(
            gridcolor="#233355",
            zerolinecolor="#39ff14",
            title_font=dict(size=16, color="#00ffff"),
            tickfont=dict(size=12, color="#ffffff"),
            linecolor="#39ff14",
        ),
        margin=dict(l=50, r=30, t=80, b=50),
    )
    return fig

# ============ الصفحة الرئيسية ============
def show_main_dashboard():
    """عرض الصفحة الرئيسية"""
    
    # الهيدر الرئيسي
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🏥 AMANY</div>
        <div class="sub-title">منصة التحليل المتقدم للرعاية الصحية الأولية</div>
        <div class="sub-title">فرع جنوب سيناء</div>
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

    # تحميل البيانات
    st.markdown('<div class="section-title">🚀 تحميل البيانات</div>', unsafe_allow_html=True)
    
    if st.button("🔄 تحميل البيانات من Google Sheets", type="primary"):
        with st.spinner("جاري تحميل البيانات..."):
            try:
                # اختبار الاتصال
                facilities = list_facility_sheets(PHC_SPREADSHEET_ID)
                
                if facilities:
                    st.success(f"✅ تم العثور على {len(facilities)} منشأة")
                    
                    # تحميل البيانات الرئيسية
                    df_main = get_df_from_sheet(PHC_SPREADSHEET_ID, "PHC Dashboard")
                    
                    if not df_main.empty:
                        st.success(f"✅ تم تحميل {len(df_main)} صف من البيانات")
                        
                        # عرض عينة من البيانات
                        st.markdown("### 📋 عينة من البيانات")
                        st.dataframe(df_main.head(), use_container_width=True)
                    else:
                        st.warning("⚠️ تم الاتصال بنجاح ولكن البيانات فارغة")
                else:
                    st.error("❌ تعذر العثور على أي منشآت")
                    
            except Exception as e:
                st.error(f"❌ خطأ في تحميل البيانات: {str(e)}")

# ============ عرض لوحة المنشأة ============
def display_facility_dashboard(df: pd.DataFrame, facility_name: str):
    """عرض لوحة البيانات للمنشأة"""
    if df.empty:
        st.info("📭 لا توجد بيانات لعرضها.")
        return

    # الهيدر
    st.markdown(f"""
    <div class="main-header">
        <div class="main-title">📊 {facility_name}</div>
        <div class="sub-title">لوحة تحليل البيانات التفصيلية</div>
    </div>
    """, unsafe_allow_html=True)

    # المؤشرات الرئيسية
    st.markdown("### 📈 المؤشرات الرئيسية")
    
    # تحويل الأعمدة الرقمية
    numeric_cols = []
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="ignore")
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
        except:
            pass
    
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
                
        # رسم بياني
        st.markdown("### 📊 الرسوم البيانية")
        col1, col2 = st.columns(2)
        
        with col1:
            if len(numeric_cols) >= 2:
                selected_col = st.selectbox("اختر المؤشر:", numeric_cols)
                fig_bar = px.bar(
                    df, 
                    x=df.index, 
                    y=selected_col,
                    title=f"توزيع {selected_col}",
                    color_discrete_sequence=[NEON_COLORS[1]]
                )
                apply_neon_layout(fig_bar, f"توزيع {selected_col}")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            if len(numeric_cols) >= 3:
                top_5 = df[numeric_cols].sum().nlargest(5)
                fig_pie = px.pie(
                    values=top_5.values, 
                    names=top_5.index,
                    title="أعلى 5 مؤشرات"
                )
                apply_neon_layout(fig_pie, "توزيع المؤشرات")
                st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("🔢 لا توجد أعمدة رقمية للعرض.")

    # الجدول التفصيلي
    st.markdown("### 📋 البيانات التفصيلية")
    st.dataframe(df, use_container_width=True, height=400)

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
            ["الرئيسية", "عرض المنشآت"],
            index=0
        )

        st.markdown("""
        <div class="sidebar-section">
            <h4>📁 التطبيقات</h4>
            <p>• ASK AMANY</p>
            <p>• Inventory</p>
            <p>• Monthly Indicators</p>
            <p>• Financial Data</p>
        </div>
        """, unsafe_allow_html=True)

    # المحتوى الرئيسي
    if app_mode == "الرئيسية":
        show_main_dashboard()
        
    elif app_mode == "عرض المنشآت":
        st.markdown('<div class="section-title">🏭 عرض البيانات حسب المنشأة</div>', unsafe_allow_html=True)
        
        facilities = list_facility_sheets(PHC_SPREADSHEET_ID)
        
        if facilities:
            selected_facility = st.selectbox("اختر المنشأة:", facilities)
            if selected_facility:
                df_facility = get_df_from_sheet(PHC_SPREADSHEET_ID, selected_facility)
                display_facility_dashboard(df_facility, selected_facility)
        else:
            st.error("❌ لا توجد منشآت متاحة")

    # التذييل
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>⏰ يتم عرض الوقت حسب توقيت القاهرة</p>
        <p>🏥 AMANY Dashboard v3.0 - منصة التحليل المتقدم للرعاية الصحية</p>
    </div>
    """, unsafe_allow_html=True)

# تشغيل التطبيق
if __name__ == "__main__":
    main()
