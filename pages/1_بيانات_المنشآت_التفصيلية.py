import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px

# --- إعدادات الصفحة ---
st.set_page_config(page_title="AMANY - دليل المنشآت", layout="wide", page_icon="🏥")

# --- استايل CSS ---
st.markdown("""
    <style>
    /* --- General & Original Styles --- */
    .amany-header { background: #14389f; padding: 0.7em 0; box-shadow: 0 2px 8px #c2cbe5; text-align: center; color: white; margin-bottom: 1.5rem; }
    .amany-header-title { font-size: 2.2em; font-weight: bold; background: linear-gradient(90deg,#06dc95,#36e5ff,#33d1ff 80%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 7px; margin: 0; }
    .amany-header-sub { color: #fff; font-size: 1.2em; margin-top: 0.1em; }
    .main-title { font-size: 1.35em; font-weight: bold; color: #1976d2; letter-spacing: 2px; margin-bottom: 0.3em; text-align: center;}
    .info-card { background-color: #ffffff; border-radius: 15px; padding: 20px; margin: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; text-align: center; }
    .info-card h3 { color: #14389f; margin-bottom: 15px; font-size: 1.2em; }
    .info-card p { color: #333; font-size: 1.5em; font-weight: bold; margin: 5px 0; }
    .kpi-card { border-radius: 15px; background: #fff; padding: 1.1em 0.7em 0.7em 0.7em; margin-bottom: 1.1em; box-shadow: 0 3px 15px #e6eaf1; text-align: center; min-height: 115px; border: 1px solid #d2e2f3; }
    .kpi-title { color: #1976d2; font-size: 1.04em; font-weight: 700; margin-bottom: 0.19em; letter-spacing: 1px; }
    .kpi-value { color: #07e672; font-size: 2em; font-weight: bold; margin-bottom: 0.09em; }
    .year-badge { background: #14389f; color: white; padding: 0.2em 0.5em; border-radius: 10px; font-size: 0.8em; margin-left: 0.5em; }
    
    /* --- Financial Analysis Dark Theme --- */
    .financial-section { background-color: #0D1117; color: #c9d1d9; padding: 2rem; border-radius: 15px; border: 1px solid #30363d; }
    .financial-title { font-size: 2em; font-weight: bold; color: #58a6ff; text-align: center; margin-bottom: 1.5rem; letter-spacing: 1px; }
    .financial-sub-title { font-size: 1.4em; font-weight: 600; color: #8b949e; text-align: center; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
    .kpi-card-financial { background: #161b22; color: #e2e8f0; border-radius: 10px; padding: 1.2em; margin-bottom: 1.1em; text-align: center; border: 1px solid #30363d; transition: all 0.3s ease-in-out; min-height: 150px; display: flex; flex-direction: column; justify-content: center; }
    .kpi-card-financial:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5); }
    .kpi-title-financial { color: #8b949e; font-size: 1em; font-weight: 700; margin-bottom: 0.7em; height: 40px; }
    .kpi-values-container { display: flex; justify-content: space-around; align-items: center; margin-top: 0.5em; }
    .kpi-value-financial { color: #f0f6fc; font-size: 1.5em; font-weight: bold; }
    .year-badge-financial { background: #21262d; color: #8b949e; padding: 0.3em 0.6em; border-radius: 10px; font-size: 0.7em; display: block; margin-top: 5px; }
    .kpi-trend { font-size: 2em; font-weight: bold; margin: 0 10px; }
    .trend-up { color: #238636; }
    .trend-down { color: #da3633; }
    </style>
""", unsafe_allow_html=True)

# --- الهيدر ---
st.markdown("""
    <div class="amany-header">
        <div class="amany-header-title">AMANY</div>
        <div class="amany-header-sub">الهيئة العامة للرعاية الصحية - إدارة الرعاية الأولية فرع جنوب سيناء</div>
    </div>
""", unsafe_allow_html=True)

st.title("دليل وبيانات المنشآت 🏥")

# --- الجزء الأول: دليل المنشآت التفاعلي ---
st.markdown("---")
st.markdown("<p class=\"main-title\">دليل معلومات المنشآت</p>", unsafe_allow_html=True)

FACILITIES_DATA_FILE = os.path.join("uploads", "facilities_data.xlsx")

if not os.path.exists(FACILITIES_DATA_FILE):
    st.warning("لم يتم العثور على ملف 'facilities_data.xlsx' في مجلد 'uploads'. يرجى إضافته لعرض دليل المنشآت.")
