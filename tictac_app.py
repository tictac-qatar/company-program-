import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
from pathlib import Path

# ============================================================
# TIC TAC - Building Maintenance Management System
# ============================================================

st.set_page_config(
    page_title="TIC TAC | Building Maintenance",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "tictac_pro.db"
LOGO_FILE = "IMG_7478.jpeg"

# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
USERS = {
    "Tictac.qatar": "Azoz@123"
}

# ------------------------------------------------------------
# Complete maintenance job list
# ------------------------------------------------------------
JOB_ROLES = [
    "مدير صيانة المباني",
    "مدير العمليات",
    "مدير المشاريع",
    "مدير الموقع",
    "مشرف صيانة",
    "مشرف ميكانيكا",
    "مشرف كهرباء",
    "مشرف سباكة",
    "مشرف تكييف و HVAC",
    "مشرف مدني",
    "مشرف سلامة وصحة مهنية HSE",
    "مهندس صيانة",
    "مهندس ميكانيكا",
    "مهندس كهرباء",
    "مهندس مدني",
    "مهندس تكييف و HVAC",
    "مهندس مكافحة حريق",
    "مهندس سلامة",
    "فني تكييف وتبريد",
    "فني كهرباء",
    "فني سباكة وصرف صحي",
    "فني مكافحة حريق",
    "فني إنذار حريق",
    "فني مصاعد",
    "فني مولدات",
    "فني مضخات",
    "فني BMS / تحكم ومباني ذكية",
    "فني أنظمة أمن ومراقبة CCTV",
    "فني شبكات واتصالات",
    "فني نجارة",
    "فني ألومنيوم وزجاج",
    "فني حدادة ولحام",
    "فني دهانات",
    "فني جبس وأسقف معلقة",
    "فني عزل مائي وحراري",
    "فني أعمال مدنية",
    "فني معدات مطابخ",
    "عامل صيانة عامة",
    "عامل نظافة",
    "عامل مساعد",
    "مراقب مخزون",
    "أمين مستودع",
    "مشتريات",
    "محاسب",
    "موظف موارد بشرية",
    "منسق صيانة",
    "منسق عقود",
    "مراقب جودة",
    "مسؤول سلامة HSE",
    "سائق",
    "مقاول خارجي",
]

MAINTENANCE_CATEGORIES = [
    "الكهرباء والإنارة",
    "التكييف والتبريد HVAC",
    "السباكة والصرف الصحي",
    "مضخات المياه",
    "مكافحة الحريق",
    "إنذار الحريق",
    "المولدات والكهرباء الاحتياطية",
    "المصاعد والسلالم المتحركة",
    "BMS والتحكم الآلي",
    "CCTV والأمن والمراقبة",
    "الشبكات والاتصالات",
    "الأبواب والأقفال",
    "الألومنيوم والزجاج",
    "النجارة",
    "الدهانات",
    "الجبس والأسقف المعلقة",
    "العزل المائي والحراري",
    "الأعمال المدنية",
    "الحدادة واللحام",
    "معدات المطابخ",
    "النظافة والخدمات العامة",
    "السلامة والصحة المهنية",
    "أخرى",
]

MATERIAL_CATEGORIES = [
    "مواد كهربائية",
    "مواد تكييف وتبريد",
    "مواد سباكة وصرف صحي",
    "مواد مضخات",
    "مواد مكافحة الحريق",
    "مواد إنذار الحريق",
    "مواد مولدات",
    "مواد مصاعد",
    "مواد BMS وتحكم",
    "مواد CCTV وأمن",
    "مواد شبكات واتصالات",
    "مواد نجارة",
    "مواد ألومنيوم وزجاج",
    "مواد حدادة ولحام",
    "مواد دهان",
    "مواد جبس وأسقف",
    "مواد عزل",
    "مواد مدنية وبناء",
    "مواد نظافة",
    "معدات وأدوات",
    "معدات سلامة شخصية PPE",
    "قطع غيار عامة",
    "أخرى",
]

UNITS = [
    "قطعة", "متر", "متر مربع", "متر مكعب", "كيلو", "جرام",
    "لتر", "جالون", "علبة", "كرتون", "رول", "طقم", "زوج", "وحدة"
]

# ------------------------------------------------------------
# CSS - Force Pure White Background Everywhere (Direct Overrides)
# ------------------------------------------------------------
st.markdown("""
<style>
/* Force pure white background on the entire app and view containers */
.stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stHeader"], 
[data-testid="stToolbar"], 
div.block-container, 
div[data-testid="stVerticalBlock"], 
section[data-testid="stSidebar"],
div.css-18e3th9, 
div.css-1d391kg {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #111827 !important;
}

/* Force Sidebar background and all inner elements to white/dark text */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e5e7eb !important;
}
section[data-testid="stSidebar"] * {
    color: #1f2937 !important;
    -webkit-text-fill-color: #1f2937 !important;
}

/* Force text and labels to be clearly readable */
h1, h2, h3, h4, h5, h6, label, p, span, div, .stMarkdown, .stText {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

/* Force all input fields, textareas, and select elements to be white */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
.stTextInput input,
.stPasswordInput input,
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    border-color: #d1d5db !important;
}

[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {
    background-color: #ffffff !important;
    color: #111827 !important;
}

/* Popovers, menus, and dropdowns background correction */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="calendar"],
[data-baseweb="select-dropdown"],
[role="listbox"],
[role="dialog"],
[role="menu"] {
    background-color: #ffffff !important;
    color: #111827 !important;
}

[data-baseweb="calendar"] *,
[data-baseweb="popover"] *,
[data-baseweb="menu"] *,
[role="listbox"] *,
[role="option"] * {
    background-color: transparent !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

/* Selected calendar day highlight */
[data-baseweb="calendar"] button[aria-selected="true"] {
    background-color: #d97706 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Custom Buttons Styling */
div.stButton > button {
    background-color: #1f2937 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
}
div.stButton > button:hover {
    background-color: #d97706 !important;
    color: #ffffff !important;
    border-color: #d97706 !important;
}

/* App Header & Card Styles */
.main-header {
    background-color: #ffffff !important;
    padding: 18px 24px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    border-top: 6px solid #d97706;
    text-align: center;
    margin-bottom: 22px;
    box-shadow: 0 2px 6px rgba(0,0,0,.04);
}
.main-header img {
    max-height: 135px;
    border-radius: 12px;
    margin-bottom: 8px;
}
.card {
    background-color: #ffffff !important;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 6px rgba(0,0,0,.04);
    margin-bottom: 18px;
}
.small-note {
    color: #4b5563 !important;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# Database Initialization & Management
# ------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building TEXT NOT NULL,
        client TEXT,
        location TEXT,
        category TEXT,
        job_type TEXT,
        description TEXT,
        priority TEXT,
        technician TEXT,
        status TEXT,
        date TEXT,
        planned_date TEXT,
        completion_date TEXT,
        estimated_cost REAL DEFAULT 0,
        actual_cost REAL DEFAULT 0,
        materials_used TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        item_name TEXT NOT NULL,
        category TEXT,
        unit TEXT,
        quantity REAL DEFAULT 0,
        min_quantity REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0,
        supplier TEXT,
        storage_location TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS material_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        transaction_type TEXT,
        quantity REAL,
        unit_cost REAL,
        reference TEXT,
        task_id INTEGER,
        date TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        category TEXT,
        description TEXT,
        amount REAL,
        date TEXT,
        reference TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        category TEXT,
        quantity REAL,
        unit TEXT,
        price REAL,
        supplier TEXT,
        invoice_no TEXT,
        date TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        qatari_id TEXT,
        phone TEXT,
        role TEXT,
        department TEXT,
        hire_date TEXT,
        salary REAL DEFAULT 0,
        status TEXT DEFAULT 'على رأس العمل',
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        emp_name TEXT,
        status TEXT,
        date TEXT,
        notes TEXT,
        UNIQUE(emp_id, date)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        client TEXT,
        address TEXT,
        contact_person TEXT,
        contact_phone TEXT,
        contract_no TEXT,
        contract_start TEXT,
        contract_end TEXT,
        contract_value REAL DEFAULT 0,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building TEXT,
        client TEXT,
        contract_no TEXT,
        contract_type TEXT,
        start_date TEXT,
        end_date TEXT,
        value REAL DEFAULT 0,
        status TEXT,
        notes TEXT
    )
    """)

    conn.commit()
    return conn


conn = init_db()
cur = conn.cursor()
today = date.today().isoformat()


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def query_df(sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)

def execute(sql, params=()):
    cur.execute(sql, params)
    conn.commit()
    return cur.lastrowid

def csv_download(df, filename):
    return st.download_button(
        "⬇️ تنزيل Excel/CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=False
    )

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.markdown("""
    <div class="main-header">
        <h1>TIC TAC</h1>
        <h3>صيانة المباني | Building Maintenance</h3>
        <p>نظام إدارة التشغيل والصيانة والمخزون والحسابات والموظفين</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
        st.markdown('</div>', unsafe_allow_html=True)

    return False


if not login():
    st.stop()


# ------------------------------------------------------------
# Header & Logo Display
# ------------------------------------------------------------
logo_html = ""
if Path(LOGO_FILE).exists():
    import base64
    encoded = base64.b64encode(Path(LOGO_FILE).read_bytes()).decode()
    logo_html = f'<img src="data:image/jpeg;base64,{encoded}" alt="TIC TAC Logo">'

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <h1>TIC TAC لصيانة المباني</h1>
    <p>Building Maintenance Management System</p>
    <p class="small-note">التشغيل • الصيانة • المواد • المشتريات • الحسابات • الموظفون • العقود • التقارير</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Sidebar Navigation
# ------------------------------------------------------------
if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("## 🗂️ أقسام النظام")
menu = st.sidebar.radio("اختر القسم:", [
    "🏠 لوحة التحكم",
    "🛠️ أوامر الصيانة",
    "📦 المواد والمخزون",
    "🛒 المشتريات",
    "🏢 المباني والعملاء والعقود",
    "💰 الحسابات والمالية",
    "👥 الموظفون والحضور",
    "📊 التقارير",
])


# ============================================================
# Dashboard Section
# ============================================================
if menu == "🏠 لوحة التحكم":
    st.markdown("## 📊 لوحة التحكم")

    tasks_count = cur.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    open_tasks = cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE status NOT IN ('مكتمل','ملغي')"
    ).fetchone()[0]
    employees_count = cur.execute(
        "SELECT COUNT(*) FROM employees WHERE status='على رأس العمل'"
    ).fetchone()[0]
    low_stock = cur.execute(
        "SELECT COUNT(*) FROM materials WHERE quantity <= min_quantity"
    ).fetchone()[0]

    rev = cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='revenue'"
    ).fetchone()[0]
    exp = cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='expense'"
    ).fetchone()[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("إجمالي أوامر الصيانة", tasks_count)
    c2.metric("مهام مفتوحة", open_tasks)
    c3.metric("الموظفون على رأس العمل", employees_count)
    c4.metric("أصناف منخفضة المخزون", low_stock)
    c5.metric("صافي الربح", f"{rev-exp:,.2f} ر.ق")

    st.markdown("### ⚠️ تنبيهات المخزون")
    low_df = query_df("""
        SELECT item_code AS "الكود", item_name AS "الصنف",
               category AS "القسم", quantity AS "الرصيد",
               min_quantity AS "الحد الأدنى", unit AS "الوحدة",
               supplier AS "المورد"
        FROM materials
        WHERE quantity <= min_quantity
        ORDER BY quantity ASC
    """)
    if low_df.empty:
        st.success("المخزون ضمن الحدود الحالية.")
    else:
        st.dataframe(low_df, use_container_width=True)

    st.markdown("### 🛠️ آخر أوامر الصيانة")
    recent = query_df("""
        SELECT id AS "رقم الأمر", building AS "المبنى",
               category AS "التخصص", priority AS "الأولوية",
               technician AS "الفني", status AS "الحالة", date AS "التاريخ"
        FROM tasks ORDER BY id DESC LIMIT 10
    """)
    st.dataframe(recent, use_container_width=True)


# ============================================================
# Work Orders Section
# ============================================================
elif menu == "🛠️ أوامر الصيانة":
    st.markdown("## 🛠️ أوامر الصيانة وإدارة البلاغات")

    tab1, tab2 = st.tabs(["➕ أمر صيانة جديد", "📋 سجل أوامر الصيانة"])

    with tab1:
        with st.container():
            c1, c2 = st.columns(2)

            with c1:
                building = st.text_input("اسم المبنى / المشروع *")
                client = st.text_input("اسم العميل")
                location = st.text_input("الموقع / الطابق / الغرفة")
                category = st.selectbox("تخصص الصيانة", MAINTENANCE_CATEGORIES)
                job_type = st.selectbox(
                    "نوع العمل",
                    ["بلاغ عطل", "صيانة وقائية", "صيانة تصحيحية",
                     "فحص دوري", "تركيب", "استبدال", "طوارئ", "أعمال تحسين"]
                )
                priority = st.selectbox(
                    "الأولوية", ["عادي", "متوسط", "عالي", "طوارئ قصوى"]
                )

            with c2:
                technician = st.text_input("الفني / المشرف / المقاول المسؤول")
                status = st.selectbox(
                    "الحالة", ["جديد", "تم التعيين", "قيد العمل",
                               "بانتظار مواد", "بانتظار العميل", "مكتمل", "ملغي"]
                )
                work_date = st.date_input("تاريخ البلاغ", value=date.today())
                planned_date = st.date_input("التاريخ المخطط", value=date.today())
                completion_date = st.date_input("تاريخ الإنجاز", value=date.today())
                estimated_cost = st.number_input("التكلفة التقديرية (ر.ق)", min_value=0.0, format="%.2f")
                actual_cost = st.number_input("التكلفة الفعلية (ر.ق)", min_value=0.0, format="%.2f")

            description = st.text_area("وصف العطل / الأعمال المطلوبة *", height=100)
            materials_used = st.text_area(
                "المواد المستخدمة",
                placeholder="مثال: 2 فلتر 20x20، 3 متر كيبل 4mm، 1 علبة سيليكون..."
            )
            notes = st.text_area("ملاحظات الفني / العميل")

            if st.button("💾 حفظ أمر الصيانة", use_container_width=True):
                if building.strip() and description.strip():
                    execute("""
                    INSERT INTO tasks
                    (building,client,location,category,job_type,description,priority,
                     technician,status,date,planned_date,completion_date,
                     estimated_cost,actual_cost,materials_used,notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        building, client, location, category, job_type, description,
                        priority, technician, status, work_date.isoformat(),
                        planned_date.isoformat(), completion_date.isoformat(),
                        estimated_cost, actual_cost, materials_used, notes
                    ))
                    st.success("تم حفظ أمر الصيانة بنجاح.")
                else:
                    st.error("يجب إدخال اسم المبنى ووصف العمل على الأقل.")

    with tab2:
        search = st.text_input("🔎 بحث في أوامر الصيانة")
        if search:
            df = query_df("""
                SELECT id AS "رقم الأمر", building AS "المبنى", client AS "العميل",
                       location AS "الموقع", category AS "التخصص",
                       job_type AS "نوع العمل", description AS "الوصف",
                       priority AS "الأولوية", technician AS "المسؤول",
                       status AS "الحالة", date AS "التاريخ",
                       estimated_cost AS "التكلفة التقديرية",
                       actual_cost AS "التكلفة الفعلية", materials_used AS "المواد المستخدمة"
                FROM tasks
                WHERE building LIKE ? OR client LIKE ? OR technician LIKE ?
                   OR description LIKE ? OR category LIKE ?
                ORDER BY id DESC
            """, tuple([f"%{search}%"] * 5))
        else:
            df = query_df("""
                SELECT id AS "رقم الأمر", building AS "المبنى", client AS "العميل",
                       location AS "الموقع", category AS "التخصص",
                       job_type AS "نوع العمل", description AS "الوصف",
                       priority AS "الأولوية", technician AS "المسؤول",
                       status AS "الحالة", date AS "التاريخ",
                       estimated_cost AS "التكلفة التقديرية",
                       actual_cost AS "التكلفة الفعلية", materials_used AS "المواد المستخدمة"
                FROM tasks ORDER BY id DESC
            """)

        st.dataframe(df, use_container_width=True, height=450)
        if not df.empty:
            csv_download(df, "tictac_maintenance_orders.csv")


# ============================================================
# Materials & Inventory Section
# ============================================================
elif menu == "📦 المواد والمخزون":
    st.markdown("## 📦 إدارة مواد وقطع غيار صيانة المباني")

    tab1, tab2, tab3 = st.tabs([
        "➕ تعريف مادة / قطعة",
        "🔄 حركة المخزون",
        "📋 المخزون الحالي"
    ])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            item_code = st.text_input("كود المادة / SKU")
            item_name = st.text_input("اسم المادة أو قطعة الغيار *")
            mcat = st.selectbox("تصنيف المادة", MATERIAL_CATEGORIES)
            unit = st.selectbox("الوحدة", UNITS)
            quantity = st.number_input("الرصيد الافتتاحي", min_value=0.0, value=0.0)
            min_quantity = st.number_input("الحد الأدنى لإعادة الطلب", min_value=0.0, value=0.0)

        with c2:
            unit_cost = st.number_input("سعر الوحدة (ر.ق)", min_value=0.0, format="%.2f")
            supplier = st.text_input("المورد")
            storage_location = st.text_input("مكان التخزين / الرف")
            notes = st.text_area("ملاحظات المادة")

        if st.button("💾 حفظ المادة", use_container_width=True):
            if item_name.strip():
                execute("""
                INSERT INTO materials
                (item_code,item_name,category,unit,quantity,min_quantity,unit_cost,
                 supplier,storage_location,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    item_code, item_name, mcat, unit, quantity, min_quantity,
                    unit_cost, supplier, storage_location, notes
                ))
                st.success("تمت إضافة المادة إلى المخزون.")
            else:
                st.error("أدخل اسم المادة.")

    with tab2:
        materials_df = query_df(
            "SELECT id, item_name, unit, quantity, unit_cost FROM materials ORDER BY item_name"
        )
        if materials_df.empty:
            st.info("أضف المواد أولاً.")
        else:
            mat_options = {
                f"{r.item_name} | الرصيد: {r.quantity:g} {r.unit}": int(r.id)
                for _, r in materials_df.iterrows()
            }
            selected_label = st.selectbox("اختر المادة", list(mat_options.keys()))
            material_id = mat_options[selected_label]

            t1, t2 = st.columns(2)
            with t1:
                transaction_type = st.selectbox(
                    "نوع الحركة",
                    ["إضافة شراء", "صرف للصيانة", "مرتجع للمخزن", "تسوية زيادة", "تسوية نقص"]
                )
                trans_qty = st.number_input("الكمية", min_value=0.01, value=1.0)
                trans_cost = st.number_input("سعر الوحدة", min_value=0.0, format="%.2f")
            with t2:
                reference = st.text_input("رقم الفاتورة / رقم أمر الصيانة")
                trans_date = st.date_input("تاريخ الحركة", value=date.today())
                trans_notes = st.text_input("ملاحظات")

            if st.button("🔄 حفظ حركة المخزون", use_container_width=True):
                current = cur.execute(
                    "SELECT quantity FROM materials WHERE id=?", (material_id,)
                ).fetchone()[0]

                additions = ["إضافة شراء", "مرتجع للمخزن", "تسوية زيادة"]
                deductions = ["صرف للصيانة", "تسوية نقص"]

                new_qty = current
                if transaction_type in additions:
                    new_qty += trans_qty
                elif transaction_type in deductions:
                    new_qty -= trans_qty

                if new_qty < 0:
                    st.error("لا يمكن صرف كمية أكبر من الرصيد المتاح.")
                else:
                    execute(
                        "UPDATE materials SET quantity=? WHERE id=?",
                        (new_qty, material_id)
                    )
                    execute("""
                    INSERT INTO material_transactions
                    (material_id,transaction_type,quantity,unit_cost,reference,date,notes)
                    VALUES (?,?,?,?,?,?,?)
                    """, (
                        material_id, transaction_type, trans_qty, trans_cost,
                        reference, trans_date.isoformat(), trans_notes
                    ))
                    st.success(f"تم حفظ الحركة. الرصيد الجديد: {new_qty:g}")

    with tab3:
        stock = query_df("""
            SELECT id AS "م", item_code AS "الكود", item_name AS "المادة",
                   category AS "التصنيف", unit AS "الوحدة",
                   quantity AS "الرصيد", min_quantity AS "الحد الأدنى",
                   unit_cost AS "سعر الوحدة", supplier AS "المورد",
                   storage_location AS "مكان التخزين"
            FROM materials ORDER BY category, item_name
        """)
        st.dataframe(stock, use_container_width=True, height=500)
        if not stock.empty:
            csv_download(stock, "tictac_materials_inventory.csv")


# ============================================================
# Purchases Section
# ============================================================
elif menu == "🛒 المشتريات":
    st.markdown("## 🛒 المشتريات وفواتير الموردين")

    c1, c2 = st.columns(2)
    with c1:
        item_name = st.text_input("اسم الصنف / القطعة *")
        p_category = st.selectbox("قسم المشتريات", MATERIAL_CATEGORIES)
        quantity = st.number_input("الكمية", min_value=0.01, value=1.0)
        unit = st.selectbox("الوحدة", UNITS)
    with c2:
        price = st.number_input("إجمالي الفاتورة (ر.ق)", min_value=0.0, format="%.2f")
        supplier = st.text_input("اسم المورد")
        invoice_no = st.text_input("رقم الفاتورة")
        purchase_date = st.date_input("تاريخ الشراء", value=date.today())

    notes = st.text_area("ملاحظات")

    if st.button("💾 حفظ فاتورة الشراء", use_container_width=True):
        if item_name.strip() and price > 0:
            execute("""
            INSERT INTO purchases
            (item_name,category,quantity,unit,price,supplier,invoice_no,date,notes)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                item_name, p_category, quantity, unit, price,
                supplier, invoice_no, purchase_date.isoformat(), notes
            ))
            st.success("تم حفظ فاتورة المشتريات.")

    st.markdown("### 📋 سجل المشتريات")
    purchases = query_df("""
        SELECT id AS "م", item_name AS "الصنف", category AS "التصنيف",
               quantity AS "الكمية", unit AS "الوحدة", price AS "السعر",
               supplier AS "المورد", invoice_no AS "الفاتورة", date AS "التاريخ"
        FROM purchases ORDER BY id DESC
    """)
    st.dataframe(purchases, use_container_width=True)
    if not purchases.empty:
        csv_download(purchases, "tictac_purchases.csv")


