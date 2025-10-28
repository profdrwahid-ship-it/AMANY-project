# 📄 pages/2_ASK_AMANY.py (النسخة النهائية والمستقلة)

import streamlit as st
import pandas as pd
import os
import google.generativeai as genai

# --- إعدادات الصفحة ---
st.set_page_config(page_title="AMANY - المساعد الذكي", layout="wide", page_icon="🧠")

# --- استايل CSS ---
st.markdown("""
    <style>
    /* ... نفس كود الـ CSS السابق ... */
    .amany-header { background: #14389f; padding: 0.7em 0; box-shadow: 0 2px 8px #c2cbe5; text-align: center; color: white; margin-bottom: 1.5rem; }
    .amany-header-title { font-size: 2.2em; font-weight: bold; background: linear-gradient(90deg,#06dc95,#36e5ff,#33d1ff 80%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 7px; margin: 0; }
    .amany-header-sub { color: #fff; font-size: 1.2em; margin-top: 0.1em; }
    .amany-abbreviation { color: #e3f6ff; font-size: 1em; font-weight: bold; letter-spacing: 2px; margin-top: 0.5em; }
    .main-title { font-size: 1.35em; font-weight: bold; color: #1976d2; letter-spacing: 2px; margin-bottom: 0.3em; text-align: center;}
    .stChatMessage .stMarkdown p { font-size: 1.15rem; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# --- الهيدر ---
st.markdown("""
    <div class="amany-header">
        <div class="amany-header-title">AMANY</div>
        <div class="amany-header-sub">الهيئة العامة للرعاية الصحية - إدارة الرعاية الأولية فرع جنوب سيناء</div>
        <div class="amany-abbreviation">Advanced Medical Analytics Networking Yielding</div>
    </div>
""", unsafe_allow_html=True)

st.title("🧠 المساعد الذكي ASK AMANY")
st.write("هذه الصفحة تتيح لك طرح أسئلة مباشرة حول أي ملف بيانات ليقوم الذكاء الاصطناعي بتحليله والإجابة.")

# --- دالة لجلب الملفات من عدة مجلدات ---
@st.cache_data
def get_all_files_from_folders(folders):
    all_files = []
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
        files_in_folder = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".xlsx") and not f.startswith("~$")]
        all_files.extend(files_in_folder)
    return all_files

# --- جلب الملفات من مجلدي uploads و Center ---
FOLDERS_TO_SCAN = ["uploads", "Center"]
all_available_files = get_all_files_from_folders(FOLDERS_TO_SCAN)

if not all_available_files:
    st.error("لم يتم العثور على أي ملفات إكسل في مجلدي 'uploads' أو 'Center'.")
    st.stop()

# --- أدوات اختيار الملفات في الشريط الجانبي ---
st.sidebar.header("إعدادات التحليل للمساعد الذكي")
file_path_to_analyze = st.sidebar.selectbox("1. اختر ملفًا لتحليله:", all_available_files, key="ai_file_selector")
sheet_to_analyze = st.sidebar.selectbox("2. اختر ورقة العمل:", pd.ExcelFile(file_path_to_analyze).sheet_names, key="ai_sheet_selector")

st.info(f"جاهز لتحليل الملف: **{os.path.basename(file_path_to_analyze)}** (ورقة: **{sheet_to_analyze}**)")
st.markdown("---")

# --- إعدادات API والنموذج ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except (KeyError, FileNotFoundError):
    st.error("لم يتم العثور على مفتاح GOOGLE_API_KEY.")
    st.stop()
except Exception as e:
    st.error(f"خطأ في إعداد نموذج Google AI: {e}")
    st.stop()

# --- منطق الدردشة ---
chat_key = f"chat_history_{file_path_to_analyze}_{sheet_to_analyze}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

@st.cache_data(ttl=3600)
def get_data_context(_file_path, _sheet):
    try:
        # قراءة الملف مع افتراض أن الصف الأول هو الهيدر (header=0)
        df_context = pd.read_excel(_file_path, sheet_name=_sheet, header=0)
        context_text = f"اسم الملف: {os.path.basename(_file_path)}\nاسم الورقة: {_sheet}\n\n{df_context.to_string()}"
        return context_text
    except Exception as e:
        return f"خطأ في قراءة الملف: {e}"

# عرض سجل المحادثة
for message in st.session_state[chat_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

# إدخال المستخدم
if prompt := st.chat_input("اسأل عن بياناتك..."):
    st.session_state[chat_key].append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("... يفكر ASK AMANY"):
            data_context = get_data_context(file_path_to_analyze, sheet_to_analyze)
            full_prompt = f"""أنت مساعد ذكي اسمه "ASK AMANY". حلل البيانات التالية وأجب عن سؤال المستخدم. البيانات: --- {data_context} --- سؤال المستخدم: "{prompt}" """
            try:
                response = model.generate_content(full_prompt)
                response_text = response.text
                st.markdown(response_text)
                st.session_state[chat_key].append({"role": "assistant", "text": response_text})
            except Exception as e:
                st.error(f"خطأ في التواصل مع الـ API: {e}")
