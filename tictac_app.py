import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path

# ============================================================
# TIC TAC - Building Maintenance Management System (PRO)
# ============================================================

st.set_page_config(
    page_title="TIC TAC | Building Maintenance Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "tictac_pro_v2.db"
LOGO_FILE = "IMG_7478.jpeg"

# ------------------------------------------------------------
# Authentication
# ------------------------------------------------------------
USERS = {
    "Tictac.qatar": "Azoz@123"
}

# ------------------------------------------------------------
# Constants & Master Lists
# ------------------------------------------------------------
MAINTENANCE_SPECIALTIES = [
    "الكهرباء",
    "HVAC (التكييف والتبريد)",
    "السباكة",
    "الصرف الصحي",
    "مضخات المياه",
    "Fire Fighting (مكافحة الحريق)",
    "Fire Alarm (إنذار الحريق)",
    "المولدات",
    "UPS",
    "المصاعد",
    "BMS (التحكم الآلي)",
    "CCTV (كاميرات المراقبة)",
    "Access Control (أنظمة الدخول)",
    "الشبكات والاتصالات",
    "أبواب وأقفال",
    "نجارة",
    "ألومنيوم وزجاج",
    "دهانات",
    "جبس وأسقف",
    "عزل",
    "أعمال مدنية",
    "حدادة ولحام",
    "معدات مطابخ",
    "نظافة",
    "HSE (السلامة والصحة المهنية)",
    "أخرى"
]

JOB_ROLES = [
    "مدير صيانة المباني", "مدير العمليات", "مدير المشاريع", "مدير الموقع",
    "مشرف صيانة", "مهندس صيانة", "فني كهرباء", "فني تكييف HVAC", "فني سباكة",
    "فني مكافحة حريق", "فني إنذار حريق", "فني مصاعد", "فني مولدات", "فني BMS",
    "فني CCTV وأمن", "فني شبكات", "فني نجارة", "فني دهانات", "فني مدني",
    "فني عزل", "عامل صيانة عامة", "مسؤول سلامة HSE", "أمين مستودع", "محاسب", "سائق"
]

MATERIAL_CATEGORIES = [
    "مواد كهربائية", "مواد تكييف HVAC", "مواد سباكة وصرف", "مضخات وقطع غيار",
    "مكافحة وإنذار الحريق", "مولدات و UPS", "مصاعد", "BMS وتحكم",
    "CCTV وأمن", "شبكات واتصالات", "نجارة وأبواب", "ألومنيوم وزجاج",
    "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية وبناء", "حدادة ولحام",
    "معدات مطابخ", "مواد نظافة", "معدات سلامة PPE", "قطع غيار عامة", "أخرى"
]

UNITS = [
    "قطعة", "متر", "متر مربع", "متر مكعب", "كيلو", "جرام",
    "لتر", "جالون", "علبة", "كرتون", "رول", "طقم", "زوج", "وحدة"
]

# ------------------------------------------------------------
# CSS Styling - Pure White High Contrast & RTL Arabic
# ------------------------------------------------------------
st.markdown("""
<style>
/* Global App Background & Text Color Fixes */
.stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stHeader"], 
[data-testid="stToolbar"], 
div.block-container, 
div[data-testid="stVerticalBlock"], 
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #111827 !important;
    direction: rtl !important;
    text-align: right !important;
}

section[data-testid="stSidebar"] {
    border-left: 1px solid #e5e7eb !important;
    border-right: none !important;
}

/* Force readable dark text everywhere */
h1, h2, h3, h4, h5, h6, label, p, span, div, .stMarkdown, .stText, .streamlit-expanderHeader {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    direction: rtl !important;
    text-align: right !important;
}

/* Form Inputs, Selectboxes, Textareas styling */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
.stTextInput input,
.stPasswordInput input,
.stTextArea textarea,
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    border-color: #cbd5e1 !important;
    border-radius: 6px !important;
}

/* Dropdown menus and popovers */
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
    background-color: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

[data-baseweb="calendar"] button[aria-selected="true"] {
    background-color: #d97706 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Buttons styling */
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

/* Sidebar button exceptions */
section[data-testid="stSidebar"] div.stButton > button {
    background-color: #ffffff !important;
    color: #1f2937 !important;
    -webkit-text-fill-color: #1f2937 !important;
    border: 1px solid #d1d5db !important;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #f3f4f6 !important;
    color: #111827 !important;
}

/* Custom Header Card */
.main-header {
    background-color: #ffffff !important;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    border-top: 6px solid #d97706;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.main-header img {
    max-height: 120px;
    border-radius: 10px;
    margin-bottom: 10px;
}

/* Cards */
.card {
    background-color: #ffffff !important;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# Database Setup & Relational Integrity (SQLite)
# ------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 1. Buildings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        client TEXT,
        address TEXT,
        contact_person TEXT,
        contact_phone TEXT,
        floors_count INTEGER DEFAULT 1,
        systems_installed TEXT,
        notes TEXT
    )
    """)

    # 2. Contracts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_id INTEGER,
        contract_no TEXT UNIQUE,
        contract_type TEXT,
        value REAL DEFAULT 0,
        services_included TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'ساري',
        notes TEXT,
        FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
    )
    """)

    # 3. Employees
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
        skills TEXT,
        notes TEXT
    )
    """)

    # 4. Materials (Inventory master)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT UNIQUE,
        barcode_sku TEXT,
        arabic_name TEXT NOT NULL,
        english_name TEXT,
        category TEXT,
        unit TEXT,
        quantity REAL DEFAULT 0,
        min_quantity REAL DEFAULT 0,
        reorder_point REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0,
        avg_cost REAL DEFAULT 0,
        supplier TEXT,
        storage_location TEXT,
        shelf_no TEXT,
        manufacturer TEXT,
        part_no TEXT,
        model TEXT,
        serial_no TEXT,
        warranty_date TEXT,
        notes TEXT
    )
    """)

    # 5. Work Orders (Tasks)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_no TEXT UNIQUE,
        building_id INTEGER,
        location TEXT,
        room TEXT,
        system_type TEXT,
        job_type TEXT,
        priority TEXT,
        description TEXT,
        technician_id INTEGER,
        supervisor_id INTEGER,
        report_date TEXT,
        assignment_date TEXT,
        start_date TEXT,
        completion_date TEXT,
        sla_hours REAL DEFAULT 24,
        estimated_cost REAL DEFAULT 0,
        actual_cost REAL DEFAULT 0,
        status TEXT DEFAULT 'جديد',
        materials_used TEXT,
        notes TEXT,
        FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL,
        FOREIGN KEY (technician_id) REFERENCES employees(id) ON DELETE SET NULL,
        FOREIGN KEY (supervisor_id) REFERENCES employees(id) ON DELETE SET NULL
    )
    """)

    # 6. Inventory Transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS material_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        transaction_type TEXT,
        quantity REAL,
        unit_cost REAL,
        reference TEXT,
        task_id INTEGER,
        warehouse_from TEXT,
        warehouse_to TEXT,
        date TEXT,
        notes TEXT,
        FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
    )
    """)

    # 7. Purchases (PR & PO)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_no TEXT UNIQUE,
        item_name TEXT,
        category TEXT,
        quantity REAL,
        unit TEXT,
        price REAL,
        tax REAL DEFAULT 0,
        total_amount REAL,
        supplier TEXT,
        invoice_no TEXT,
        date TEXT,
        status TEXT DEFAULT 'مكتمل',
        notes TEXT
    )
    """)

    # 8. Attendance
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        status TEXT,
        date TEXT,
        work_hours REAL DEFAULT 8,
        notes TEXT,
        UNIQUE(emp_id, date),
        FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE
    )
    """)

    # 9. Finance
    cur.execute("""
    CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        category TEXT,
        description TEXT,
        amount REAL,
        date TEXT,
        reference TEXT,
        task_id INTEGER,
        contract_id INTEGER,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
        FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()