# ============================================================
# Buildings, Clients & Contracts Section
# ============================================================
elif menu == "🏢 المباني والعملاء والعقود":
    st.markdown("## 🏢 المباني والعملاء والعقود")

    tab1, tab2 = st.tabs(["🏢 المباني والعملاء", "📄 العقود"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            bname = st.text_input("اسم المبنى / المشروع *")
            bclient = st.text_input("العميل")
            address = st.text_input("العنوان / المنطقة")
            contact_person = st.text_input("مسؤول العميل")
        with c2:
            contact_phone = st.text_input("هاتف المسؤول")
            contract_no = st.text_input("رقم العقد")
            contract_start = st.date_input("بداية العقد", value=date.today())
            contract_end = st.date_input("نهاية العقد", value=date.today())
            contract_value = st.number_input("قيمة العقد (ر.ق)", min_value=0.0, format="%.2f")
        bnotes = st.text_area("ملاحظات المبنى")

        if st.button("💾 حفظ المبنى", use_container_width=True):
            if bname.strip():
                execute("""
                INSERT INTO buildings
                (name,client,address,contact_person,contact_phone,contract_no,
                 contract_start,contract_end,contract_value,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    bname, bclient, address, contact_person, contact_phone, contract_no,
                    contract_start.isoformat(), contract_end.isoformat(),
                    contract_value, bnotes
                ))
                st.success("تم حفظ بيانات المبنى.")

        buildings = query_df("""
            SELECT id AS "م", name AS "المبنى", client AS "العميل",
                   address AS "العنوان", contact_person AS "المسؤول",
                   contact_phone AS "الهاتف", contract_no AS "رقم العقد",
                   contract_start AS "بداية العقد", contract_end AS "نهاية العقد",
                   contract_value AS "قيمة العقد"
            FROM buildings ORDER BY id DESC
        """)
        st.dataframe(buildings, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            cb = st.text_input("المبنى / المشروع")
            cc = st.text_input("العميل")
            cno = st.text_input("رقم العقد")
            ctype = st.selectbox("نوع العقد", [
                "صيانة شاملة", "صيانة وقائية", "صيانة تصحيحية",
                "إدارة مرافق FM", "نظافة وخدمات", "أخرى"
            ])
        with c2:
            cs = st.date_input("تاريخ البداية", value=date.today())
            ce = st.date_input("تاريخ النهاية", value=date.today())
            cv = st.number_input("قيمة العقد", min_value=0.0, format="%.2f")
            cstatus = st.selectbox("حالة العقد", ["ساري", "منتهي", "معلق", "ملغي"])

        cn = st.text_area("ملاحظات العقد")
        if st.button("💾 حفظ العقد", use_container_width=True):
            execute("""
            INSERT INTO contracts
            (building,client,contract_no,contract_type,start_date,end_date,value,status,notes)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (cb, cc, cno, ctype, cs.isoformat(), ce.isoformat(), cv, cstatus, cn))
            st.success("تم حفظ العقد.")

        contracts = query_df("""
            SELECT id AS "م", building AS "المبنى", client AS "العميل",
                   contract_no AS "رقم العقد", contract_type AS "نوع العقد",
                   start_date AS "البداية", end_date AS "النهاية",
                   value AS "القيمة", status AS "الحالة"
            FROM contracts ORDER BY id DESC
        """)
        st.dataframe(contracts, use_container_width=True)


# ============================================================
# Finance Section
# ============================================================
elif menu == "💰 الحسابات والمالية":
    st.markdown("## 💰 الإدارة المالية")

    c1, c2 = st.columns(2)
    with c1:
        ftype = st.selectbox("نوع المعاملة", ["إيراد", "مصروف"])
        fcat = st.selectbox("التصنيف المالي", [
            "عقود صيانة",
            "إصلاحات وطوارئ",
            "أجور ورواتب",
            "شراء مواد وقطع غيار",
            "معدات وأدوات",
            "سيارات ونقل",
            "إيجارات",
            "تراخيص وتصاريح",
            "مصاريف تشغيلية",
            "إيرادات خدمات إضافية",
            "أخرى"
        ])
        fdesc = st.text_input("بيان المعاملة *")
    with c2:
        amount = st.number_input("المبلغ (ر.ق)", min_value=0.0, format="%.2f")
        fdate = st.date_input("التاريخ", value=date.today())
        ref = st.text_input("رقم المرجع / الفاتورة / العقد")

    if st.button("💾 حفظ المعاملة", use_container_width=True):
        if fdesc.strip() and amount > 0:
            execute("""
            INSERT INTO finance(type,category,description,amount,date,reference)
            VALUES (?,?,?,?,?,?)
            """, (
                "revenue" if ftype == "إيراد" else "expense",
                fcat, fdesc, amount, fdate.isoformat(), ref
            ))
            st.success("تم حفظ المعاملة المالية.")
        else:
            st.error("أدخل البيان والمبلغ.")

    rev = cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='revenue'"
    ).fetchone()[0]
    exp = cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='expense'"
    ).fetchone()[0]

    a, b, c = st.columns(3)
    a.metric("إجمالي الإيرادات", f"{rev:,.2f} ر.ق")
    b.metric("إجمالي المصروفات", f"{exp:,.2f} ر.ق")
    c.metric("صافي الربح", f"{rev-exp:,.2f} ر.ق")

    finance = query_df("""
        SELECT id AS "م",
               CASE WHEN type='revenue' THEN 'إيراد' ELSE 'مصروف' END AS "النوع",
               category AS "التصنيف", description AS "البيان",
               amount AS "المبلغ", date AS "التاريخ", reference AS "المرجع"
        FROM finance ORDER BY date DESC, id DESC
    """)
    st.dataframe(finance, use_container_width=True)
    if not finance.empty:
        csv_download(finance, "tictac_finance.csv")


