# pages/3_ASK_AMANY.py
import streamlit as st
import pandas as pd
import gspread
import numpy as np
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import re

# إعداد الصفحة
st.set_page_config(
    page_title="ASK AMANY - المساعد الذكي",
    page_icon="🤖",
    layout="wide"
)

# تهيئة حالة الجلسة
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'data_dict' not in st.session_state:
    st.session_state.data_dict = {}
if 'current_df' not in st.session_state:
    st.session_state.current_df = None
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = None

# تنسيق الصفحة
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .assistant-message {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-right: 5px solid #667eea;
        margin: 10px 0;
    }
    .user-message {
        background: #e6f7ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1890ff;
        margin: 10px 0;
    }
    .analysis-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
        border-left: 4px solid #52c41a;
    }
    .warning-card {
        background: #fffbe6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #faad14;
        margin: 10px 0;
    }
    .success-card {
        background: #f6ffed;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #52c41a;
        margin: 10px 0;
    }
    .data-card {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1890ff;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.markdown("""
<div class="main-header">
    <h1>🤖 ASK AMANY - المساعد الذكي للتحليل المالي</h1>
    <p>مساعد ذكي متقدم لتحليل البيانات المالية وتوليد التقارير الذكية</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# دوال المساعد الذكي
# ---------------------------

class FinancialAnalyst:
    def __init__(self):
        self.analysis_types = {
            'تقرير احصائي': self.generate_statistical_report,
            'مقال تحليلي': self.generate_analytical_article,
            'مقارنة بين الأعمدة': self.generate_comparison_analysis,
            'تحليل الاتجاهات': self.generate_trend_analysis,
            'توقع مبسط': self.generate_simple_forecast,
            'تحليل الأداء': self.generate_performance_analysis
        }
    
    def detect_data_frequency(self, df):
        """اكتشاف تواتر البيانات (يومي، شهري، سنوي)"""
        date_columns = ['date', 'تاريخ', 'month', 'شهر', 'year', 'سنة']
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in date_columns):
                try:
                    dates = pd.to_datetime(df[col], errors='coerce')
                    valid_dates = dates.dropna()
                    if len(valid_dates) > 1:
                        date_diff = (valid_dates.max() - valid_dates.min()).days
                        num_periods = len(valid_dates)
                        avg_days_between = date_diff / num_periods
                        
                        if avg_days_between <= 7:
                            return "يومي"
                        elif avg_days_between <= 35:
                            return "شهري"
                        else:
                            return "سنوي"
                except:
                    pass
        return "غير محدد"
    
    def detect_organization_type(self, sheet_name, columns):
        """اكتشاف نوع المنشأة بناءً على اسم الورقة والأعمدة"""
        sheet_lower = sheet_name.lower()
        columns_lower = [str(col).lower() for col in columns]
        
        # تحليل اسم الورقة والأعمدة
        healthcare_indicators = ['مستشفى', 'عيادة', 'مريض', 'طبيب', 'علاج', 'health', 'hospital', 'clinic', 'medical']
        retail_indicators = ['مبيعات', 'منتج', 'عميل', 'متجر', 'sales', 'product', 'customer', 'revenue']
        service_indicators = ['خدمة', 'عميل', 'مشروع', 'service', 'client', 'project']
        financial_indicators = ['ميزانية', 'ربح', 'خسارة', 'مصروف', 'إيراد', 'budget', 'profit', 'loss', 'expense', 'income']
        
        if any(indicator in sheet_lower for indicator in healthcare_indicators) or \
           any(any(indicator in col for indicator in healthcare_indicators) for col in columns_lower):
            return "منشأة صحية"
        elif any(indicator in sheet_lower for indicator in retail_indicators) or \
             any(any(indicator in col for indicator in retail_indicators) for col in columns_lower):
            return "منشأة تجارية"
        elif any(indicator in sheet_lower for indicator in service_indicators) or \
             any(any(indicator in col for indicator in service_indicators) for col in columns_lower):
            return "منشأة خدمية"
        elif any(indicator in sheet_lower for indicator in financial_indicators) or \
             any(any(indicator in col for indicator in financial_indicators) for col in columns_lower):
            return "منشأة مالية"
        else:
            return "منشأة عامة"
    
    def generate_statistical_report(self, df, sheet_name, columns):
        """توليد تقرير إحصائي مفصل"""
        try:
            report = []
            report.append(f"## 📊 التقرير الإحصائي لـ {sheet_name}")
            report.append("")
            
            # معلومات أساسية
            org_type = self.detect_organization_type(sheet_name, columns)
            frequency = self.detect_data_frequency(df)
            
            report.append(f"**نوع المنشأة:** {org_type}")
            report.append(f"**تواتر البيانات:** {frequency}")
            report.append(f"**فترة البيانات:** {len(df)} سجل")
            report.append(f"**عدد المؤشرات:** {len(columns)} مؤشر")
            report.append("")
            
            # الإحصائيات الوصفية
            report.append("### 📈 الإحصائيات الوصفية")
            
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                report.append("⚠️ لا توجد أعمدة رقمية في البيانات")
                return "\n".join(report)
            
            for col in numeric_columns[:6]:  # عرض أول 6 أعمدة رقمية فقط
                if df[col].notna().sum() > 0:
                    report.append(f"#### 📋 {col}")
                    report.append(f"- **المتوسط:** {df[col].mean():,.2f}")
                    report.append(f"- **الوسيط:** {df[col].median():,.2f}")
                    report.append(f"- **الانحراف المعياري:** {df[col].std():,.2f}")
                    report.append(f"- **القيمة القصوى:** {df[col].max():,.2f}")
                    report.append(f"- **القيمة الدنيا:** {df[col].min():,.2f}")
                    report.append(f"- **مجموع القيم:** {df[col].sum():,.2f}")
                    report.append("")
            
            # مؤشرات الأداء الرئيسية
            report.append("### 🎯 مؤشرات الأداء الرئيسية (KPIs)")
            
            # البحث عن أعمدة الإيرادات والمصروفات
            revenue_cols = [col for col in numeric_columns if any(word in str(col).lower() for word in ['إيراد', 'ربح', 'دخل', 'revenue', 'income', 'sales'])]
            expense_cols = [col for col in numeric_columns if any(word in str(col).lower() for word in ['مصروف', 'تكلفة', 'خسارة', 'expense', 'cost'])]
            
            if revenue_cols and expense_cols:
                total_revenue = df[revenue_cols[0]].sum()
                total_expense = df[expense_cols[0]].sum()
                profit = total_revenue - total_expense
                profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
                
                report.append(f"**إجمالي الإيرادات:** {total_revenue:,.2f}")
                report.append(f"**إجمالي المصروفات:** {total_expense:,.2f}")
                report.append(f"**صافي الربح:** {profit:,.2f}")
                report.append(f"**هامش الربح:** {profit_margin:.1f}%")
            
            # أفضل المؤشرات أداءً
            report.append("### 🏆 أفضل المؤشرات أداءً")
            growth_rates = {}
            for col in numeric_columns:
                if len(df[col]) > 1 and df[col].iloc[0] != 0:
                    growth = ((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0] * 100)
                    growth_rates[col] = growth
            
            if growth_rates:
                top_3 = sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)[:3]
                for col, growth in top_3:
                    report.append(f"- **{col}:** {growth:+.1f}%")
            
            return "\n".join(report)
        except Exception as e:
            return f"⚠️ حدث خطأ في إنشاء التقرير: {str(e)}"
    
    def generate_analytical_article(self, df, sheet_name, columns):
        """توليد مقال تحليلي"""
        try:
            org_type = self.detect_organization_type(sheet_name, columns)
            frequency = self.detect_data_frequency(df)
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            
            article = []
            article.append(f"# 📝 التحليل الشامل لـ {sheet_name}")
            article.append("")
            article.append(f"تمثل ورقة البيانات '{sheet_name}' سجلاً {frequency} لأداء {org_type}، حيث توفر رؤى قيّمة حول المؤشرات الرئيسية للأداء خلال {len(df)} فترة زمنية.")
            article.append("")
            
            if len(numeric_columns) > 0:
                # تحليل أفضل وأسوأ الأداء
                best_performer = None
                best_growth = -float('inf')
                worst_performer = None
                worst_growth = float('inf')
                
                for col in numeric_columns:
                    if len(df[col]) > 1 and df[col].iloc[0] != 0:
                        growth = ((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0] * 100)
                        if growth > best_growth:
                            best_growth = growth
                            best_performer = col
                        if growth < worst_growth:
                            worst_growth = growth
                            worst_performer = col
                
                article.append("## 📈 الأداء البارز")
                if best_performer:
                    article.append(f"**المؤشر الأكثر نمواً:** {best_performer} بنسبة نمو مذهلة تبلغ {best_growth:.1f}%")
                if worst_performer and worst_growth < 0:
                    article.append(f"**المؤشر الأكثر تراجعاً:** {worst_performer} بنسبة تراجع {worst_growth:.1f}%")
                article.append("")
                
                # التوصيات
                article.append("## 💡 التوصيات الاستراتيجية")
                article.append("1. **تعزيز المؤشرات الإيجابية:** التركيز على دعم المؤشرات التي تظهر نمواً مستمراً وزيادة الاستثمار فيها")
                article.append("2. **معالجة نقاط الضعف:** دراسة الأسباب الكامنة وراء تراجع بعض المؤشرات ووضع خطط تحسين")
                article.append("3. **تحسين الكفاءة:** مراجعة المؤشرات ذات التقلبات الكبيرة للوصول إلى استقرار أفضل في الأداء")
                article.append("4. **التخطيط المستقبلي:** استخدام البيانات التاريخية للتنبؤ بالأداء المستقبلي ووضع أهداف واقعية")
                article.append("")
            
            article.append(f"*تم إنشاء هذا التحليل آلياً باستخدام ذكاء AMANY الاصطناعي بناءً على {len(df)} سجلاً من البيانات*")
            
            return "\n".join(article)
        except Exception as e:
            return f"⚠️ حدث خطأ في إنشاء المقال: {str(e)}"
    
    def generate_comparison_analysis(self, df, selected_columns):
        """تحليل المقارنة بين الأعمدة"""
        try:
            analysis = []
            analysis.append("## ⚖️ تحليل المقارنة بين المؤشرات")
            analysis.append("")
            
            numeric_df = df[selected_columns].select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) < 2:
                return "⚠️ يرجى اختيار عمودين رقميين على الأقل للمقارنة"
            
            # مقارنة المتوسطات
            analysis.append("### 📊 مقارنة المتوسطات")
            means = numeric_df.mean()
            for col in numeric_df.columns:
                analysis.append(f"- **{col}:** {means[col]:,.2f}")
            analysis.append("")
            
            # مقارنة النمو
            analysis.append("### 📈 مقارنة معدلات النمو")
            for col in numeric_df.columns:
                if len(numeric_df[col]) > 1 and numeric_df[col].iloc[0] != 0:
                    growth = ((numeric_df[col].iloc[-1] - numeric_df[col].iloc[0]) / numeric_df[col].iloc[0] * 100)
                    trend = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
                    analysis.append(f"- {trend} **{col}:** {growth:+.1f}%")
            analysis.append("")
            
            # التوصيات
            analysis.append("### 💡 الاستنتاجات والتوصيات")
            max_mean_col = means.idxmax()
            min_mean_col = means.idxmin()
            
            analysis.append(f"- **المؤشر الأعلى قيمة:** {max_mean_col} (متوسط: {means[max_mean_col]:,.2f})")
            analysis.append(f"- **المؤشر الأقل قيمة:** {min_mean_col} (متوسط: {means[min_mean_col]:,.2f})")
            analysis.append("- **نصيحة استراتيجية:** التركيز على تطوير المؤشرات ذات القيم المنخفضة مع الحفاظ على تميز المؤشرات المرتفعة")
            
            return "\n".join(analysis)
        except Exception as e:
            return f"⚠️ حدث خطأ في التحليل: {str(e)}"
    
    def generate_trend_analysis(self, df, columns):
        """تحليل الاتجاهات الزمنية"""
        try:
            analysis = []
            analysis.append("## 📅 تحليل الاتجاهات الزمنية")
            analysis.append("")
            
            numeric_columns = df[columns].select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return "⚠️ لا توجد أعمدة رقمية لتحليل الاتجاهات"
            
            analysis.append("### 📈 اتجاهات المؤشرات الرئيسية")
            
            for col in numeric_columns[:4]:  # تحليل أول 4 أعمدة
                if len(df[col]) > 2:
                    # حساب الاتجاه باستخدام الانحدار الخطي البسيط
                    x = np.arange(len(df[col]))
                    y = df[col].values
                    slope = np.polyfit(x, y, 1)[0]
                    
                    trend = "📈 تصاعدي" if slope > 0 else "📉 تنازلي" if slope < 0 else "➡️ مستقر"
                    trend_strength = "قوي" if abs(slope) > df[col].std() else "معتدل" if abs(slope) > df[col].std()/2 else "ضعيف"
                    
                    analysis.append(f"- **{col}:** اتجاه {trend} ({trend_strength})")
            
            analysis.append("")
            analysis.append("### 💡 تفسير النتائج")
            analysis.append("- **الاتجاه التصاعدي:** يشير إلى تحسن في الأداء over time")
            analysis.append("- **الاتجاه التنازلي:** قد يدل على حاجة للتدخل لتحسين الأداء")
            analysis.append("- **الاتجاه المستقر:** يعكس استقراراً في الأداء")
            
            return "\n".join(analysis)
        except Exception as e:
            return f"⚠️ حدث خطأ في تحليل الاتجاهات: {str(e)}"
    
    def generate_simple_forecast(self, df, column):
        """توقع مبسط للقيم المستقبلية"""
        try:
            if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
                return "⚠️ يرجى اختيار عمود رقمي صالح"
            
            analysis = []
            analysis.append(f"## 🔮 توقع مبسط للمؤشر: {column}")
            analysis.append("")
            
            values = df[column].dropna()
            if len(values) < 3:
                return "⚠️ لا توجد بيانات كافية للتوقع (يحتاج إلى 3 قيم على الأقل)"
            
            # توقع بسيط باستخدام المتوسط المتحرك
            last_value = values.iloc[-1]
            avg_growth = values.pct_change().mean()
            
            if pd.notna(avg_growth) and not np.isinf(avg_growth):
                forecast_1 = last_value * (1 + avg_growth)
                forecast_3 = last_value * (1 + avg_growth) ** 3
                
                analysis.append(f"**📊 تحليل السلسلة الزمنية:**")
                analysis.append(f"- القيمة الأخيرة: {last_value:,.2f}")
                analysis.append(f"- معدل النمو المتوسط: {avg_growth:+.2%}")
                analysis.append(f"- عدد الفترات: {len(values)}")
                analysis.append("")
                
                analysis.append(f"**🔮 التوقعات:**")
                analysis.append(f"- الفترة القادمة: {forecast_1:,.2f}")
                analysis.append(f"- بعد 3 فترات: {forecast_3:,.2f}")
                analysis.append("")
                
                analysis.append("💡 *ملاحظة: هذا توقع مبسط ويعتمد على افتراض استمرار النمط الحالي*")
                analysis.append("⚠️ *التحذير: التوقعات قد تختلف بناءً على عوامل خارجية*")
            else:
                analysis.append("⚠️ لا يمكن حساب التوقع بسبب عدم وجود نمط نمو واضح")
            
            return "\n".join(analysis)
        except Exception as e:
            return f"⚠️ حدث خطأ في التوقع: {str(e)}"
    
    def generate_performance_analysis(self, df, columns):
        """تحليل مؤشرات الأداء"""
        try:
            analysis = []
            analysis.append("## 🎯 تحليل مؤشرات الأداء")
            analysis.append("")
            
            numeric_columns = df[columns].select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return "⚠️ لا توجد أعمدة رقمية لتحليل الأداء"
            
            analysis.append("### 📊 تقييم الأداء الحالي")
            
            for col in numeric_columns[:5]:
                values = df[col].dropna()
                if len(values) > 1:
                    current = values.iloc[-1]
                    previous = values.iloc[-2] if len(values) > 1 else values.iloc[0]
                    change = ((current - previous) / previous * 100) if previous != 0 else 0
                    
                    status = "🟢 تحسن كبير" if change > 10 else "🟡 تحسن طفيف" if change > 0 else "🔴 تراجع طفيف" if change > -10 else "🔻 تراجع كبير"
                    analysis.append(f"- **{col}:** {current:,.2f} ({status} {change:+.1f}%)")
            
            analysis.append("")
            analysis.append("### 🏆 التصنيف حسب الأداء")
            
            # تصنيف المؤشرات حسب متوسط القيم
            means = df[numeric_columns].mean()
            top_3 = means.nlargest(3)
            
            analysis.append("**أعلى 3 مؤشرات أداء:**")
            for col, value in top_3.items():
                analysis.append(f"- {col}: {value:,.2f}")
            
            return "\n".join(analysis)
        except Exception as e:
            return f"⚠️ حدث خطأ في تحليل الأداء: {str(e)}"

# ---------------------------
# دوال الاتصال بجوجل شيتس
# ---------------------------

@st.cache_resource
def get_google_sheets_client():
    """الاتصال بجوجل شيتس"""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

@st.cache_data
def get_spreadsheet_data(_client, spreadsheet_id):
    """جلب بيانات السبريدشيت مع معالجة العناوين المكررة"""
    try:
        spreadsheet = _client.open_by_key(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        data_dict = {}
        
        for ws in worksheets:
            try:
                # طريقة بديلة بدون استخدام get_all_records
                all_data = ws.get_all_values()
                
                if len(all_data) > 0:
                    # معالجة العناوين المكررة
                    headers = all_data[0]
                    unique_headers = []
                    header_count = {}
                    
                    for header in headers:
                        header_str = str(header).strip() or "Column"
                        if header_str in header_count:
                            header_count[header_str] += 1
                            unique_headers.append(f"{header_str}_{header_count[header_str]}")
                        else:
                            header_count[header_str] = 1
                            unique_headers.append(header_str)
                    
                    # إنشاء DataFrame يدوياً
                    if len(all_data) > 1:
                        data_rows = all_data[1:]
                        df = pd.DataFrame(data_rows, columns=unique_headers)
                        # تنظيف البيانات الرقمية
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
                        data_dict[ws.title] = df
                    else:
                        data_dict[ws.title] = pd.DataFrame(columns=unique_headers)
                        
            except Exception as e:
                st.warning(f"تحذير في ورقة {ws.title}: {e}")
                continue
                
        return data_dict
        
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return {}

# ---------------------------
# واجهة المستخدم
# ---------------------------

def main():
    # المساعد الذكي
    analyst = FinancialAnalyst()
    
    # قسم الإدخال
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔗 إعدادات البيانات")
        spreadsheet_id = st.text_input(
            "معرف ملف Google Sheets:",
            value="1lELs2hhkOnFVix8HSE4iHpw8r20RXnEMXK9uzHSbT6Y",
            help="أدخل الـ Spreadsheet ID الخاص بملفك"
        )
    
    with col2:
        st.subheader("⚡ الإجراءات")
        load_data = st.button("🔄 تحميل البيانات", type="primary", key="load_data")
    
    # تحميل البيانات
    if load_data and spreadsheet_id:
        with st.spinner("جاري تحميل البيانات..."):
            client = get_google_sheets_client()
            if client:
                data_dict = get_spreadsheet_data(client, spreadsheet_id)
                
                if data_dict:
                    st.session_state.data_loaded = True
                    st.session_state.data_dict = data_dict
                    st.success(f"✅ تم تحميل {len(data_dict)} ورقة بنجاح")
                else:
                    st.error("❌ لم يتم العثور على بيانات في الملف")
    
    # عرض البيانات إذا كانت محملة
    if st.session_state.data_loaded and st.session_state.data_dict:
        st.markdown("---")
        st.subheader("📊 البيانات المحملة")
        
        # عرض الأوراق المتاحة
        sheets_list = list(st.session_state.data_dict.keys())
        selected_sheet = st.selectbox("📄 اختر الورقة للتحليل:", sheets_list, key="sheet_selector")
        
        if selected_sheet:
            df = st.session_state.data_dict[selected_sheet]
            st.session_state.current_df = df
            st.session_state.current_sheet = selected_sheet
            
            st.markdown(f'<div class="data-card">'
                       f'📋 **الورقة:** {selected_sheet} | '
                       f'📊 **الأبعاد:** {len(df)} صف × {len(df.columns)} عمود | '
                       f'🔢 **الأعمدة الرقمية:** {len(df.select_dtypes(include=[np.number]).columns)}'
                       f'</div>', unsafe_allow_html=True)
            
            # عرض عينة من البيانات
            with st.expander("👀 معاينة البيانات", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # قسم التحليل
            st.markdown("---")
            st.subheader("🤖 تحليل AMANY الذكي")
            
            # نوع التحليل
            analysis_type = st.selectbox(
                "اختر نوع التحليل:",
                list(analyst.analysis_types.keys()),
                key="analysis_type"
            )
            
            # اختيار الأعمدة إذا لزم الأمر
            available_columns = df.columns.tolist()
            
            if analysis_type in ['مقارنة بين الأعمدة', 'تحليل الاتجاهات', 'تحليل الأداء']:
                selected_columns = st.multiselect(
                    "اختر الأعمدة للتحليل:",
                    available_columns,
                    default=available_columns[:min(3, len(available_columns))],
                    key="column_selector"
                )
            elif analysis_type == 'توقع مبسط':
                selected_column = st.selectbox("اختر العمود للتوقع:", available_columns, key="forecast_column")
            else:
                selected_columns = available_columns
            
            # زر التنفيذ
            if st.button("🚀 تنفيذ التحليل", type="primary", key="run_analysis"):
                with st.spinner("جاري التحليل... قد يستغرق بضع ثوانٍ"):
                    try:
                        if analysis_type == 'توقع مبسط':
                            result = analyst.generate_simple_forecast(df, selected_column)
                        elif analysis_type in ['مقارنة بين الأعمدة', 'تحليل الاتجاهات', 'تحليل الأداء']:
                            result = analyst.analysis_types[analysis_type](df, selected_columns)
                        else:
                            result = analyst.analysis_types[analysis_type](df, selected_sheet, available_columns)
                        
                        # عرض النتيجة
                        st.markdown("---")
                        st.markdown("### 📋 نتيجة التحليل")
                        st.markdown(f'<div class="analysis-card">{result}</div>', unsafe_allow_html=True)
                        
                        # خيارات التصدير
                        st.download_button(
                            "📥 تحميل التقرير كـ نص",
                            result,
                            file_name=f"تحليل_{selected_sheet}_{analysis_type}.txt",
                            mime="text/plain",
                            key="download_report"
                        )
                        
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء التحليل: {str(e)}")
        
        # قسم الأسئلة الذكية
        st.markdown("---")
        st.subheader("💬 أسئلة ذكية فورية")
        
        col_q1, col_q2, col_q3 = st.columns(3)
        
        with col_q1:
            if st.button("📈 أفضل مؤشر أداء", key="best_kpi"):
                if st.session_state.current_df is not None:
                    with st.spinner("جاري التحليل..."):
                        result = analyst.generate_performance_analysis(st.session_state.current_df, st.session_state.current_df.columns)
                        st.markdown(f'<div class="analysis-card">{result}</div>', unsafe_allow_html=True)
        
        with col_q2:
            if st.button("🔄 تحليل الاتجاهات", key="trend_analysis"):
                if st.session_state.current_df is not None:
                    with st.spinner("جاري التحليل..."):
                        result = analyst.generate_trend_analysis(st.session_state.current_df, st.session_state.current_df.columns)
                        st.markdown(f'<div class="analysis-card">{result}</div>', unsafe_allow_html=True)
        
        with col_q3:
            if st.button("🎯 تقرير إحصائي", key="stat_report"):
                if st.session_state.current_df is not None:
                    with st.spinner("جاري التحليل..."):
                        result = analyst.generate_statistical_report(
                            st.session_state.current_df, 
                            st.session_state.current_sheet, 
                            st.session_state.current_df.columns
                        )
                        st.markdown(f'<div class="analysis-card">{result}</div>', unsafe_allow_html=True)
    
    else:
        st.info("👆 يرجى تحميل البيانات أولاً باستخدام الزر أعلاه")

if __name__ == "__main__":
    main()