else:
    try:
        df_facilities = pd.read_excel(FACILITIES_DATA_FILE)
        
        facility_col = next((col for col in df_facilities.columns if "منشأة" in str(col)), None)
        manager_col = next((col for col in df_facilities.columns if "مدير" in str(col) or "اسم" in str(col)), None)
        phone_col = next((col for col in df_facilities.columns if "تليفون" in str(col) or "هاتف" in str(col)), None)
        type_col = next((col for col in df_facilities.columns if "نوع" in str(col)), None)
        
        if facility_col and manager_col and phone_col:
            facility_names = df_facilities[facility_col].dropna().tolist()
            selected_facility_name = st.selectbox("اختر منشأة لعرض بياناتها:", facility_names)

            if selected_facility_name:
                facility_info = df_facilities[df_facilities[facility_col] == selected_facility_name].iloc[0]
                manager_name = facility_info[manager_col]
                phone_number = str(facility_info[phone_col])
                if not phone_number.startswith("0"):
                    phone_number = "0" + phone_number

                cols = st.columns(3) if type_col else st.columns(2)
                with cols[0]:
                    st.markdown(f"""<div class="info-card"><h3>اسم مدير المنشأة</h3><p>👨‍⚕️ {manager_name}</p></div>""", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"""<div class="info-card"><h3>رقم التليفون</h3><p>📞 {phone_number}</p></div>""", unsafe_allow_html=True)
                if type_col:
                    with cols[2]:
                        st.markdown(f"""<div class="info-card"><h3>نوع المنشأة</h3><p>🏢 {facility_info[type_col]}</p></div>""", unsafe_allow_html=True)

                # --- بداية قسم تحليل بيانات الرويسات ---
                if "الرويسات" in selected_facility_name:
                    st.markdown("---")
                    st.subheader("تحليلات مركز طب أسرة الرويسات")

                    if 'view' not in st.session_state:
                        st.session_state.view = 'operational'

                    button_cols = st.columns(2)
                    if button_cols[0].button("📊 عرض مؤشرات الأداء التشغيلية"):
                        st.session_state.view = 'operational'
                    if button_cols[1].button("📈 عرض التحليل المالي المتقدم"):
                        st.session_state.view = 'financial'
                    
                    # --- عرض المؤشرات التشغيلية ---
                    if st.session_state.view == 'operational':
                        OPERATIONAL_FILE = os.path.join("Center", "dashboard ruwaisat.xlsx")
                        if os.path.exists(OPERATIONAL_FILE):
                            st.info("يتم الآن عرض مؤشرات الأداء التشغيلية من ملف `dashboard ruwaisat.xlsx`.")
                            
                            excel_file_op = pd.ExcelFile(OPERATIONAL_FILE)
                            sheet_options = excel_file_op.sheet_names
                            selected_sheet = st.selectbox("اختر ورقة العمل للتحليل:", sheet_options, key="op_sheet")

                            df_op_headers = pd.read_excel(excel_file_op, sheet_name=selected_sheet, header=None, nrows=2)
                            headers_op = [f"{h1} {h2}".strip().replace('nan', '') for h1, h2 in zip(df_op_headers.iloc[0].fillna(''), df_op_headers.iloc[1].fillna(''))]
                            df_op = pd.read_excel(excel_file_op, sheet_name=selected_sheet, header=None, skiprows=2)
                            df_op.columns = headers_op

                            numeric_indices_op = []
                            for i, col in enumerate(df_op.columns):
                                if i > 0:
                                    try:
                                        df_op[col] = pd.to_numeric(df_op[col], errors='coerce')
                                        numeric_indices_op.append(i)
                                    except (ValueError, TypeError):
                                        continue
                            
                            st.markdown("### 📈 مؤشرات الأداء الرئيسية السنوية")
                            for i in range(0, len(numeric_indices_op), 4):
                                kpi_cols_row = st.columns(4)
                                for j, idx in enumerate(numeric_indices_op[i:i+4]):
                                    with kpi_cols_row[j]:
                                        val_2023 = df_op.iloc[11, idx] # الصف 14
                                        val_2024 = df_op.iloc[24, idx] # الصف 27
                                        st.markdown(f"""
                                            <div class="kpi-card">
                                                <div class="kpi-title">{headers_op[idx]}</div>
                                                <div class="kpi-value">{val_2023:,.0f}<span class="year-badge">2023</span></div>
                                                <div class="kpi-value">{val_2024:,.0f}<span class="year-badge">2024</span></div>
                                            </div>
                                        """, unsafe_allow_html=True)

                            st.markdown("### 📊 الرسوم البيانية وتحليلات 2025")
                            
                            df_2025 = df_op.iloc[25:37].copy() 
                            df_2025.reset_index(drop=True, inplace=True)
                            months_2025 = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

                            def get_op_chart_layout(title_text):
                                return {
                                    'plot_bgcolor': '#00008B', 
                                    'paper_bgcolor': '#00008B',
                                    'title': {'text': title_text, 'font': {'color': '#FFD700', 'size': 26}, 'x': 0.5},
                                    'xaxis': {'gridcolor': '#444488', 'linecolor': '#FFD700', 'title_font': {'color': '#FFD700', 'size': 20}, 'tickfont': {'color': '#FFD700', 'size': 18}},
                                    'yaxis': {'gridcolor': '#444488', 'linecolor': '#FFD700', 'title_font': {'color': '#FFD700', 'size': 20}, 'tickfont': {'color': '#FFD700', 'size': 18}, 'tickformat': ',.0f'},
                                    'legend': {'font': {'color': '#FFD700', 'size': 18}},
                                    'hovermode': 'x unified'
                                }

                            def create_op_chart(col_indices, title, chart_type='line'):
                                fig = go.Figure()
                                colors = ['#39FF14', '#FFD700', '#FF00FF', '#00FFFF', '#FFA500', '#DA70D6', '#7FFF00'] 
                                for i, idx in enumerate(col_indices):
                                    col_name = headers_op[idx]
                                    y_data = df_2025.iloc[:, idx].dropna()
                                    x_data = months_2025[:len(y_data)]
                                    
                                    if chart_type == 'line':
                                        fig.add_trace(go.Scatter(x=x_data, y=y_data, name=col_name, mode='lines+markers', line=dict(color=colors[i % len(colors)], width=3), marker=dict(size=8)))
                                    elif chart_type == 'bar':
                                         fig.add_trace(go.Bar(x=x_data, y=y_data, name=col_name, marker_color=colors[i % len(colors)]))
                                fig.update_layout(**get_op_chart_layout(title))
                                st.plotly_chart(fig, use_container_width=True)

                            if "الخدمات المدفوعة" in selected_sheet:
                                create_op_chart([1, 2, 10, 11, 12, 13, 14], "تردد الخدمات") 
                                create_op_chart([17, 16, 15], "الصيدلية", chart_type='bar') 
                                create_op_chart([14, 17], "مقارنة بين التردد والصيدلية") 
                                create_op_chart([20, 19, 18], "المعمل", chart_type='bar') 
                                create_op_chart([23, 22, 21], "الأشعة") 
                                create_op_chart([24, 14], "مقارنة بين إجمالي الخدمات والتردد", chart_type='bar') 
                            else: 
                                st.info(f"عرض جميع المؤشرات الرقمية لورقة '{selected_sheet}'")
                                for idx in numeric_indices_op:
                                    create_op_chart([idx], f"تحليل مؤشر: {headers_op[idx]}")

                        else:
                            st.error("ملف `dashboard ruwaisat.xlsx` غير موجود في مجلد `Center`.")

                    # --- عرض التحليل المالي ---
                    if st.session_state.view == 'financial':
                        FINANCIAL_FILE = os.path.join("Center", "financial and KPIs.xlsx")
                        if not os.path.exists(FINANCIAL_FILE):
                            st.error("ملف `financial and KPIs.xlsx` غير موجود في مجلد `Center`.")
                        else:
                            try:
                                st.markdown('<div class="financial-section">', unsafe_allow_html=True)
                                st.markdown('<p class="financial-title">التحليل المالي وأداء المؤشرات</p>', unsafe_allow_html=True)

                                df_headers = pd.read_excel(FINANCIAL_FILE, header=None, nrows=2)
                                headers = [f"{h1} {h2}".strip().replace('nan', '') for h1, h2 in zip(df_headers.iloc[0].fillna(''), df_headers.iloc[1].fillna(''))]
                                df_full = pd.read_excel(FINANCIAL_FILE, header=None, skiprows=2)
                                df_full.columns = headers
                                
                                percent_cols = [h for h in headers if '%' in h]
                                for col in df_full.columns:
                                    if col != headers[0]:
                                        df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
                                        if col in percent_cols:
                                            df_full[col] = df_full[col] * 100
                                
                                MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

                                def get_stock_chart_layout(title_text, y_title):
                                    return go.Layout(title={'text': title_text, 'y':0.9, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'color': '#c9d1d9', 'size': 18}}, plot_bgcolor='#161b22', paper_bgcolor='#161b22', xaxis=dict(gridcolor='#30363d', tickfont=dict(color='#8b949e')), yaxis=dict(title=y_title, gridcolor='#30363d', tickfont=dict(color='#8b949e'), tickformat=',.1f'), legend=dict(font=dict(color='#c9d1d9')), hovermode='x unified')

                                st.markdown('<p class="financial-sub-title">مقارنة أداء المؤشرات الرئيسية (2024 مقابل 2025)</p>', unsafe_allow_html=True)
                                kpi_cols = st.columns(4)
                                financial_kpi_indices = range(13, 25) 
                                
                                for i, col_idx in enumerate(financial_kpi_indices):
                                    with kpi_cols[i % 4]:
                                        kpi_title = headers[col_idx]
                                        val_2024 = df_full.iloc[12, col_idx] 
                                        val_2025 = df_full.iloc[19, col_idx] 
                                        is_percent = '%' in kpi_title
                                        format_2024 = f"{val_2024:,.1f}%" if is_percent and pd.notna(val_2024) else f"{val_2024:,.1f}"
                                        format_2025 = f"{val_2025:,.1f}%" if is_percent and pd.notna(val_2025) else f"{val_2025:,.1f}"
                                        trend_arrow, trend_class = ("▲", "trend-up") if val_2025 > val_2024 else (("▼", "trend-down") if val_2025 < val_2024 else ("-", ""))
                                        st.markdown(f"""
                                            <div class="kpi-card-financial">
                                                <div class="kpi-title-financial">{kpi_title}</div>
                                                <div class="kpi-values-container">
                                                    <div><div class="kpi-value-financial">{format_2024}</div><span class="year-badge-financial">2024</span></div>
                                                    <div class="kpi-trend {trend_class}">{trend_arrow}</div>
                                                    <div><div class="kpi-value-financial">{format_2025}</div><span class="year-badge-financial">2025</span></div>
                                                </div>
                                            </div>""", unsafe_allow_html=True)

                                st.markdown('<p class="financial-sub-title">تحليل الإيرادات والمصروفات</p>', unsafe_allow_html=True)
                                fig_rev_exp = go.Figure()
                                fig_rev_exp.add_trace(go.Scatter(x=MONTHS_AR, y=df_full.iloc[0:12, 9], name='إجمالي الإيرادات 2024', line=dict(color='#238636', width=2))) 
                                fig_rev_exp.add_trace(go.Scatter(x=MONTHS_AR, y=df_full.iloc[0:12, 12], name='إجمالي المصروفات 2024', line=dict(color='#da3633', width=2))) 
                                fig_rev_exp.add_trace(go.Scatter(x=MONTHS_AR[:6], y=df_full.iloc[13:19, 9], name='إجمالي الإيرادات 2025', line=dict(color='#3fb950', width=3)))
                                fig_rev_exp.add_trace(go.Scatter(x=MONTHS_AR[:6], y=df_full.iloc[13:19, 12], name='إجمالي المصروفات 2025', line=dict(color='#f85149', width=3)))
                                fig_rev_exp.update_layout(get_stock_chart_layout("مقارنة الإيرادات والمصروفات (2024-2025)", "القيمة (ج.م)"))
                                st.plotly_chart(fig_rev_exp, use_container_width=True)

                                st.markdown('<p class="financial-sub-title">تحليل المؤشرات المالية الشهرية</p>', unsafe_allow_html=True)
                                chart_col1, chart_col2 = st.columns(2)
                                with chart_col1:
                                    fig_n = go.Figure()
                                    fig_n.add_trace(go.Scatter(x=MONTHS_AR, y=df_full.iloc[0:12, 13], name='2024', line=dict(color='#58a6ff', width=2))) 
                                    fig_n.add_trace(go.Scatter(x=MONTHS_AR[:6], y=df_full.iloc[13:19, 13], name='2025', line=dict(color='#80b9ff', width=3)))
                                    fig_n.update_layout(get_stock_chart_layout(headers[13], "القيمة"))
                                    st.plotly_chart(fig_n, use_container_width=True)
                                with chart_col2:
                                    fig_pq = go.Figure()
                                    fig_pq.add_trace(go.Scatter(x=MONTHS_AR, y=df_full.iloc[0:12, 15], name=f'{headers[15]} 2024', line=dict(color='#db61ff', width=2))) 
                                    fig_pq.add_trace(go.Scatter(x=MONTHS_AR, y=df_full.iloc[0:12, 16], name=f'{headers[16]} 2024', line=dict(color='#e796ff', width=2))) 
                                    fig_pq.add_trace(go.Scatter(x=MONTHS_AR[:6], y=df_full.iloc[13:19, 15], name=f'{headers[15]} 2025', line=dict(color='#c084fc', width=3)))
                                    fig_pq.add_trace(go.Scatter(x=MONTHS_AR[:6], y=df_full.iloc[13:19, 16], name=f'{headers[16]} 2025', line=dict(color='#d8b4fe', width=3)))
                                    fig_pq.update_layout(get_stock_chart_layout(f"مقارنة: {headers[15]} و {headers[16]}", "القيمة"))
                                    st.plotly_chart(fig_pq, use_container_width=True)

                                st.markdown('<p class="financial-sub-title">تفاصيل الإيرادات والمصروفات لعام 2025</p>', unsafe_allow_html=True)
                                bar_col1, bar_col2 = st.columns(2)
                                with bar_col1:
                                    revenue_indices = range(2, 9) 
                                    df_rev_2025 = df_full.iloc[13:19, revenue_indices].copy()
                                    df_rev_2025.index = MONTHS_AR[:6]
                                    df_rev_2025.columns = headers[2:9]
                                    fig_bar_rev = px.bar(df_rev_2025, x=df_rev_2025.index, y=df_rev_2025.columns, labels={'value': 'المبلغ', 'variable': 'بند الإيراد', 'index': 'الشهر'}, color_discrete_sequence=px.colors.sequential.Greens_r)
                                    fig_bar_rev.update_layout(get_stock_chart_layout("توزيع إيرادات 2025", "المبلغ"), barmode='stack', legend_title_text='بنود الإيرادات')
                                    st.plotly_chart(fig_bar_rev, use_container_width=True)
                                with bar_col2:
                                    expense_indices = range(10, 12) 
                                    df_exp_2025 = df_full.iloc[13:19, expense_indices].copy()
                                    df_exp_2025.index = MONTHS_AR[:6]
                                    df_exp_2025.columns = headers[10:12]
                                    fig_bar_exp = px.bar(df_exp_2025, x=df_exp_2025.index, y=df_exp_2025.columns, labels={'value': 'المبلغ', 'variable': 'بند المصروف', 'index': 'الشهر'}, color_discrete_sequence=px.colors.sequential.Reds_r)
                                    # *** السطر الذي تم إصلاحه ***
                                    fig_bar_exp.update_layout(get_stock_chart_layout("توزيع مصروفات 2025", "المبلغ"), barmode='stack', legend_title_text='بنود المصروفات')
                                    st.plotly_chart(fig_bar_exp, use_container_width=True)

                                st.markdown('</div>', unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"حدث خطأ أثناء تحليل الملف المالي: {e}")
                                st.exception(e)
        else:
            st.error("لم يتم العثور على الأعمدة المطلوبة في ملف المنشآت.")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف دليل المنشآت: {e}")

