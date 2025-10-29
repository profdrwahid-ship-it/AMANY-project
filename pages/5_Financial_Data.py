# pages/5_Financial_Data.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="AMANY - لوحة البيانات المالية", layout="wide")

# العنوان
st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <h1 style="color: #39ff14;">AMANY</h1>
    <h3 style="color: white;">AMANY – Advanced Financial Dashboard</h3>
    <p style="color: #ddd;">{}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

st.title("💡 لوحة البيانات المالية")

# الحصول على Spreadsheet ID
SPREADSHEET_ID = st.secrets.get("sheets", {}).get("spreadsheet_id", "1lELs2hhkOnFVix8HSE4iHpw8r20RXnEMXK9uzHSbT6Y")

try:
    # الاتصال بجوجل شيتس
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    # الحصول على قائمة الأوراق
    worksheets = spreadsheet.worksheets()
    sheet_names = [ws.title for ws in worksheets]
    
    st.success(f"✅ تم الاتصال بنجاح - {len(sheet_names)} ورقة متاحة")
    
    # اختيار الورقة
    sheet_name = st.selectbox("اختر الورقة:", sheet_names)
    
    if sheet_name:
        # جلب البيانات مباشرة باستخدام pandas
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # الطريقة الأولى: جلب كل البيانات كقائمة
        st.subheader("🔍 فحص البيانات الخام")
        all_data = worksheet.get_all_values()
        
        if not all_data:
            st.warning("الورقة فارغة")
            st.stop()
        
        st.write(f"عدد الصفوف: {len(all_data)}")
        st.write(f"عدد الأعمدة: {len(all_data[0])}")
        
        # عرض أول 5 صفوف
        st.write("أول 5 صفوف من البيانات:")
        for i, row in enumerate(all_data[:5]):
            st.write(f"الصف {i}: {row}")
        
        # محاولة تحويل إلى DataFrame بطرق مختلفة
        st.subheader("🔄 معالجة البيانات")
        
        # الطريقة 1: استخدام الصف الأول كعناوين
        try:
            df1 = pd.DataFrame(all_data[1:], columns=all_data[0])
            st.write("**الطريقة 1:** استخدام الصف الأول كعناوين")
            st.dataframe(df1.head())
        except Exception as e:
            st.error(f"الطريقة 1 فشلت: {e}")
        
        # الطريقة 2: بدون عناوين
        try:
            df2 = pd.DataFrame(all_data)
            st.write("**الطريقة 2:** بدون عناوين")
            st.dataframe(df2.head())
        except Exception as e:
            st.error(f"الطريقة 2 فشلت: {e}")
        
        # الطريقة 3: البحث عن صف العناوين
        try:
            # البحث عن الصف الذي يحتوي على أكبر عدد من القيم غير الفارغة
            header_row_idx = 0
            max_non_empty = 0
            
            for i, row in enumerate(all_data[:5]):
                non_empty = sum(1 for cell in row if str(cell).strip())
                if non_empty > max_non_empty:
                    max_non_empty = non_empty
                    header_row_idx = i
            
            st.write(f"✅ سيتم استخدام الصف {header_row_idx} كعناوين")
            
            # إنشاء DataFrame
            headers = [str(cell).strip() or f"Column_{i+1}" for i, cell in enumerate(all_data[header_row_idx])]
            data_rows = all_data[header_row_idx + 1:]
            
            df3 = pd.DataFrame(data_rows, columns=headers)
            
            # تنظيف البيانات الرقمية
            for col in df3.columns:
                if col.lower() not in ['date', 'month', 'year', 'period']:
                    df3[col] = pd.to_numeric(df3[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            st.write("**الطريقة 3:** مع معالجة البيانات الرقمية")
            st.dataframe(df3)
            
            # إذا كانت البيانات تحتوي على عمود تاريخ
            date_columns = [col for col in df3.columns if any(keyword in col.lower() for keyword in ['date', 'month', 'year', 'period'])]
            if date_columns:
                st.write(f"أعمدة التاريخ المحتملة: {date_columns}")
                
        except Exception as e:
            st.error(f"الطريقة 3 فشلت: {e}")
            
except Exception as e:
    st.error(f"❌ خطأ في الاتصال: {e}")
    st.info("""
    **لحل المشكلة:**
    1. تأكد من مشاركة ملف Google Sheets مع: amany-data-reader@amany-health-project.iam.gserviceaccount.com
    2. تحقق من أن الـ Spreadsheet ID صحيح
    3. تأكد من وجود بيانات في الورقة
    """)

# إضافة قسم للمساعدة
st.markdown("---")
st.subheader("🆘 المساعدة الفنية")

if st.button("فحص الإعدادات"):
    st.write("### 🔍 فحص الإعدادات الحالية:")
    st.write(f"- Spreadsheet ID: {SPREADSHEET_ID}")
    st.write(f"- Service Account: {st.secrets['gcp_service_account']['client_email']}")
    st.write("- حالة الاتصال: ✅ ناجح" if 'spreadsheet' in locals() else "❌ فاشل")

if st.button("تعليمات الاستخدام"):
    st.info("""
    **تعليمات الاستخدام:**
    
    1. **تأكد من تنسيق البيانات في Google Sheets:**
       - يجب أن تحتوي الصف الأول على عناوين الأعمدة
       - يجب أن يحتوي العمود الأول على التواريخ (بأي تنسيق)
       - البيانات الرقمية يجب أن تكون بأرقام فقط (بدون رموز مثل $, %)
    
    2. **إعدادات المشاركة:**
       - شارك الملف مع: amany-data-reader@amany-health-project.iam.gserviceaccount.com
       - صلاحية "مشاهد"
    
    3. **تنسيق التواريخ المقبول:**
       - 01/2024, 1/2024
       - Jan 2024, January 2024
       - 2024-01, 2024/01
    """)