# ============================================================
# Employees & Attendance Section
# ============================================================
elif menu == "👥 الموظفون والحضور":
    st.markdown("## 👥 شؤون الموظفين والحضور والغياب")

    tab1, tab2, tab3 = st.tabs([
        "➕ إضافة موظف",
        "🕘 الحضور والغياب",
        "📋 قائمة الموظفين"
    ])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            emp_name = st.text_input("اسم الموظف الرباعي *")
            qatari_id = st.text_input("رقم البطاقة الشخصية / الإقامة")
            phone = st.text_input("رقم الهاتف")
            role = st.selectbox("الوظيفة", JOB_ROLES)
            department = st.selectbox("القسم", [
                "الصيانة", "الكهرباء", "الميكانيكا", "التكييف",
                "السباكة", "المدني", "السلامة", "المخازن",
                "المشتريات", "الحسابات", "الموارد البشرية",
                "الإدارة", "النظافة", "أخرى"
            ])
        with c2:
            hire_date = st.date_input("تاريخ التعيين", value=date.today())
            salary = st.number_input("الراتب (ر.ق)", min_value=0.0, format="%.2f")
            emp_status = st.selectbox("حالة الموظف", [
                "على رأس العمل", "إجازة", "موقوف", "منتهي الخدمة"
            ])
            emp_notes = st.text_area("ملاحظات")

        if st.button("💾 إضافة الموظف", use_container_width=True):
            if emp_name.strip():
                execute("""
                INSERT INTO employees
                (name,qatari_id,phone,role,department,hire_date,salary,status,notes)
                VALUES (?,?,?,?,?,?,?,?,?)
                """, (
                    emp_name, qatari_id, phone, role, department,
                    hire_date.isoformat(), salary, emp_status, emp_notes
                ))
                st.success(f"تمت إضافة الموظف: {emp_name}")
            else:
                st.error("أدخل اسم الموظف.")

    with tab2:
        emps = query_df("""
            SELECT id, name, role FROM employees
            WHERE status='على رأس العمل' ORDER BY name
        """)
        if emps.empty:
            st.info("لا يوجد موظفون على رأس العمل.")
        else:
            emp_map = {
                f"{r['name']} — {r['role']}": int(r["id"])
                for _, r in emps.iterrows()
            }
            selected = st.selectbox("اختر الموظف", list(emp_map.keys()))
            emp_id = emp_map[selected]
            emp_name_selected = selected.split(" — ")[0]
            att_date = st.date_input("تاريخ الحضور", value=date.today())
            att_status = st.selectbox(
                "الحالة", ["حاضر", "غائب", "إجازة", "مهمة خارجية", "راحة"]
            )
            att_notes = st.text_input("ملاحظات")

            if st.button("💾 حفظ الحضور", use_container_width=True):
                execute("""
                INSERT INTO attendance(emp_id,emp_name,status,date,notes)
                VALUES (?,?,?,?,?)
                ON CONFLICT(emp_id,date)
                DO UPDATE SET emp_name=excluded.emp_name,
                              status=excluded.status,
                              notes=excluded.notes
                """, (
                    emp_id, emp_name_selected, att_status,
                    att_date.isoformat(), att_notes
                ))
                st.success("تم حفظ حالة الحضور.")

        attendance = query_df("""
            SELECT id AS "م", emp_name AS "الموظف",
                   status AS "الحالة", date AS "التاريخ", notes AS "ملاحظات"
            FROM attendance ORDER BY date DESC, id DESC
        """)
        st.dataframe(attendance, use_container_width=True)

    with tab3:
        employees = query_df("""
            SELECT id AS "م", name AS "الموظف",
                   qatari_id AS "البطاقة/الإقامة", phone AS "الهاتف",
                   role AS "الوظيفة", department AS "القسم",
                   hire_date AS "تاريخ التعيين", salary AS "الراتب",
                   status AS "الحالة"
            FROM employees ORDER BY id DESC
        """)
        st.dataframe(employees, use_container_width=True)
        if not employees.empty:
            csv_download(employees, "tictac_employees.csv")