# --- الجزء الأخير: عرض وتحليل ملفات البيانات الأخرى ---
st.markdown("---")
st.markdown("<p class=\"main-title\">عرض وتحليل ملفات البيانات الأخرى</p>", unsafe_allow_html=True)

def get_all_files_from_folders(folders):
    all_files = []
    for folder in folders:
        if os.path.exists(folder):
            files_in_folder = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith((".xlsx", ".xls")) and not f.startswith("~$")]
            all_files.extend(files_in_folder)
    return all_files

FOLDERS_TO_SCAN = ["uploads", "Center"]
all_available_files = get_all_files_from_folders(FOLDERS_TO_SCAN)

if not all_available_files:
    st.info("لا توجد ملفات إكسل في مجلدي 'uploads' أو 'Center' لعرضها.")
else:
    file_path_selected = st.selectbox("اختر ملف لعرضه:", all_available_files, format_func=lambda x: os.path.basename(x))
    try:
        excel_file = pd.ExcelFile(file_path_selected)
        sheet_name = st.selectbox("اختر ورقة العمل:", excel_file.sheet_names, key=f"sheet_{os.path.basename(file_path_selected)}")
        df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
        st.dataframe(df_sheet, use_container_width=True)
    except Exception as e:
        st.error(f"حدث خطأ أثناء عرض الملف: {e}")
