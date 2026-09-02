import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Tic Tac for Building Maintenance", layout="wide")

# تنسيق عام شامل لإجبار جميع النصوص والخطوط على أن تكون واضحة وقوية
st.markdown("""
    <style>
    /* خلفية التطبيق العامة */
    .stApp {
        background-color: #f7f4ed !important;
        color: #0b132b !important;
        font-family: Tahoma, sans-serif !important;
    }
    
    /* إجبار كافة النصوص والعناوين والتسميات على أن تكون داكنة وواضحة جداً */
    h1, h2, h3, h4, h5, h6, label, p, span, div, 
    .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label, 
    .stDateInput label, .stRadio label, .stCheckbox label {
        color: #0b132b !important;
        font-weight: bold !important;
    }
    
    /* القائمة الجانبية: خلفية كحلي داكن ونصوص بيضاء ساطعة 100% للوضوح التام */
    section[data-testid="stSidebar"] {
        background-color: #14213d !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    /* حقول الإدخال داخل القائمة الجانبية */
    section[data-testid="stSidebar"] input {
        color: #0b132b !important;
        background-color: #ffffff !important;
    }
    
    /* الهيدر الرئيسي */
    .main-header {
        background-color: #14213d !important;
        color: #ffffff !important;
        padding: 22px;
        border-radius: 10px;
        border-bottom: 5px solid #c59b27;
        text-align: center;
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: #c59b27 !important;
        font-size: 28px !important;
        margin: 0 !important;
    }
    .main-header p {
        color: #ffffff !important;
        font-size: 15px !important;
    }
    
    /* صندوق تسجيل الدخول */
    .login-box {
        max-width: 420px;
        margin: 50px auto;
        padding: 30px;
        background-color: #ffffff !important;
        border-radius: 12px;
        border-top: 6px solid #c59b27;
        border: 1px solid #dcd6c9;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* كروت وحاويات الإدخال */
    .card-container {
        background-color: #ffffff !important;
        padding: 25px !important;
        border-radius: 12px !important;
        border: 1px solid #dcd6c9 !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06) !important;
        margin-bottom: 25px !important;
    }
    
    /* تحسين ألوان عناصر الإدخال والنصوص بداخله */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0b132b !important;
        border: 1px solid #b0a896 !important;
    }
    </style>
""", unsafe_allow_html=True)

