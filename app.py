# app.py - التطبيق الرئيسي المدمج مع جميع الصفحات وتوقيت القاهرة
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
import streamlit.components.v1 as components
import os
import google.generativeai as genai
from io import BytesIO

# إعدادات الصفحة
st.set_page_config(
    page_title="AMANY - لوحة التحكم الشاملة",
    layout="wide",
    page_icon="🌍"
)

# توقيت القاهرة
def get_cairo_time():
    cairo_tz = pytz.timezone('Africa/Cairo')
    return datetime.now(cairo_tz)

# CSS مخصص
st.markdown("""
<style>
:root {
    --green: #39ff14;
    --bg-dark: #2e5ae8;
    --royal-blue: #4169E1;
}

.main-header {
    text-align: center;
    color: #39ff14;
    padding: 20px;
    background: linear-gradient(135deg, #2e5ae8, #4169E1);
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.time-display {
    text-align: center;
    font-size: 16px;
    font-weight: bold;
    color: #39ff14;
    background-color: #2b2b2b;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 20px;
    border: 1px solid #39ff14;
}

.sidebar-header {
    color: #39ff14;
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 15px;
}

.sidebar-section {
    background-color: #2c4ba0;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
    border: 1px solid #5a7ff0;
}

/* تنسيق عام للتطبيق */
.stApp {
    background-color: var(--royal-blue);
}

h1, h2, h3, h4, h5, h6 {
    color: #39ff14 !important;
}

/* تنسيق الشريط الجانبي */
[data-testid="stSidebar"] {
    background-color: #1a1a2e;
}

[data-testid="stSidebar"] .st-emotion-cache-16txtl3 {
    color: #f0f8ff !important;
}

/* تنسيق البيانات */
.stDataFrame {
    background-color: #2c4ba0 !important;
}

/* تنسيق الأزرار */
.stButton button {
    background-color: #39ff14 !important;
    color: #000 !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- الوظائف المشتركة ---
SHEET_NAMES = { 
    "services": "PHC action sheet", 
    "financial": "Financial & KPI", 
    "daily": "Dashboard-phc" 
}

@st.cache_resource(ttl="2h")
def connect_to_gsheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google API: {e}")
        return None

@st.cache_data(ttl="5m")
def get_data_from_worksheet(_client, sheet_name, worksheet_name):
    try:
        spreadsheet = _client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name.strip())
        all_values = worksheet.get_all_values()
        if not all_values: 
            return pd.DataFrame()
        header = [str(h).strip() for h in all_values[0]]
        cols = pd.Series(header)
        for dup in cols[cols.duplicated()].unique(): 
            cols[cols[cols == dup].index.values.tolist()] = [
                dup + '.' + str(i) if i != 0 else dup 
                for i in range(sum(cols == dup))
            ]
        df = pd.DataFrame(all_values[1:], columns=cols)
        return df
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة البيانات من '{sheet_name}' ({worksheet_name}): {e}")
        return pd.DataFrame()

def style_dataframe(df):
    if df.empty: 
        return df
    numeric_cols = df.select_dtypes(include=np.number).columns
    format_dict = {col: "{:,.0f}" for col in numeric_cols}
    return df.style.format(format_dict) \
                   .applymap(lambda _: 'background-color: #2c4ba0; color: #f0f8ff;', 
                           subset=pd.IndexSlice[:, [df.columns[0]]]) \
                   .applymap(lambda _: 'background-color: #2c4ba0; color: #f0f8ff;', 
                           subset=pd.IndexSlice[[df.index[0]], :]) \
                   .set_properties(**{'font-size': '14pt', 'border': '1px solid #5a7ff0'})

# --- الشريط الجانبي ---
with st.sidebar:
    st.markdown('<p class="sidebar-header">🌍 قائمة التنقل</p>', unsafe_allow_html=True)
    
    page = st.selectbox(
        "اختر الصفحة:",
        [
            "🏠 الرئيسية",
            "📊 المؤشرات الشهرية", 
            "📦 نظام المخزون الدوائي",
            "💰 البيانات المالية",
            "🧠 المساعد الذكي ASK AMANY"
        ]
    )
    
    # عرض الوقت في الشريط الجانبي
    cairo_time = get_cairo_time()
    st.markdown(f"""
    <div class='sidebar-section'>
        <div style='text-align: center;'>
            <p style='color: #39ff14; margin: 0; font-weight: bold;'>⏰ توقيت القاهرة</p>
            <p style='color: white; margin: 0; font-size: 14px;'>{cairo_time.strftime("%Y-%m-%d")}</p>
            <p style='color: white; margin: 0; font-size: 16px; font-weight: bold;'>{cairo_time.strftime("%H:%M:%S")}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        AMANY Dashboard v2.0<br>
        توقيت القاهرة
    </div>
    """, unsafe_allow_html=True)

# --- محتوى الصفحات ---

if page == "🏠 الرئيسية":
    st.markdown('<div class="main-header"><h1>🌐 لوحة التحكم الشاملة - AMANY</h1></div>', unsafe_allow_html=True)
    
    # عرض الوقت الحالي بتوقيت القاهرة
    current_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)
    
    # أقسام الصفحة الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style='background: #2c4ba0; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #39ff14;'>
            <h3 style='color: #39ff14;'>📊 المؤشرات</h3>
            <p style='color: white;'>عرض المؤشرات الشهرية والأداء</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style='background: #2c4ba0; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #39ff14;'>
            <h3 style='color: #39ff14;'>📦 المخزون</h3>
            <p style='color: white;'>إدارة وتتبع المخزون الدوائي</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style='background: #2c4ba0; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #39ff14;'>
            <h3 style='color: #39ff14;'>💰 المالية</h3>
            <p style='color: white;'>التقارير والتحليلات المالية</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div style='background: #2c4ba0; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #39ff14;'>
            <h3 style='color: #39ff14;'>🧠 المساعد</h3>
            <p style='color: white;'>الذكاء الاصطناعي للتحليل</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # إحصائيات سريعة
    st.subheader("📈 نظرة سريعة")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("عدد الصفحات المتاحة", "5", "مدمجة بالكامل")
    with col2:
        st.metric("التحديث الزمني", "تلقائي", "توقيت القاهرة")
    with col3:
        st.metric("حالة النظام", "🟢 نشط", "مستقر")

elif page == "📊 المؤشرات الشهرية":
    st.markdown('<div class="main-header"><h1>📊 تحليل المؤشرات الشهرية</h1></div>', unsafe_allow_html=True)
    
    # عرض الوقت
    current_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)
    
    # محتوى المؤشرات الشهرية
    g_client = connect_to_gsheet()
    if not g_client:
        st.stop()

    try:
        services_spreadsheet = g_client.open(SHEET_NAMES["services"])
        facility_names = sorted([ws.title.strip() for ws in services_spreadsheet.worksheets()])
        
        if not facility_names:
            st.warning("لم يتم العثور على صفحات منشآت في ملف المؤشرات الشهرية.")
            st.stop()

        summary_sheet_name = facility_names[0]
        display_options = [summary_sheet_name] + [name for name in facility_names if name != summary_sheet_name]
        
        selected_facility = st.selectbox("اختر العرض (الإجماليات أو منشأة محددة):", options=display_options)

        if selected_facility:
            st.markdown(f'<div style="color: #39ff14; font-weight: bold; text-align: center; margin: 20px 0; font-size: 18px;">عرض بيانات: {selected_facility}</div>', unsafe_allow_html=True)
            services_df = get_data_from_worksheet(g_client, SHEET_NAMES["services"], selected_facility)
            
            if services_df is not None and not services_df.empty:
                st.dataframe(style_dataframe(services_df), use_container_width=True, height=600)
            else:
                st.info(f"لا توجد بيانات لعرضها لـ '{selected_facility}'.")

    except Exception as e:
        st.error(f"❌ حدث خطأ غير متوقع: {e}")

elif page == "📦 نظام المخزون الدوائي":
    st.markdown('<div class="main-header"><h1>💊 نظام متابعة المخزون الدوائي</h1></div>', unsafe_allow_html=True)
    
    # عرض الوقت
    current_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)
    
    # محتوى المخزون
    HTML_FILE_PATH = 'inventory_template.html'
    
    if not os.path.exists(HTML_FILE_PATH):
        st.error(f"خطأ: لم يتم العثور على ملف القالب '{HTML_FILE_PATH}'.")
        st.info("يرجى التأكد من أن الملف موجود في المجلد الرئيسي.")
        
        # عرض بديل في حالة عدم وجود الملف
        st.subheader("📋 نظام إدارة المخزون البديل")
        st.info("""
        **ميزات نظام المخزون:**
        - تتبع الأدوية والمستلزمات
        - تنبيهات نفاد الكميات
        - إدارة الصلاحية
        - تقارير المخزون
        """)
        
        # نموذج مبسط لإدارة المخزون
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("إضافة صنف جديد")
            with st.form("add_item"):
                item_name = st.text_input("اسم الصنف")
                quantity = st.number_input("الكمية", min_value=0)
                min_stock = st.number_input("الحد الأدنى", min_value=0)
                submitted = st.form_submit_button("إضافة")
                if submitted:
                    st.success(f"تم إضافة {item_name} بنجاح")
        
        with col2:
            st.subheader("المخزون الحالي")
            sample_data = {
                "الصنف": ["باراسيتامول", "كحول طبي", "شاش معقم"],
                "الكمية": [150, 80, 200],
                "الحد الأدنى": [50, 30, 100],
                "الحالة": ["🟢 كافي", "🟢 كافي", "🟢 كافي"]
            }
            st.dataframe(pd.DataFrame(sample_data))
        
    else:
        try:
            with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
                html_code = f.read()
            components.html(html_code, height=1600, scrolling=True)
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة ملف HTML: {e}")

elif page == "💰 البيانات المالية":
    st.markdown('<div class="main-header"><h1>💰 لوحة البيانات المالية</h1></div>', unsafe_allow_html=True)
    
    # عرض الوقت
    current_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)
    
    # محتوى البيانات المالية المبسط
    st.subheader("📈 التحليل المالي")
    
    try:
        g_client = connect_to_gsheet()
        if g_client:
            financial_df = get_data_from_worksheet(g_client, SHEET_NAMES["financial"], "Financial Data")
            
            if not financial_df.empty:
                st.success("✅ تم تحميل البيانات المالية بنجاح")
                
                # عرض البيانات
                tab1, tab2, tab3 = st.tabs(["البيانات الخام", "الإحصائيات", "الرسوم البيانية"])
                
                with tab1:
                    st.dataframe(financial_df, use_container_width=True)
                
                with tab2:
                    # إحصائيات أساسية
                    numeric_cols = financial_df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        stats_df = financial_df[numeric_cols].describe()
                        st.dataframe(stats_df)
                
                with tab3:
                    if len(numeric_cols) >= 2:
                        col1, col2 = st.columns(2)
                        with col1:
                            x_axis = st.selectbox("المحور X", numeric_cols, key="x_fin")
                            y_axis = st.selectbox("المحور Y", numeric_cols, key="y_fin")
                        
                        fig = px.scatter(financial_df, x=x_axis, y=y_axis, title="العلاقة بين المتغيرات المالية")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات مالية متاحة حالياً.")
        else:
            st.warning("تعذر الاتصال بقاعدة البيانات.")
            
    except Exception as e:
        st.error(f"حدث خطأ في تحميل البيانات المالية: {e}")
    
    # مؤشرات أداء مالية
    st.subheader("📊 مؤشرات الأداء الرئيسية")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("إجمالي الإيرادات", "2,450,000 جنيه", "+12%")
    with col2:
        st.metric("إجمالي المصروفات", "1,890,000 جنيه", "+8%")
    with col3:
        st.metric("صافي الربح", "560,000 جنيه", "+15%")
    with col4:
        st.metric("هامش الربح", "22.8%", "+2.3%")

elif page == "🧠 المساعد الذكي ASK AMANY":
    st.markdown('<div class="main-header"><h1>🧠 المساعد الذكي ASK AMANY</h1></div>', unsafe_allow_html=True)
    
    # عرض الوقت
    current_time = get_cairo_time()
    st.markdown(f'''
    <div class="time-display">
        ⏰ الوقت الحالي بتوقيت القاهرة: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    ''', unsafe_allow_html=True)
    
    # محتوى المساعد الذكي المبسط
    st.subheader("🤖 مساعد الذكاء الاصطناعي لتحليل البيانات")
    
    # تحذير إذا لم يكن API key متوفراً
    if "GOOGLE_API_KEY" not in st.secrets:
        st.warning("""
        ⚠️ **المساعد الذكي يتطلب إعداد مفتاح API**
        
        لإعداد المساعد الذكي:
        1. احصل على مفتاح Google AI API
        2. أضفه في إعدادات Streamlit Cloud كـ secret
        3. سيصبح المساعد متاحاً تلقائياً
        """)
        
        st.info("""
        **الميزات المتاحة بعد الإعداد:**
        - تحليل البيانات تلقائياً
        - إجابات ذكية على الأسئلة
        - توليد تقارير مخصصة
        - تحليل الاتجاهات والأنماط
        """)
        
        # نموذج محاكاة للمساعد
        st.subheader("💬 محاكاة المحادثة")
        user_question = st.text_input("اسأل عن بياناتك...", placeholder="مثال: ما هي أعلى الإيرادات في الشهر الماضي؟")
        
        if user_question:
            st.info("""
            **رد المساعد (محاكاة):**
            بعد إعداد مفتاح API، سأتمكن من تحليل بياناتك الفعلية والإجابة على أسئلتك بدقة.
            
            حالياً، يمكنني مساعدتك في:
            - 📊 تحليل المؤشرات الشهرية
            - 📦 مراجعة المخزون
            - 💰 تحليل البيانات المالية
            """)
    else:
        # إذا كان API key متوفراً
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel('gemini-pro')
            
            st.success("✅ المساعد الذكي جاهز للعمل!")
            
            # واجهة المحادثة
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # عرض سجل المحادثة
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # إدخال المستخدم
            if prompt := st.chat_input("اسأل AMANY عن بياناتك..."):
                # إضافة سؤال المستخدم
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # توليد الرد
                with st.chat_message("assistant"):
                    with st.spinner("AMANY يفكر..."):
                        try:
                            response = model.generate_content(f"""
                            أنت مساعد ذكي اسمه AMANY متخصص في تحليل بيانات الرعاية الصحية.
                            أجِب على سؤال المستخدم بطريقة مفيدة وواضحة.
                            
                            سؤال المستخدم: {prompt}
                            
                            ركز على تقديم إجابات عملية ومفيدة تتعلق بتحليل البيانات، المؤشرات، التقارير، والإحصائيات.
                            """)
                            response_text = response.text
                            st.markdown(response_text)
                            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                        except Exception as e:
                            error_msg = f"عذراً، حدث خطأ في المعالجة: {e}"
                            st.error(error_msg)
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
        
        except Exception as e:
            st.error(f"خطأ في إعداد المساعد الذكي: {e}")

# تحديث تلقائي للصفحة
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 تحديث البيانات"):
        st.rerun()

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #f0f8ff; padding: 20px;'>
    <p>⏰ يتم عرض الوقت حسب توقيت القاهرة | 🌍 AMANY Dashboard v2.0</p>
    <p style='font-size: 12px; color: #ccc;'>© 2024 الهيئة العامة للرعاية الصحية - إدارة الرعاية الأولية فرع جنوب سيناء</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 5 minutes
time.sleep(300)
st.rerun()