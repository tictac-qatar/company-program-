import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Tic Tac for Building Maintenance", layout="wide")

st.markdown("""
    <style>
    .main-header {
        background-color: #14213d;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 4px solid #c59b27;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #c59b27;
        font-size: 28px;
        margin: 0;
    }
    .main-header p {
        color: #e5e5e5;
        margin: 5px 0 0 0;
    }
    </style>
    <div class="main-header">
        <h1>TIC TAC لصيانة المباني</h1>
        <p>نظام إدارة طلبات الصيانة، المهام، والمشتريات والحسابات</p>
    </div>
""", unsafe_allow_html=True)

# إعداد قاعدة البيانات الشاملة
def init_db():
    conn = sqlite3.connect('tictac_full.db', check_same_thread=False)
    cursor = conn.cursor()
    # جدول طلبات الصيانة والمهام
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            building_name TEXT,
            location TEXT,
            issue_desc TEXT,
            priority TEXT,
            assigned_to TEXT,
            status TEXT,
            date TEXT
        )
    ''')
    # جدول المعاملات المالية والمشتريات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# القائمة الجانبية للتسجيل (مهام أو مالية)
st.sidebar.header("لوحة الإدخال والتشغيل")
section_choice = st.sidebar.radio("اختر نوع الإدخال:", ["تسجيل طلب / مهمة صيانة", "تسجيل معاملة مالية / مشتريات"])

if section_choice == "تسجيل طلب / مهمة صيانة":
    st.sidebar.subheader("إضافة أمر صيانة جديد")
    building_name = st.sidebar.text_input("اسم المبنى / المشروع")
    location = st.sidebar.text_input("رقم الغرفة / الطابق / الموقع")
    issue_desc = st.sidebar.text_area("وصف العطل أو المطلوب تنفيذه")
    priority = st.sidebar.selectbox("الأولوية", ["عادي", "متوسط", "طوارئ قصوى"])
    assigned_to = st.sidebar.text_input("الفني المسؤول / المقاول")
    task_status = st.sidebar.selectbox("حالة الطلب", ["جديد", "قجار العمل عليه", "مكتمل"])
    task_date = st.sidebar.date_input("تاريخ الطلب", datetime.now()).strftime("%Y-%m-%d")

    if st.sidebar.button("حفظ مهمة الصيانة"):
        if building_name and issue_desc:
            cursor.execute("INSERT INTO tasks (building_name, location, issue_desc, priority, assigned_to, status, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (building_name, location, issue_desc, priority, assigned_to, task_status, task_date))
            conn.commit()
            st.sidebar.success("تم حفظ مهمة الصيانة بنجاح!")
            st.rerun()
        else:
            st.sidebar.error("الرجاء إدخال اسم المبنى ووصف الطلب على الأقل.")

else:
    st.sidebar.subheader("تسجيل معاملة مالية")
    t_type_label = st.sidebar.selectbox("نوع المعاملة", ["إيراد (عقد صيانة / خدمة)", "مصروف / مشتريات قطع غيار"])
    t_type = "revenue" if "إيراد" in t_type_label else "expense"

    category = st.sidebar.selectbox("التصنيف", [
        "عقد صيانة دورية", 
        "إصلاح طارئ", 
        "شراء قطع غيار ومواد", 
        "أجور عمالة وفنيين", 
        "مصروفات تشغيلية"
    ])

    description = st.sidebar.text_input("الوصف / اسم العميل أو المورد")
    amount = st.sidebar.number_input("المبلغ (ر.ق / ر.س)", min_value=0.0, format="%.2f")
    date_str = st.sidebar.date_input("تاريخ المعاملة", datetime.now()).strftime("%Y-%m-%d")

    if st.sidebar.button("حفظ المعاملة المالية"):
        if description and amount > 0:
            cursor.execute("INSERT INTO transactions (type, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                           (t_type, category, description, amount, date_str))
            conn.commit()
            st.sidebar.success("تم حفظ المعاملة المالية بنجاح!")
            st.rerun()
        else:
            st.sidebar.error("الرجاء إدخال الوصف والمبلغ بشكل صحيح.")

# الشاشة الرئيسية لعرض البيانات والأقسام
tab1, tab2 = st.tabs(["إدارة ومتابعة طلبات الصيانة", "التقارير المالية والمشتريات"])

with tab1:
    st.subheader("سجل طلبات وأعمال الصيانة للمباني")
    cursor.execute("SELECT id, building_name, location, issue_desc, priority, assigned_to, status, date FROM tasks ORDER BY id DESC")
    tasks_rows = cursor.fetchall()
    
    if tasks_rows:
        df_tasks = pd.DataFrame(tasks_rows, columns=["م", "المبنى", "الموقع", "الوصف", "الأولوية", "المسؤول", "الحالة", "التاريخ"])
        st.dataframe(df_tasks, use_container_width=True)
    else:
        st.info("لا توجد طلبات صيانة مسجلة حتى الآن.")

with tab2:
    st.subheader("مؤشرات وملخص الحسابات والمشتريات")
    
    cursor.execute("SELECT id, type, category, description, amount, date FROM transactions ORDER BY date DESC")
    trans_rows = cursor.fetchall()
    
    total_rev = sum([r[4] for r in trans_rows if r[1] == 'revenue'])
    total_exp = sum([r[4] for r in trans_rows if r[1] == 'expense'])
    net_profit = total_rev - total_exp

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الإيرادات", f"{total_rev:,.2f}")
    col2.metric("إجمالي المصروفات/المشتريات", f"{total_exp:,.2f}")
    col3.metric("صافي الربح", f"{net_profit:,.2f}")

    st.markdown("---")
    if trans_rows:
        df_trans = pd.DataFrame(trans_rows, columns=["م", "النوع", "التصنيف", "الوصف", "المبلغ", "التاريخ"])
        df_trans["النوع"] = df_trans["النوع"].apply(lambda x: "إيراد" if x == 'revenue' else "مصروف/شراء")
        st.dataframe(df_trans, use_container_width=True)
    else:
        st.info("لا توجد معاملات مالية مسجلة حتى الآن.")