# بيانات الدخول
USERS = {
    "Tictac.qatar": "Azoz@123"
}

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("""
            <div class="login-box">
                <h2 style="color: #14213d !important;">TIC TAC</h2>
                <p style="color: #333333 !important;">نظام صيانة المباني - تسجيل الدخول</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            
            if st.button("تسجيل الدخول", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
        return False
    return True

if not check_login():
    st.stop()

# قاعدة البيانات الشاملة
def init_db():
    conn = sqlite3.connect('tictac_pro.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, building TEXT, location TEXT, 
                        category TEXT, description TEXT, priority TEXT, technician TEXT, status TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS finance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, category TEXT, description TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, category TEXT, quantity INTEGER, price REAL, supplier TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, qatari_id TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, emp_name TEXT, status TEXT, date TEXT)''')
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# الهيدر
st.markdown("""
    <div class="main-header">
        <h1>TIC TAC لصيانة المباني</h1>
        <p>نظام الإدارة الشامل - التشغيل، المشتريات، الحسابات، وشؤون الموظفين</p>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

# القائمة الجانبية
st.sidebar.markdown("### 🗂️ أقسام النظام")
menu = st.sidebar.radio("اختر القسم:", [
    "🛠️ إدخال مهام الصيانة", 
    "💰 الإدخال المالي", 
    "🛒 إدخال المشتريات", 
    "👥 شؤون الموظفين (حضور وغياب)", 
    "📊 التقارير الشاملة"
])

# 1. إدخال مهام الصيانة
if menu == "🛠️ إدخال مهام الصيانة":
    st.markdown("### 🛠️ تسجيل وتفصيل مهام صيانة المباني")
    with st.container():
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            building = st.text_input("اسم المبنى / المشروع")
            location = st.text_input("رقم الغرفة / الطابق / الموقع")
            m_category = st.selectbox("تخصص الصيانة", [
                "أعمال الكهرباء والإنارة", 
                "أعمال السباكة والصرف الصحي", 
                "أنظمة التكييف والتبريد (HVAC)", 
                "الأبواب، الأقفال، والواجهات", 
                "أنظمة الإنذار ومكافحة الحريق", 
                "أعمال المدني والدهانات العامة"
            ])
            priority = st.selectbox("الأولوية", ["عادي", "متوسط", "طوارئ قصوى"])
        with col2:
            technician = st.text_input("الفني المسؤول / المقاول المكلف")
            status = st.selectbox("حالة المهمة", ["جديد", "قيد العمل عليه", "مكتمل", "مؤجل"])
            date = st.date_input("تاريخ الأمر", datetime.now()).strftime("%Y-%m-%d")
            description = st.text_area("وصف تفصيلي للعطل أو الإصلاح المطلوب")

        if st.button("حفظ مهمة الصيانة", use_container_width=True):
            if building and description:
                cursor.execute("INSERT INTO tasks (building, location, category, description, priority, technician, status, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (building, location, m_category, description, priority, technician, status, date))
                conn.commit()
                st.success("تم حفظ مهمة الصيانة بنجاح!")
            else:
                st.error("الرجاء إدخال اسم المبنى ووصف العطل على الأقل.")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. الإدخال المالي
elif menu == "💰 الإدخال المالي":
    st.markdown("### 💰 الإدارة المالية وعقود الصيانة")
    with st.container():
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            f_type = st.selectbox("نوع المعاملة", ["إيراد (قبض)", "مصروف (دفع)"])
            category = st.selectbox("التصنيف المالي", [
                "عقد صيانة دورية سنوي/شهري", 
                "دفعة إصلاح طارئ", 
                "أجور فنيين وعمالة", 
                "رسوم تراخيص وتصاريح حكومية", 
                "غرامات أو خصومات تشغيلية", 
                "إيرادات خدمات إضافية للمباني"
            ])
            description = st.text_input("بيان المعاملة / اسم العميل أو المستفيد")
        with col2:
            amount = st.number_input("المبلغ (ر.ق / ر.س)", min_value=0.0, format="%.2f")
            date = st.date_input("تاريخ المعاملة المالية", datetime.now()).strftime("%Y-%m-%d")

        if st.button("حفظ المعاملة المالية", use_container_width=True):
            if description and amount > 0:
                t_val = "revenue" if "إيراد" in f_type else "expense"
                cursor.execute("INSERT INTO finance (type, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                               (t_val, category, description, amount, date))
                conn.commit()
                st.success("تم تسجيل المعاملة المالية بنجاح!")
            else:
                st.error("الرجاء إدخال البيان والمبلغ الصحيح.")
        st.markdown('</div>', unsafe_allow_html=True)

# 3. إدخال المشتريات
elif menu == "🛒 إدخال المشتريات":
    st.markdown("### 🛒 مشتريات قطع الغيار ومواد التشغيل")
    with st.container():
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("اسم الصنف أو القطعة المطلوبة")
            p_category = st.selectbox("قسم المشتريات", [
                "قطع غيار تكييف وتبريد", 
                "مستلزمات وعمليات سباكة", 
                "أسلاك ومفاتيح وأدوات كهرباء", 
                "مواد دهان وأدوات نجارة", 
                "معدات أمن وسلامة مهنية"
            ])
            quantity = st.number_input("الكمية", min_value=1, value=1)
        with col2:
            price = st.number_input("إجمالي التكلفة / السعر", min_value=0.0, format="%.2f")
            supplier = st.text_input("اسم المورد / المحل")
            date = st.date_input("تاريخ الشراء", datetime.now()).strftime("%Y-%m-%d")

        if st.button("حفظ فاتورة المشتريات", use_container_width=True):
            if item_name and price > 0:
                cursor.execute("INSERT INTO purchases (item_name, category, quantity, price, supplier, date) VALUES (?, ?, ?, ?, ?, ?)",
                               (item_name, p_category, quantity, price, supplier, date))
                conn.commit()
                st.success("تم حفظ المشتريات بنجاح وإضافتها للنظام!")
            else:
                st.error("الرجاء إدخال اسم الصنف والسعر.")
        st.markdown('</div>', unsafe_allow_html=True)

# 4. شؤون الموظفين (حضور وغياب)
elif menu == "👥 شؤون الموظفين (حضور وغياب)":
    st.markdown("### 👥 إدارة الموظفين وسجل الحضور والغياب")
    
    tab_emp1, tab_emp2 = st.tabs(["إضافة موظفين جدد", "تسجيل الحضور والغياب اليومي"])
    
    with tab_emp1:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.subheader("تسجيل موظف جديد في النظام")
        emp_name = st.text_input("اسم الموظف الرباعي")
        qatari_id = st.text_input("رقم البطاقة الشخصية / الإقامة")
        role = st.selectbox("المسمى الوظيفي", ["فني تكييف", "فني كهرباء", "فني سباكة", "مشرف مباني", "عامل صيانة عامة"])
        
        if st.button("إضافة الموظف للقاعدة", use_container_width=True):
            if emp_name and qatari_id:
                cursor.execute("INSERT INTO employees (name, qatari_id, role) VALUES (?, ?, ?)", (emp_name, qatari_id, role))
                conn.commit()
                st.success(f"تمت إضافة الموظف ({emp_name}) بنجاح!")
            else:
                st.error("الرجاء إدخال اسم الموظف ورقم البطاقة الشخصية.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_emp2:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.subheader("سجل الحضور والغياب اليومي")
        
        cursor.execute("SELECT name FROM employees")
        emps = [row[0] for row in cursor.fetchall()]
        
        if emps:
            att_date = st.date_input("تاريخ اليوم", datetime.now()).strftime("%Y-%m-%d")
            selected_emp = st.selectbox("اختر الموظف", emps)
            att_status = st.selectbox("الحالة", ["حاضر", "غائب", "إجازة", "مهمة خارجية"])
            
            if st.button("حفظ حالة الحضور", use_container_width=True):
                cursor.execute("INSERT INTO attendance (emp_name, status, date) VALUES (?, ?, ?)", (selected_emp, att_status, att_date))
                conn.commit()
                st.success("تم تسجيل الحالة بنجاح!")
        else:
            st.info("لا يوجد موظفون مسجلون حالياً. يرجى إضافتهم من تبويب (إضافة موظفين جدد) أولاً.")
        st.markdown('</div>', unsafe_allow_html=True)

# 5. التقارير الشاملة
elif menu == "📊 التقارير الشاملة":
    st.markdown("### 📊 التقارير والسجلات التفصيلية الشاملة")
    
    rep_tab = st.selectbox("اختر التقرير المراد عرضه:", [
        "سجل مهام الصيانة للمباني", 
        "التقرير المالي وحساب الأرباح", 
        "سجل المشتريات", 
        "قائمة الموظفين وسجل الحضور والغياب"
    ])
    
    st.markdown("---")
    
    if rep_tab == "سجل مهام الصيانة للمباني":
        cursor.execute("SELECT id, building, location, category, description, priority, technician, status, date FROM tasks ORDER BY id DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["م", "المبنى", "الموقع", "التخصص", "الوصف", "الأولوية", "المسؤول", "الحالة", "التاريخ"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد مهام صيانة مسجلة.")
            
    elif rep_tab == "التقرير المالي وحساب الأرباح":
        cursor.execute("SELECT id, type, category, description, amount, date FROM finance ORDER BY date DESC")
        rows = cursor.fetchall()
        
        rev = sum([r[4] for r in rows if r[1] == 'revenue'])
        exp = sum([r[4] for r in rows if r[1] == 'expense'])
        net = rev - exp
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الإيرادات", f"{rev:,.2f}")
        c2.metric("إجمالي المصروفات", f"{exp:,.2f}")
        c3.metric("صافي الربح", f"{net:,.2f}")
        
        st.markdown("---")
        if rows:
            df = pd.DataFrame(rows, columns=["م", "النوع", "التصنيف", "البيان", "المبلغ", "التاريخ"])
            df["النوع"] = df["النوع"].apply(lambda x: "إيراد" if x == 'revenue' else "مصروف")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد معاملات مالية مسجلة.")
            
    elif rep_tab == "سجل المشتريات":
        cursor.execute("SELECT id, item_name, category, quantity, price, supplier, date FROM purchases ORDER BY id DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["م", "الصنف", "القسم", "الكمية", "السعر", "المورد", "التاريخ"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد فواتير مشتريات مسجلة.")
            
    elif rep_tab == "قائمة الموظفين وسجل الحضور والغياب":
        st.subheader("قائمة الموظفين المسجلين")
        cursor.execute("SELECT id, name, qatari_id, role FROM employees")
        e_rows = cursor.fetchall()
        if e_rows:
            df_e = pd.DataFrame(e_rows, columns=["م", "اسم الموظف", "رقم البطاقة الشخصية", "المسمى الوظيفي"])
            st.dataframe(df_e, use_container_width=True)
        else:
            st.info("لا يوجد موظفون مسجلون.")
            
        st.subheader("سجل الحضور والغياب اليومي")
        cursor.execute("SELECT id, emp_name, status, date FROM attendance ORDER BY id DESC")
        a_rows = cursor.fetchall()
        if a_rows:
            df_a = pd.DataFrame(a_rows, columns=["م", "اسم الموظف", "الحالة", "التاريخ"])
            st.dataframe(df_a, use_container_width=True)
        else:
            st.info("لا توجد سجلات حضور مسجلة.")
