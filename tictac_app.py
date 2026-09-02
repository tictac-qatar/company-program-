import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Tic Tac for Building Maintenance", layout="wide")

# تخصيص التصميم، الخلفية، ووضوح الخطوط بناءً على الهوية البصرية
st.markdown("""
    <style>
    /* خلفية الصفحة العامة ووضوح الخطوط */
    .stApp {
        background-color: #f7f4ed;
        color: #0b132b;
        font-family: Tahoma, sans-serif;
    }
    
    /* الهيدر الرئيسي */
    .main-header {
        background-color: #14213d;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 5px solid #c59b27;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #c59b27;
        font-size: 28px;
        margin: 0;
        font-weight: bold;
    }
    .main-header p {
        color: #e5e5e5;
        margin: 5px 0 0 0;
        font-size: 15px;
    }
    
    /* تنسيق صندوق تسجيل الدخول */
    .login-box {
        max-width: 400px;
        margin: 50px auto;
        padding: 25px;
        background-color: #ffffff;
        border-radius: 10px;
        border-top: 5px solid #c59b27;
        border: 1px solid #e0d6c3;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* تحسين وضوح النصوص والعناوين داخل التطبيق */
    h1, h2, h3, h4, h5, h6, label, .stRadio div, .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
        color: #0b132b !important;
        font-weight: bold !important;
    }
    
    /* تنسيق الكروت والأقسام */
    .section-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0d6c3;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# بيانات الدخول الخاصة بك
USERS = {
    "Tictac.qatar": "Azoz@123"
}

# دالة التحقق من تسجيل الدخول
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("""
            <div class="login-box">
                <h2 style="color: #14213d !important;">TIC TAC</h2>
                <p style="color: #444444 !important;">نظام صيانة المباني - تسجيل الدخول</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            
            if st.button("تسجيل الدخول", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
        return False
    return True

if not check_login():
    st.stop()

# --- واجهة البرنامج بعد تسجيل الدخول ---

st.markdown("""
    <div class="main-header">
        <h1>TIC TAC لصيانة المباني</h1>
        <p>نظام إدارة طلبات الصيانة، المهام، والمشتريات والحسابات</p>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

def init_db():
    conn = sqlite3.connect('tictac_full.db', check_same_thread=False)
    cursor = conn.cursor()
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

# --- إعادة ترتيب الشاشة: خيارات الإدخال أولاً في الشاشة الرئيسية ---
st.markdown("### 📝 لوحة الإدخال والتشغيل السريع")

col_input1, col_input2 = st.columns(2)

with col_input1:
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("إضافة أمر صيانة جديد")
        building_name = st.text_input("اسم المبنى / المشروع")
        location = st.text_input("رقم الغرفة / الطابق / الموقع")
        issue_desc = st.text_area("وصف العطل أو المطلوب تنفيذه")
        priority = st.selectbox("الأولوية", ["عادي", "متوسط", "طوارئ قصوى"])
        assigned_to = st.text_input("الفني المسؤول / المقاول")
        task_status = st.selectbox("حالة الطلب", ["جديد", "قيد العمل عليه", "مكتمل"])
        task_date = st.date_input("تاريخ الطلب", datetime.now()).strftime("%Y-%m-%d")

        if st.button("حفظ مهمة الصيانة", use_container_width=True):
            if building_name and issue_desc:
                cursor.execute("INSERT INTO tasks (building_name, location, issue_desc, priority, assigned_to, status, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (building_name, location, issue_desc, priority, assigned_to, task_status, task_date))
                conn.commit()
                st.success("تم حفظ مهمة الصيانة بنجاح!")
                st.rerun()
            else:
                st.error("الرجاء إدخال اسم المبنى ووصف الطلب على الأقل.")
        st.markdown('</div>', unsafe_allow_html=True)

with col_input2:
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("تسجيل معاملة مالية / مشتريات")
        t_type_label = st.selectbox("نوع المعاملة", ["إيراد (عقد صيانة / خدمة)", "مصروف / مشتريات قطع غيار"])
        t_type = "revenue" if "إيراد" in t_type_label else "expense"

        category = st.selectbox("التصنيف", [
            "عقد صيانة دورية", 
            "إصلاح طارئ", 
            "شراء قطع غيار ومواد", 
            "أجور عمالة والفنيين", 
            "مصروفات تشغيلية"
        ])

        description = st.text_input("الوصف / اسم العميل أو المورد")
        amount = st.number_input("المبلغ (ر.ق / ر.س)", min_value=0.0, format="%.2f")
        date_str = st.date_input("تاريخ المعاملة", datetime.now()).strftime("%Y-%m-%d")

        if st.button("حفظ المعاملة المالية", use_container_width=True):
            if description and amount > 0:
                cursor.execute("INSERT INTO transactions (type, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                               (t_type, category, description, amount, date_str))
                conn.commit()
                st.success("تم حفظ المعاملة المالية بنجاح!")
                st.rerun()
            else:
                st.error("الرجاء إدخال الوصف والمبلغ بشكل صحيح.")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# --- التقارير وسجلات المتابعة في الجانب (أو بتبويبات واضحة ومفصولة) ---
st.markdown("### 📊 التقارير، السجلات، والمتابعة المالية")

tab1, tab2 = st.tabs(["سجل طلبات وأعمال الصيانة", "التقارير المالية والمشتريات"])

with tab1:
    cursor.execute("SELECT id, building_name, location, issue_desc, priority, assigned_to, status, date FROM tasks ORDER BY id DESC")
    tasks_rows = cursor.fetchall()
    
    if tasks_rows:
        df_tasks = pd.DataFrame(tasks_rows, columns=["م", "المبنى", "الموقع", "الوصف", "الأولوية", "المسؤول", "الحالة", "التاريخ"])
        st.dataframe(df_tasks, use_container_width=True)
    else:
        st.info("لا توجد طلبات صيانة مسجلة حتى الآن.")

with tab2:
    cursor.execute("SELECT id, type, category, description, amount, date FROM transactions ORDER BY date DESC")
    trans_rows = cursor.fetchall()
    
    total_rev = sum([r[4] for r in trans_rows if r[1] == 'revenue'])
    total_exp = sum([r[4] for r in trans_rows if r[1] == 'expense'])
    net_profit = total_rev - total_exp

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("إجمالي الإيرادات", f"{total_rev:,.2f}")
    col_m2.metric("إجمالي المصروفات/المشتريات", f"{total_exp:,.2f}")
    col_m3.metric("صافي الربح", f"{net_profit:,.2f}")

    st.markdown("---")
    if trans_rows:
        df_trans = pd.DataFrame(trans_rows, columns=["م", "النوع", "التصنيف", "الوصف", "المبلغ", "التاريخ"])
        df_trans["النوع"] = df_trans["النوع"].apply(lambda x: "إيراد" if x == 'revenue' else "مصروف/شراء")
        st.dataframe(df_trans, use_container_width=True)
    else:
        st.info("لا توجد معاملات مالية مسجلة حتى الآن.")
