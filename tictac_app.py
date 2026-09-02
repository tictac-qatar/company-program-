import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# التصحيح هنا: استخدام st.set_page_config بدلاً من st.set_page_title
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
        <p>نظام الحسابات، المشتريات، وإدارة التقارير الفورية</p>
    </div>
""", unsafe_allow_html=True)

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('tictac_web.db', check_same_thread=False)
    cursor = conn.cursor()
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

# القائمة الجانبية لإدخال البيانات
st.sidebar.header("تسجيل معاملة جديدة")
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
date_str = st.sidebar.date_input("التاريخ", datetime.now()).strftime("%Y-%m-%d")

if st.sidebar.button("حفظ المعاملة"):
    if description and amount > 0:
        cursor.execute("INSERT INTO transactions (type, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                       (t_type, category, description, amount, date_str))
        conn.commit()
        st.sidebar.success("تم الحفظ بنجاح!")
        st.rerun()
    else:
        st.sidebar.error("الرجاء إدخال الوصف والمبلغ بشكل صحيح.")

# واجهة التقارير والعرض الرئيسي
st.subheader("لوحة التحكم والتقارير المالية")

report_type = st.radio("اختر نطاق التقرير:", ["عرض كافة المعاملات", "التقرير اليومي", "التقرير الأسبوعي", "التقرير الشهري", "التقرير السنوي"], horizontal=True)

today = datetime.now().date()
if report_type == "التقرير اليومي":
    query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date = ?"
    params = (today.strftime("%Y-%m-%d"),)
elif report_type == "التقرير الأسبوعي":
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
    params = (start_date, today.strftime("%Y-%m-%d"))
elif report_type == "التقرير الشهري":
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
    params = (start_date, today.strftime("%Y-%m-%d"))
elif report_type == "التقرير السنوي":
    start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
    params = (start_date, today.strftime("%Y-%m-%d"))
else:
    query = "SELECT id, type, category, description, amount, date FROM transactions ORDER BY date DESC"
    params = ()

cursor.execute(query, params)
rows = cursor.fetchall()

total_rev = sum([r[4] for r in rows if r[1] == 'revenue'])
total_exp = sum([r[4] for r in rows if r[1] == 'expense'])
net_profit = total_rev - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("إجمالي الإيرادات", f"{total_rev:,.2f}")
col2.metric("إجمالي المصروفات/المشتريات", f"{total_exp:,.2f}")
col3.metric("صافي الربح", f"{net_profit:,.2f}")

st.markdown("---")

if rows:
    df = pd.DataFrame(rows, columns=["م", "النوع", "التصنيف", "الوصف", "المبلغ", "التاريخ"])
    df["النوع"] = df["النوع"].apply(lambda x: "إيراد" if x == 'revenue' else "مصروف/شراء")
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد معاملات مسجلة ضمن النطاق المختار.")