conn = get_conn()
today = date.today().isoformat()

# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def query_df(sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)

def execute(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    return cur.lastrowid

def csv_download(df, filename):
    return st.download_button(
        "⬇️ تنزيل البيانات كملف CSV / Excel",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=False
    )

def login_screen():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.markdown("""
    <div class="main-header">
        <h1>TIC TAC</h1>
        <h3>نظام إدارة صيانة المباني والمرافق الاحترافي</h3>
        <p>Building Maintenance & Facilities Management System</p>
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

if not login_screen():
    st.stop()


# ------------------------------------------------------------
# App Header & Navigation
# ------------------------------------------------------------
logo_html = ""
if Path(LOGO_FILE).exists():
    import base64
    encoded = base64.b64encode(Path(LOGO_FILE).read_bytes()).decode()
    logo_html = f'<img src="data:image/jpeg;base64,{encoded}" alt="TIC TAC Logo">'

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <h1>TIC TAC لإدارة صيانة المباني</h1>
    <p>Facility & Building Maintenance Management Platform</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("### 🗂️ القائمة الرئيسية")
menu = st.sidebar.radio("اختر القسم:", [
    "🏠 لوحة التحكم (Dashboard)",
    "🛠️ أوامر الصيانة والبلاغات",
    "📦 المواد وقطع الغيار",
    "🔄 حركة المخزون",
    "🛒 المشتريات",
    "🏢 المباني والعملاء",
    "📄 العقود",
    "👥 الموظفون",
    "🕘 الحضور والدوام",
    "💰 الحسابات والمالية",
    "📊 التقارير الشاملة"
])


# ============================================================
# 1. Dashboard (لوحة التحكم الاحترافية)
# ============================================================
if menu == "🏠 لوحة التحكم (Dashboard)":
    st.markdown("## 📊 لوحة التحكم الشاملة")

    # Metrics aggregation
    total_tasks = query_df("SELECT COUNT(*) FROM tasks").iloc[0,0]
    open_tasks = query_df("SELECT COUNT(*) FROM tasks WHERE status NOT IN ('مكتمل','ملغي')").iloc[0,0]
    overdue_tasks = query_df("SELECT COUNT(*) FROM tasks WHERE status NOT IN ('مكتمل','ملغي') AND report_date < date('now','-3 days')").iloc[0,0]
    emergency_tasks = query_df("SELECT COUNT(*) FROM tasks WHERE priority='طوارئ قصوى' AND status NOT IN ('مكتمل','ملغي')").iloc[0,0]
    completed_tasks = query_df("SELECT COUNT(*) FROM tasks WHERE status='مكتمل'").iloc[0,0]

    total_buildings = query_df("SELECT COUNT(*) FROM buildings").iloc[0,0]
    active_contracts = query_df("SELECT COUNT(*) FROM contracts WHERE status='ساري'").iloc[0,0]
    expiring_contracts = query_df("SELECT COUNT(*) FROM contracts WHERE end_date BETWEEN date('now') AND date('now','+30 days')").iloc[0,0]

    inv_val = query_df("SELECT COALESCE(SUM(quantity * avg_cost),0) FROM materials").iloc[0,0]
    low_stock_count = query_df("SELECT COUNT(*) FROM materials WHERE quantity <= min_quantity").iloc[0,0]

    rev = query_df("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='إيراد'").iloc[0,0]
    exp = query_df("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='مصروف'").iloc[0,0]

    # Row 1 metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("إجمالي أوامر الصيانة", total_tasks)
    c2.metric("أوامر مفتوحة", open_tasks)
    c3.metric("أوامر متأخرة", overdue_tasks)
    c4.metric("طوارئ نشطة", emergency_tasks)
    c5.metric("أوامر مكتملة", completed_tasks)

    # Row 2 metrics
    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("إجمالي المباني", total_buildings)
    c7.metric("العقود السارية", active_contracts)
    c8.metric("عقود تنتهي قريباً", expiring_contracts)
    c9.metric("قيمة المخزون (ر.ق)", f"{inv_val:,.2f}")
    c10.metric("أصناف منخفضة", low_stock_count)

    # Row 3 metrics
    c11, c12, c13 = st.columns(3)
    c11.metric("إجمالي الإيرادات", f"{rev:,.2f} ر.ق")
    c12.metric("إجمالي المصروفات", f"{exp:,.2f} ر.ق")
    c13.metric("صافي الربح", f"{rev-exp:,.2f} ر.ق")

    st.markdown("---")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("### 🚨 بلاغات الطوارئ النشطة")
        emer_df = query_df("""
            SELECT ticket_no AS "رقم البلاغ", system_type AS "النظام", priority AS "الأولوية", status AS "الحالة"
            FROM tasks WHERE priority='طوارئ قصوى' AND status NOT IN ('مكتمل','ملغي') ORDER BY id DESC
        """)
        st.dataframe(emer_df, use_container_width=True)

    with c_right:
        st.markdown("### ⚠️ تنبيهات انخفاض المخزون")
        low_df = query_df("""
            SELECT item_code AS "الكود", arabic_name AS "الصنف", quantity AS "الرصيد", min_quantity AS "الحد الأدنى"
            FROM materials WHERE quantity <= min_quantity ORDER BY quantity ASC
        """)
        st.dataframe(low_df, use_container_width=True)


# ============================================================
# 2. Work Orders (أوامر الصيانة والبلاغات)
# ============================================================
elif menu == "🛠️ أوامر الصيانة والبلاغات":
    st.markdown("## 🛠️ إدارة أوامر الصيانة والبلاغات الفنية")

    tab1, tab2 = st.tabs(["➕ إصدار أمر صيانة / بلاغ جديد", "📋 سجل ومتابعة أوامر الصيانة"])

    with tab1:
        buildings_list = query_df("SELECT id, name FROM buildings")
        emps_list = query_df("SELECT id, name, role FROM employees")

        b_map = {row['name']: row['id'] for _, row in buildings_list.iterrows()} if not buildings_list.empty else {}
        e_map = {f"{row['name']} ({row['role']})": row['id'] for _, row in emps_list.iterrows()} if not emps_list.empty else {}

        c1, c2 = st.columns(2)
        with c1:
            ticket_no = f"TICK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.info(f"رقم البلاغ التلقائي: **{ticket_no}**")

            building_name = st.selectbox("المبنى / المشروع *", list(b_map.keys()) if b_map else ["لا توجد مباني مضافة"])
            building_id = b_map.get(building_name) if b_map else None

            location = st.text_input("الموقع / الطابق")
            room = st.text_input("رقم الغرفة / المساحة")
            system_type = st.selectbox("النظام المتعطل / التخصص", MAINTENANCE_SPECIALTIES)
            job_type = st.selectbox("نوع أمر العمل", [
                "بلاغ عطل", "صيانة وقائية (PM)", "صيانة تصحيحية (CM)",
                "طوارئ", "فحص دوري", "تركيب واستبدال"
            ])
            priority = st.selectbox("الأولوية", ["عادي", "متوسط", "عالي", "طوارئ قصوى"])

        with c2:
            tech_label = st.selectbox("الفني المسؤول", list(e_map.keys()) if e_map else ["لا يوجد موظفون"])
            technician_id = e_map.get(tech_label) if e_map else None

            sup_label = st.selectbox("المشرف المسؤول", list(e_map.keys()) if e_map else ["لا يوجد موظفون"])
            supervisor_id = e_map.get(sup_label) if e_map else None

            report_date = st.date_input("تاريخ البلاغ", value=date.today())
            assignment_date = st.date_input("تاريخ التعيين", value=date.today())
            sla_hours = st.number_input("مدة الاستجابة SLA (بالساعات)", min_value=1.0, value=24.0)
            status = st.selectbox("حالة الأمر", ["جديد", "تم التعيين", "قيد العمل", "بانتظار قطع غيار", "مكتمل", "ملغي"])
            estimated_cost = st.number_input("التكلفة التقديرية (ر.ق)", min_value=0.0, format="%.2f")
            actual_cost = st.number_input("التكلفة الفعلية (ر.ق)", min_value=0.0, format="%.2f")

        description = st.text_area("وصف عطل الأجهزة / الأعمال المطلوبة *", height=90)
        materials_used = st.text_area("المواد وقطع الغيار المستخدمة", placeholder="مثال: 2 فلتر هواء، 1 قاطع كهربائي...")
        notes = st.text_area("ملاحظات فنية إضافية")

        if st.button("💾 حفظ وإصدار أمر الصيانة", use_container_width=True):
            if building_id and description.strip():
                execute("""
                INSERT INTO tasks
                (ticket_no, building_id, location, room, system_type, job_type, priority,
                 description, technician_id, supervisor_id, report_date, assignment_date,
                 sla_hours, estimated_cost, actual_cost, status, materials_used, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    ticket_no, building_id, location, room, system_type, job_type, priority,
                    description, technician_id, supervisor_id, report_date.isoformat(),
                    assignment_date.isoformat(), sla_hours, estimated_cost, actual_cost,
                    status, materials_used, notes
                ))
                st.success(f"تم إصدار أمر الصيانة بنجاح برقم: {ticket_no}")
            else:
                st.error("يرجى اختيار المبنى وإدخال وصف العطل على الأقل.")

    with tab2:
        st.markdown("### 🔍 بحث وتصفية متقدمة لأوامر الصيانة")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            search_text = st.text_input("بحث برقم البلاغ أو الوصف")
        with sc2:
            status_filter = st.selectbox("تصفية بالحالة", ["الكل", "جديد", "تم التعيين", "قيد العمل", "بانتظار قطع غيار", "مكتمل", "ملغي"])
        with sc3:
            priority_filter = st.selectbox("تصفية بالأولوية", ["الكل", "عادي", "متوسط", "عالي", "طوارئ قصوى"])

        query_sql = """
            SELECT t.id AS "م", t.ticket_no AS "رقم البلاغ", b.name AS "المبنى",
                   t.system_type AS "النظام", t.job_type AS "نوع العمل",
                   t.priority AS "الأولوية", t.status AS "الحالة",
                   t.report_date AS "تاريخ البلاغ", t.description AS "الوصف"
            FROM tasks t
            LEFT JOIN buildings b ON t.building_id = b.id
            WHERE 1=1
        """
        params = []
        if search_text:
            query_sql += " AND (t.ticket_no LIKE ? OR t.description LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        if status_filter != "الكل":
            query_sql += " AND t.status = ?"
            params.append(status_filter)
        if priority_filter != "الكل":
            query_sql += " AND t.priority = ?"
            params.append(priority_filter)

        query_sql += " ORDER BY t.id DESC"
        tasks_df = query_df(query_sql, tuple(params))
        st.dataframe(tasks_df, use_container_width=True, height=500)
        if not tasks_df.empty:
            csv_download(tasks_df, "tictac_work_orders.csv")


# ============================================================
# 3. Materials & Spare Parts (قاعدة المواد وقطع الغيار)
# ============================================================
elif menu == "📦 المواد وقطع الغيار":
    st.markdown("## 📦 قاعدة بيانات المواد وقطع الغيار الشاملة")

    tab1, tab2 = st.tabs(["➕ إضافة مادة جديدة", "📋 المخزون الحالي والبحث"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            item_code = st.text_input("كود المادة الداخلي *")
            barcode_sku = st.text_input("Barcode / SKU")
            arabic_name = st.text_input("الاسم العربي للمادة *")
            english_name = st.text_input("الاسم الإنجليزي للمادة")
            category = st.selectbox("التصنيف الرئيسي", MATERIAL_CATEGORIES)
            unit = st.selectbox("وحدة القياس", UNITS)
            quantity = st.number_input("الرصيد الحالي", min_value=0.0, value=0.0)
            min_quantity = st.number_input("الحد الأدنى للمخزون", min_value=0.0, value=0.0)
            reorder_point = st.number_input("حد إعادة الطلب", min_value=0.0, value=0.0)
            purchase_price = st.number_input("سعر الشراء (ر.ق)", min_value=0.0, format="%.2f")

        with c2:
            avg_cost = st.number_input("متوسط التكلفة (ر.ق)", min_value=0.0, format="%.2f")
            supplier = st.text_input("المورد الأساسي")
            storage_location = st.text_input("موقع التخزين / المستودع")
            shelf_no = st.text_input("رقم الرف")
            manufacturer = st.text_input("الشركة المصنعة")
            part_no = st.text_input("Part Number")
            model = st.text_input("الموديل")
            serial_no = st.text_input("Serial Number (عند الحاجة)")
            warranty_date = st.date_input("تاريخ انتهاء الضمان", value=date.today())

        notes = st.text_area("ملاحظات إضافية عن الصنف")

        if st.button("💾 حفظ الصنف في قاعدة المواد", use_container_width=True):
            if item_code.strip() and arabic_name.strip():
                try:
                    execute("""
                    INSERT INTO materials
                    (item_code, barcode_sku, arabic_name, english_name, category, unit,
                     quantity, min_quantity, reorder_point, purchase_price, avg_cost,
                     supplier, storage_location, shelf_no, manufacturer, part_no, model,
                     serial_no, warranty_date, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        item_code, barcode_sku, arabic_name, english_name, category, unit,
                        quantity, min_quantity, reorder_point, purchase_price, avg_cost,
                        supplier, storage_location, shelf_no, manufacturer, part_no, model,
                        serial_no, warranty_date.isoformat(), notes
                    ))
                    st.success("تمت إضافة الصنف بنجاح.")
                except sqlite3.IntegrityError:
                    st.error("كود المادة (Item Code) موجود مسبقاً، يرجى إدخال كود فريد.")
            else:
                st.error("يرجى إدخال كود المادة والاسم العربي على الأقل.")

    with tab2:
        m_search = st.text_input("🔎 بحث عن مادة (بالاسم أو الكود أو الباركود)")
        sql_m = "SELECT * FROM materials WHERE 1=1"
        params_m = []
        if m_search:
            sql_m += " AND (item_code LIKE ? OR arabic_name LIKE ? OR barcode_sku LIKE ? OR part_no LIKE ?)"
            params_m.extend([f"%{m_search}%", f"%{m_search}%", f"%{m_search}%", f"%{m_search}%"])
        sql_m += " ORDER BY id DESC"

        materials_df = query_df(sql_m, tuple(params_m))
        st.dataframe(materials_df, use_container_width=True, height=500)
        if not materials_df.empty:
            csv_download(materials_df, "tictac_materials_database.csv")


# ============================================================
# 4. Inventory Transactions (حركة المخزون)
# ============================================================
elif menu == "🔄 حركة المخزون":
    st.markdown("## 🔄 إدارة حركات المخزون والمستودعات")

    tab1, tab2 = st.tabs(["➕ تسجيل حركة مخزنية", "📋 سجل الحركات بالكامل"])

    with tab1:
        m_list = query_df("SELECT id, item_code, arabic_name, quantity, unit FROM materials")
        m_map = {f"{row['item_code']} - {row['arabic_name']} (الرصيد: {row['quantity']} {row['unit']})": row['id'] for _, row in m_list.iterrows()} if not m_list.empty else {}

        tasks_list = query_df("SELECT id, ticket_no FROM tasks")
        t_map = {row['ticket_no']: row['id'] for _, row in tasks_list.iterrows()} if not tasks_list.empty else {}

        c1, c2 = st.columns(2)
        with c1:
            selected_m = st.selectbox("اختر الصنف *", list(m_map.keys()) if m_map else ["لا توجد مواد"])
            material_id = m_map.get(selected_m) if m_map else None

            transaction_type = st.selectbox("نوع الحركة", [
                "إضافة رصيد / شراء", "صرف لأمر صيانة", "مرتجع للمستودع",
                "تسوية زيادة", "تسوية نقص", "تحويل بين المستودعات"
            ])
            quantity = st.number_input("الكمية *", min_value=0.01, value=1.0)
            unit_cost = st.number_input("سعر الوحدة (ر.ق)", min_value=0.0, format="%.2f")

        with c2:
            reference = st.text_input("رقم المرجع / أمر الشراء / الفاتورة")
            t_sel = st.selectbox("ربط بأمر صيانة (اختياري)", ["بدون ربط"] + list(t_map.keys()))
            task_id = t_map.get(t_sel) if t_sel != "بدون ربط" else None

            warehouse_from = st.text_input("المستودع المصدر (في حال التحويل)")
            warehouse_to = st.text_input("المستودع المستلم / الحالي")
            trans_date = st.date_input("تاريخ الحركة", value=date.today())

        trans_notes = st.text_area("ملاحظات الحركة")

        if st.button("🔄 تنفيذ وتسجيل الحركة المخزنية", use_container_width=True):
            if material_id and quantity > 0:
                current_qty = query_df("SELECT quantity FROM materials WHERE id=?", (material_id,)).iloc[0,0]

                add_types = ["إضافة رصيد / شراء", "مرتجع للمستودع", "تسوية زيادة"]
                ded_types = ["صرف لأمر صيانة", "تسوية نقص"]

                new_qty = current_qty
                if transaction_type in add_types:
                    new_qty += quantity
                elif transaction_type in ded_types:
                    new_qty -= quantity

                if new_qty < 0:
                    st.error("الكمية المراد صرفها أكبر من الرصيد المتاح في المخزن!")
                else:
                    execute("UPDATE materials SET quantity = ? WHERE id = ?", (new_qty, material_id))
                    execute("""
                    INSERT INTO material_transactions
                    (material_id, transaction_type, quantity, unit_cost, reference, task_id,
                     warehouse_from, warehouse_to, date, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (
                        material_id, transaction_type, quantity, unit_cost, reference, task_id,
                        warehouse_from, warehouse_to, trans_date.isoformat(), trans_notes
                    ))
                    st.success(f"تم تنفيذ الحركة بنجاح. الرصيد الجديد للصنف: {new_qty}")
            else:
                st.error("يرجى اختيار المادة وإدخال كمية صحيحة.")

    with tab2:
        st.markdown("### 📋 سجل حركات المخزون")
        trans_df = query_df("""
            SELECT mt.id AS "م", m.arabic_name AS "المادة", mt.transaction_type AS "نوع الحركة",
                   mt.quantity AS "الكمية", mt.unit_cost AS "السعر", mt.reference AS "المرجع",
                   mt.date AS "التاريخ", mt.notes AS "ملاحظات"
            FROM material_transactions mt
            LEFT JOIN materials m ON mt.material_id = m.id
            ORDER BY mt.id DESC
        """)
        st.dataframe(trans_df, use_container_width=True, height=500)
        if not trans_df.empty:
            csv_download(trans_df, "tictac_inventory_transactions.csv")


# ============================================================
# 5. Purchases (المشتريات PR / PO)
# ============================================================
elif menu == "🛒 المشتريات":
    st.markdown("## 🛒 إدارة المشتريات (طلبات الشراء وأوامر الشراء PO)")

    tab1, tab2 = st.tabs(["➕ تسجيل أمر شراء جديد PO", "📋 سجل المشتريات"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            po_no = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.info(f"رقم أمر الشراء التلقائي: **{po_no}**")

            item_name = st.text_input("اسم الصنف أو الخدمة المطلوبة *")
            category = st.selectbox("قسم المشتريات", MATERIAL_CATEGORIES)
            quantity = st.number_input("الكمية", min_value=0.01, value=1.0)
            unit = st.selectbox("الوحدة", UNITS)
            price = st.number_input("سعر الوحدة (ر.ق)", min_value=0.0, format="%.2f")

        with c2:
            tax = st.number_input("قيمة الضريبة (ر.ق)", min_value=0.0, format="%.2f")
            supplier = st.text_input("المورد *")
            invoice_no = st.text_input("رقم الفاتورة المرتبطة")
            p_date = st.date_input("تاريخ الشراء", value=date.today())
            status = st.selectbox("حالة الطلب", ["مكتمل", "بانتظار الموافقة", "قيد الشحن", "ملغي"])

        notes = st.text_area("ملاحظات الشراء")

        if st.button("💾 حفظ أمر الشراء وربطه بالمالية", use_container_width=True):
            if item_name.strip() and supplier.strip():
                total_amount = (quantity * price) + tax
                execute("""
                INSERT INTO purchases
                (po_no, item_name, category, quantity, unit, price, tax, total_amount,
                 supplier, invoice_no, date, status, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    po_no, item_name, category, quantity, unit, price, tax, total_amount,
                    supplier, invoice_no, p_date.isoformat(), status, notes
                ))
                # Auto record in finance as expense
                execute("""
                INSERT INTO finance (type, category, description, amount, date, reference)
                VALUES ('مصروف', 'شراء مواد وقطع غيار', ?, ?, ?, ?)
                """, (f"أمر شراء {po_no} - {item_name}", total_amount, p_date.isoformat(), po_no))

                st.success(f"تم حفظ أمر الشراء برقم {po_no} وإضافته للمصاريف المالية بنجاح.")
            else:
                st.error("يرجى إدخال اسم الصنف والمورد.")

    with tab2:
        purchases_df = query_df("""
            SELECT id AS "م", po_no AS "رقم PO", item_name AS "الصنف",
                   quantity AS "الكمية", total_amount AS "الإجمالي (ر.ق)",
                   supplier AS "المورد", invoice_no AS "الفاتورة", date AS "التاريخ", status AS "الحالة"
            FROM purchases ORDER BY id DESC
        """)
        st.dataframe(purchases_df, use_container_width=True, height=500)
        if not purchases_df.empty:
            csv_download(purchases_df, "tictac_purchases.csv")


# ============================================================
# 6. Buildings & Clients (المباني والعملاء)
# ============================================================
elif menu == "🏢 المباني والعملاء":
    st.markdown("## 🏢 إدارة المباني والعملاء والمرافق")

    tab1, tab2 = st.tabs(["➕ إضافة مبنى جديد", "📋 قائمة المباني"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("اسم المبنى / المشروع *")
            client = st.text_input("اسم العميل / المالك *")
            address = st.text_input("العنوان التفصيلي / المنطقة")
            contact_person = st.text_input("مسؤول التواصل بالموقع")
        with c2:
            contact_phone = st.text_input("هاتف المسؤول")
            floors_count = st.number_input("عدد الطوابق", min_value=1, value=1)
            systems_installed = st.text_area("الأنظمة الموجودة بالمبنى", placeholder="تكييف مركزى، إنذار حريق، مصاعد، BMS...")

        notes = st.text_area("ملاحظات المبنى")

        if st.button("💾 حفظ بيانات المبنى", use_container_width=True):
            if name.strip() and client.strip():
                execute("""
                INSERT INTO buildings
                (name, client, address, contact_person, contact_phone, floors_count, systems_installed, notes)
                VALUES (?,?,?,?,?,?,?,?)
                """, (name, client, address, contact_person, contact_phone, floors_count, systems_installed, notes))
                st.success("تم حفظ المبنى بنجاح.")
            else:
                st.error("يرجى إدخال اسم المبنى والعميل.")

    with tab2:
        b_df = query_df("""
            SELECT id AS "م", name AS "المبنى", client AS "العميل",
                   address AS "العنوان", contact_person AS "المسؤول",
                   contact_phone AS "الهاتف", floors_count AS "الطوابق"
            FROM buildings ORDER BY id DESC
        """)
        st.dataframe(b_df, use_container_width=True, height=500)
        if not b_df.empty:
            csv_download(b_df, "tictac_buildings.csv")


# ============================================================
# 7. Contracts (العقود)
# ============================================================
elif menu == "📄 العقود":
    st.markdown("## 📄 إدارة عقود الصيانة والتشغيل")

    tab1, tab2 = st.tabs(["➕ تسجيل عقد جديد", "📋 قائمة العقود والتنبيهات"])

    with tab1:
        b_list = query_df("SELECT id, name FROM buildings")
        b_map = {row['name']: row['id'] for _, row in b_list.iterrows()} if not b_list.empty else {}

        c1, c2 = st.columns(2)
        with c1:
            building_name = st.selectbox("المبنى المرتبط بالعقد", list(b_map.keys()) if b_map else ["لا توجد مباني"])
            building_id = b_map.get(building_name) if b_map else None

            contract_no = st.text_input("رقم العقد *")
            contract_type = st.selectbox("نوع العقد", ["عقد صيانة شاملة (Comprehensive)", "عقد صيانة وقائية", "إدارة مرافق FM", "أخرى"])
            value = st.number_input("قيمة العقد (ر.ق)", min_value=0.0, format="%.2f")

        with c2:
            start_date = st.date_input("تاريخ بداية العقد", value=date.today())
            end_date = st.date_input("تاريخ انتهاء العقد", value=date.today() + timedelta(days=365))
            status = st.selectbox("حالة العقد", ["ساري", "منتهي", "قيد التجديد", "ملغي"])

        services_included = st.text_area("الخدمات والأنظمة المشمولة بالعقد")
        notes = st.text_area("ملاحظات العقد")

        if st.button("💾 حفظ العقد", use_container_width=True):
            if contract_no.strip():
                try:
                    c_id = execute("""
                    INSERT INTO contracts
                    (building_id, contract_no, contract_type, value, services_included, start_date, end_date, status, notes)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """, (building_id, contract_no, contract_type, value, services_included, start_date.isoformat(), end_date.isoformat(), status, notes))

                    # Auto record revenue
                    execute("""
                    INSERT INTO finance (type, category, description, amount, date, reference, contract_id)
                    VALUES ('إيراد', 'عقود صيانة', ?, ?, ?, ?, ?)
                    """, (f"عقد صيانة رقم {contract_no}", value, start_date.isoformat(), contract_no, c_id))

                    st.success("تم حفظ العقد وإضافة إيراداته المالية بنجاح.")
                except sqlite3.IntegrityError:
                    st.error("رقم العقد موجود مسبقاً.")
            else:
                st.error("يرجى إدخال رقم العقد.")

    with tab2:
        st.markdown("### 🔔 تنبيهات العقود التي ستنتهي خلال 30 يوماً")
        exp_df = query_df("""
            SELECT c.contract_no AS "رقم العقد", b.name AS "المبنى", c.end_date AS "تاريخ الانتهاء", c.status AS "الحالة"
            FROM contracts c LEFT JOIN buildings b ON c.building_id = b.id
            WHERE c.end_date BETWEEN date('now') AND date('now','+30 days')
        """)
        st.dataframe(exp_df, use_container_width=True)

        st.markdown("### 📋 كافة العقود المسجلة")
        contracts_df = query_df("""
            SELECT c.id AS "م", c.contract_no AS "رقم العقد", b.name AS "المبنى",
                   c.contract_type AS "النوع", c.value AS "القيمة (ر.ق)",
                   c.start_date AS "البداية", c.end_date AS "النهاية", c.status AS "الحالة"
            FROM contracts c LEFT JOIN buildings b ON c.building_id = b.id
            ORDER BY c.id DESC
        """)
        st.dataframe(contracts_df, use_container_width=True, height=400)
        if not contracts_df.empty:
            csv_download(contracts_df, "tictac_contracts.csv")


# ============================================================
# 8. Employees (الموظفون)
# ============================================================
elif menu == "👥 الموظفون":
    st.markdown("## 👥 إدارة الموظفين والفنيين والمهندسين")

    tab1, tab2 = st.tabs(["➕ إضافة موظف جديد", "📋 قائمة الموظفين"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("اسم الموظف الرباعي *")
            qatari_id = st.text_input("رقم البطاقة الشخصية / الإقامة")
            phone = st.text_input("رقم الهاتف")
            role = st.selectbox("الوظيفة / المسمى", JOB_ROLES)
            department = st.selectbox("القسم", ["الصيانة التشغيلية", "الفني والمهندسون", "السلامة HSE", "المستودعات", "الإدارة والحسابات"])
        with c2:
            hire_date = st.date_input("تاريخ التعيين", value=date.today())
            salary = st.number_input("الراتب الأساسي (ر.ق)", min_value=0.0, format="%.2f")
            status = st.selectbox("حالة الموظف", ["على رأس العمل", "إجازة", "موقوف", "منتهي الخدمة"])
            skills = st.text_input("المهارات والتخصصات الدقيقة", placeholder="فني تكييف مركزى، كهرباء ضغط عالي...")

        notes = st.text_area("ملاحظات الموظف")

        if st.button("💾 حفظ بيانات الموظف", use_container_width=True):
            if name.strip():
                execute("""
                INSERT INTO employees
                (name, qatari_id, phone, role, department, hire_date, salary, status, skills, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (name, qatari_id, phone, role, department, hire_date.isoformat(), salary, status, skills, notes))
                st.success("تمت إضافة الموظف بنجاح.")
            else:
                st.error("يرجى إدخال اسم الموظف.")

    with tab2:
        emp_df = query_df("""
            SELECT id AS "م", name AS "الموظف", role AS "الوظيفة",
                   department AS "القسم", phone AS "الهاتف", salary AS "الراتب", status AS "الحالة"
            FROM employees ORDER BY id DESC
        """)
        st.dataframe(emp_df, use_container_width=True, height=500)
        if not emp_df.empty:
            csv_download(emp_df, "tictac_employees.csv")


# ============================================================
# 9. Attendance (الحضور والدوام)
# ============================================================
elif menu == "🕘 الحضور والدوام":
    st.markdown("## 🕘 تسجيل ومتابعة الحضور والغياب وساعات العمل")

    tab1, tab2 = st.tabs(["➕ تسجيل الحضور اليومي", "📋 تقرير الحضور"])

    with tab1:
        e_list = query_df("SELECT id, name, role FROM employees WHERE status='على رأس العمل'")
        e_map = {f"{row['name']} ({row['role']})": row['id'] for _, row in e_list.iterrows()} if not e_list.empty else {}

        c1, c2 = st.columns(2)
        with c1:
            selected_emp = st.selectbox("اختر الموظف", list(e_map.keys()) if e_map else ["لا توجد موظفون"])
            emp_id = e_map.get(selected_emp) if e_map else None
            att_status = st.selectbox("حالة الحضور", ["حاضر", "غائب", "إجازة", "مرضي", "مهمة خارجية", "راحة", "تأخير"])
        with c2:
            att_date = st.date_input("تاريخ اليوم", value=date.today())
            work_hours = st.number_input("ساعات العمل", min_value=0.0, max_value=24.0, value=8.0)

        att_notes = st.text_input("ملاحظات الدوام")

        if st.button("💾 تسجيل الحضور", use_container_width=True):
            if emp_id:
                try:
                    execute("""
                    INSERT INTO attendance (emp_id, status, date, work_hours, notes)
                    VALUES (?,?,?,?,?)
                    """, (emp_id, att_status, att_date.isoformat(), work_hours, att_notes))
                    st.success("تم تسجيل الحضور بنجاح.")
                except sqlite3.IntegrityError:
                    st.error("تم تسجيل حضور هذا الموظف مسبقاً لهذا اليوم. يمكنك التعديل عند الحاجة.")
            else:
                st.error("يرجى اختيار موظف صحيح.")

    with tab2:
        att_df = query_df("""
            SELECT a.id AS "م", e.name AS "الموظف", a.status AS "الحالة",
                   a.date AS "التاريخ", a.work_hours AS "ساعات العمل", a.notes AS "ملاحظات"
            FROM attendance a
            LEFT JOIN employees e ON a.emp_id = e.id
            ORDER BY a.date DESC, a.id DESC
        """)
        st.dataframe(att_df, use_container_width=True, height=500)
        if not att_df.empty:
            csv_download(att_df, "tictac_attendance.csv")


# ============================================================
# 10. Finance (الحسابات والمالية)
# ============================================================
elif menu == "💰 الحسابات والمالية":
    st.markdown("## 💰 الإدارة المالية والحسابات")

    tab1, tab2 = st.tabs(["➕ إضافة معاملة مالية", "📋 السجل المالي والربحية"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            ftype = st.selectbox("نوع المعاملة", ["إيراد", "مصروف"])
            fcat = st.selectbox("التصنيف", [
                "عقود صيانة", "إصلاحات طارئة", "رواتب وأجور", "شراء مواد وقطع غيار",
                "مصاريف تشغيلية", "مصاريف المركبات", "معدات وأدوات", "أخرى"
            ])
            description = st.text_input("بيان المعاملة *")
        with c2:
            amount = st.number_input("المبلغ (ر.ق)", min_value=0.0, format="%.2f")
            fdate = st.date_input("تاريخ المعاملة", value=date.today())
            reference = st.text_input("رقم المرجع / الفاتورة")

        if st.button("💾 حفظ المعاملة المالية", use_container_width=True):
            if description.strip() and amount > 0:
                execute("""
                INSERT INTO finance (type, category, description, amount, date, reference)
                VALUES (?,?,?,?,?,?)
                """, (ftype, fcat, description, amount, fdate.isoformat(), reference))
                st.success("تم حفظ المعاملة المالية بنجاح.")
            else:
                st.error("يرجى إدخال البيان والمبلغ.")

    with tab2:
        rev_total = query_df("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='إيراد'").iloc[0,0]
        exp_total = query_df("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='مصروف'").iloc[0,0]

        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي الإيرادات", f"{rev_total:,.2f} ر.ق")
        col2.metric("إجمالي المصروفات", f"{exp_total:,.2f} ر.ق")
        col3.metric("صافي الربح", f"{rev_total - exp_total:,.2f} ر.ق")

        st.markdown("### 📋 سجل المعاملات المالية")
        fin_df = query_df("""
            SELECT id AS "م", type AS "النوع", category AS "التصنيف",
                   description AS "البيان", amount AS "المبلغ (ر.ق)", date AS "التاريخ", reference AS "المرجع"
            FROM finance ORDER BY date DESC, id DESC
        """)
        st.dataframe(fin_df, use_container_width=True, height=400)
        if not fin_df.empty:
            csv_download(fin_df, "tictac_finance.csv")


# ============================================================
# 11. Reports (التقارير الشاملة)
# ============================================================
elif menu == "📊 التقارير الشاملة":
    st.markdown("## 📊 التقارير الشاملة والتصدير")

    report_type = st.selectbox("اختر التقرير المطلوب:", [
        "تقرير أوامر الصيانة الشامل",
        "تقرير المواد والمخزون",
        "تقرير حركات المخزون",
        "تقرير المشتريات",
        "تقرير العقود",
        "تقرير الموظفين",
        "تقرير الحضور والغياب",
        "تقرير الإيرادات والمصروفات والربحية"
    ])

    if report_type == "تقرير أوامر الصيانة الشامل":
        df = query_df("SELECT * FROM tasks ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_tasks.csv")

    elif report_type == "تقرير المواد والمخزون":
        df = query_df("SELECT * FROM materials ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_materials.csv")

    elif report_type == "تقرير حركات المخزون":
        df = query_df("SELECT * FROM material_transactions ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_inventory_trans.csv")

    elif report_type == "تقرير المشتريات":
        df = query_df("SELECT * FROM purchases ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_purchases.csv")

    elif report_type == "تقرير العقود":
        df = query_df("SELECT * FROM contracts ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_contracts.csv")

    elif report_type == "تقرير الموظفين":
        df = query_df("SELECT * FROM employees ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_employees.csv")

    elif report_type == "تقرير الحضور والغياب":
        df = query_df("SELECT * FROM attendance ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_attendance.csv")

    elif report_type == "تقرير الإيرادات والمصروفات والربحية":
        df = query_df("SELECT * FROM finance ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if not df.empty: csv_download(df, "tictac_report_finance.csv")

st.sidebar.markdown("---")
st.sidebar.caption("TIC TAC Building Maintenance Platform")
st.sidebar.caption("Qatar • Professional Edition v2.0")