# ============================================================
# Reports Section
# ============================================================
elif menu == "📊 التقارير":
    st.markdown("## 📊 التقارير الشاملة")

    report = st.selectbox("اختر التقرير:", [
        "أوامر الصيانة",
        "المواد والمخزون",
        "حركات المخزون",
        "المشتريات",
        "المالية",
        "الموظفون",
        "الحضور والغياب",
        "المباني والعقود",
    ])

    if report == "أوامر الصيانة":
        df = query_df("SELECT * FROM tasks ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_tasks.csv")

    elif report == "المواد والمخزون":
        df = query_df("SELECT * FROM materials ORDER BY category,item_name")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_materials.csv")

    elif report == "حركات المخزون":
        df = query_df("""
            SELECT mt.id, m.item_name, m.unit, mt.transaction_type,
                   mt.quantity, mt.unit_cost, mt.reference,
                   mt.date, mt.notes
            FROM material_transactions mt
            LEFT JOIN materials m ON m.id=mt.material_id
            ORDER BY mt.id DESC
        """)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_stock_transactions.csv")

    elif report == "المشتريات":
        df = query_df("SELECT * FROM purchases ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_purchases.csv")

    elif report == "المالية":
        df = query_df("SELECT * FROM finance ORDER BY date DESC,id DESC")
        rev = df.loc[df["type"] == "revenue", "amount"].sum() if not df.empty else 0
        exp = df.loc[df["type"] == "expense", "amount"].sum() if not df.empty else 0
        x, y, z = st.columns(3)
        x.metric("الإيرادات", f"{rev:,.2f} ر.ق")
        y.metric("المصروفات", f"{exp:,.2f} ر.ق")
        z.metric("الصافي", f"{rev-exp:,.2f} ر.ق")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_finance.csv")

    elif report == "الموظفون":
        df = query_df("SELECT * FROM employees ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_employees.csv")

    elif report == "الحضور والغياب":
        df = query_df("SELECT * FROM attendance ORDER BY date DESC,id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv_download(df, "tictac_report_attendance.csv")

    elif report == "المباني والعقود":
        buildings = query_df("SELECT * FROM buildings ORDER BY id DESC")
        contracts = query_df("SELECT * FROM contracts ORDER BY id DESC")
        st.markdown("### المباني")
        st.dataframe(buildings, use_container_width=True)
        st.markdown("### العقود")
        st.dataframe(contracts, use_container_width=True)
        if not buildings.empty:
            csv_download(buildings, "tictac_report_buildings.csv")


st.sidebar.markdown("---")
st.sidebar.caption("TIC TAC Building Maintenance")
st.sidebar.caption("Qatar • نظام إدارة الصيانة")
