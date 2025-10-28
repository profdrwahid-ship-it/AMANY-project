# pages/2_📊_Monthly_Indicators.py

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

# --- إعدادات المشروع والستايل (مشتركة) ---
st.set_page_config(page_title="AMANY - المؤشرات الشهرية", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    :root { 
        --phosphor-green: #39ff14;
        --royal-blue: #4169E1;
        --dark-blue-card: #2c4ba0;
        --border-blue: #5a7ff0;
        --font-color-light: #f0f8ff;
    }
    .stApp { background-color: var(--royal-blue); }
    h1, h2, h3, h4, h5, h6 { color: var(--phosphor-green) !important; }
    p, .st-emotion-cache-16txtl3 { color: var(--font-color-light) !important; }
    .subtitle { color: var(--phosphor-green) !important; font-weight: bold; text-align: center; margin-bottom: 1em; border-bottom: 2px solid var(--border-blue); padding-bottom: 0.5em; }
    [data-testid="stSidebar"] .st-emotion-cache-10trblm, [data-testid="stSidebar"] .st-emotion-cache-16txtl3, [data-testid="stSidebar"] label { color: var(--phosphor-green) !important; }
    </style>
""", unsafe_allow_html=True)

# --- الوظائف المشتركة (منسوخة من الملف الرئيسي) ---
SHEET_NAMES = { "services": "PHC action sheet", "financial": "Financial & KPI", "daily": "Dashboard-phc" }

@st.cache_resource(ttl="2h")
def connect_to_gsheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes )
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
        if not all_values: return pd.DataFrame()
        header = [str(h).strip() for h in all_values[0]]
        cols = pd.Series(header)
        for dup in cols[cols.duplicated()].unique(): 
            cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
        df = pd.DataFrame(all_values[1:], columns=cols)
        return df
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة البيانات من '{sheet_name}' ({worksheet_name}): {e}")
        return pd.DataFrame()

def style_dataframe(df):
    if df.empty: return df
    numeric_cols = df.select_dtypes(include=np.number).columns
    format_dict = {col: "{:,.0f}" for col in numeric_cols}
    return df.style.format(format_dict) \
                   .applymap(lambda _: 'background-color: #2c4ba0; color: #f0f8ff;', subset=pd.IndexSlice[:, [df.columns[0]]]) \
                   .applymap(lambda _: 'background-color: #2c4ba0; color: #f0f8ff;', subset=pd.IndexSlice[[df.index[0]], :]) \
                   .set_properties(**{'font-size': '14pt', 'border': '1px solid #5a7ff0'})

# --- الجزء الرئيسي للصفحة ---
st.title("📊 تحليل المؤشرات الشهرية")

g_client = connect_to_gsheet()
if not g_client:
    st.stop()

try:
    services_spreadsheet = g_client.open(SHEET_NAMES["services"])
    # الحصول على كل أسماء المنشآت (كل الصفحات)
    facility_names = sorted([ws.title.strip() for ws in services_spreadsheet.worksheets()])
    
    if not facility_names:
        st.warning("لم يتم العثور على صفحات منشآت في ملف المؤشرات الشهرية.")
        st.stop()

    # إضافة خيار "الإجماليات" ليكون الافتراضي
    summary_sheet_name = facility_names[0] # نفترض أن أول صفحة هي الإجماليات
    display_options = [summary_sheet_name] + [name for name in facility_names if name != summary_sheet_name]
    
    selected_facility = st.selectbox("اختر العرض (الإجماليات أو منشأة محددة):", options=display_options)

    if selected_facility:
        st.markdown(f'<div class="subtitle">عرض بيانات: {selected_facility}</div>', unsafe_allow_html=True)
        services_df = get_data_from_worksheet(g_client, SHEET_NAMES["services"], selected_facility)
        
        if services_df is not None and not services_df.empty:
            st.dataframe(style_dataframe(services_df), use_container_width=True, height=800)
        else:
            st.info(f"لا توجد بيانات لعرضها لـ '{selected_facility}'.")

except Exception as e:
    st.error(f"❌ حدث خطأ غير متوقع: {e}")

