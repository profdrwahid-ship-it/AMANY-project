# pages/2_نظام_المخزون_الدوائي.py

import streamlit as st
import streamlit.components.v1 as components
import os

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="نظام متابعة المخزون الدوائي",
    layout="wide",
    page_icon="💊"
)

# --- عنوان مخصص للصفحة ---
st.markdown("""
    <style>
    .inventory-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    <div class="inventory-title">نظام متابعة المخزون الدوائي</div>
""", unsafe_allow_html=True)

# --- دمج كود HTML ---

# المسار إلى ملف HTML الذي وضعناه في المجلد الرئيسي
HTML_FILE_PATH = 'inventory_template.html'

# التحقق من وجود الملف لضمان عدم حدوث أخطاء
if not os.path.exists(HTML_FILE_PATH):
    st.error(f"خطأ: لم يتم العثور على ملف القالب '{HTML_FILE_PATH}'.")
    st.info("يرجى التأكد من أن الملف موجود في المجلد الرئيسي 'AMANY 1.1'.")
    st.stop()

# قراءة محتوى ملف HTML
try:
    with open(HTML_FILE_PATH, 'r', encoding='utf-8') as f:
        html_code = f.read()
except Exception as e:
    st.error(f"حدث خطأ أثناء قراءة ملف HTML: {e}")
    st.stop()

# عرض مكون HTML في تطبيق Streamlit
# تم زيادة الارتفاع لضمان ظهور الصفحة كاملة
components.html(html_code, height=1600, scrolling=True)
