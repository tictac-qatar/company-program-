import base64
import hashlib
import hmac
import io
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

APP_DIR = Path(__file__).resolve().parent
DB_FILE = str(APP_DIR / "tictac_pro_v5.db")
LOGO_FILE = APP_DIR / "IMG_7478.JPG"
SESSION_SECRET = os.environ.get("TICTAC_SESSION_SECRET", "change-this-secret-in-production")

NAVY = "#17324D"
NAVY_DARK = "#0E2236"
COPPER = "#A96343"
COPPER_LIGHT = "#C98A68"
CREAM = "#F7F3EC"
INK = "#17212B"
MUTED = "#667085"
WHITE = "#FFFFFF"

SPECIALTIES = ["الكهرباء", "HVAC والتكييف", "السباكة", "الصرف الصحي", "مضخات المياه", "مكافحة الحريق", "إنذار الحريق", "المولدات", "UPS", "المصاعد", "BMS", "CCTV", "Access Control", "الشبكات والاتصالات", "الأبواب والأقفال", "نجارة", "ألومنيوم وزجاج", "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية", "حدادة ولحام", "معدات مطابخ", "نظافة", "HSE", "أخرى"]
ROLES = ["مدير النظام", "مدير العمليات التشغيلية", "مدير العقود والعملاء", "مشرف صيانة ميدانية", "مهندس دعم فني", "فني كهرباء", "فني تكييف HVAC", "فني سباكة", "فني مكافحة حريق", "فني مصاعد", "فني مولدات", "فني BMS", "فني CCTV وأمن", "فني شبكات", "فني مدني", "مسؤول سلامة HSE", "أمين مستودع", "محاسب", "مسؤول مشتريات", "مسؤول موارد بشرية", "سائق", "فني صيانة عامة"]
DEPARTMENTS = ["الإدارة", "الoperations التشغيلية", "الفنيون والمهندسون", "السلامة HSE", "المستودعات", "المشتريات", "المالية والحسابات", "خدمة العملاء والعقود"]
CATEGORIES = ["مواد كهربائية", "مواد تكييف HVAC", "مواد سباكة وصرف", "مضخات وقطع غيار", "مكافحة وإنذار الحريق", "مولدات و UPS", "مصاعد", "BMS وتحكم", "CCTV وأمن", "شبكات واتصالات", "نجارة وأبواب", "ألومنيوم وزجاج", "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية وبناء", "حدادة ولحام", "معدات مطابخ", "مواد نظافة", "معدات سلامة PPE", "قطع غيار عامة", "أخرى"]
UNITS = ["قطعة", "متر", "متر مربع", "متر مكعب", "كيلو", "لتر", "جالون", "علبة", "كرتون", "رول", "طقم", "وحدة"]
STATUSES = ["جديد", "تم التعميد / الإسناد", "قيد التنفيذ بالموقع", "بانتظار قطع غيار", "مكتمل ومسلم للعميل", "ملغي"]

FINANCE_CATEGORIES = {
    "إيراد": [
        "إيرادات عقود الصيانة الدورية السنوية",
        "إيرادات فواتير بلاغات الطوارئ (Call-out)",
        "إيرادات أعمال الإصلاح التصحيحي الإضافية",
        "إيرادات عقود إدارة المرافق المتكاملة (FM)",
        "إيرادات توريد وتركيب معدات جديدة للعميل",
        "أرباح تعويضات تأمين أو غرامات تشغيلية",
        "إيرادات أخرى متفرقة"
    ],
    "مصروف": [
        "رواتب وأجور الفنيين والمهندسين الميدانيين",
        "مشتريات مواد وقطع غيار لمشاريع العملاء",
        "أجور مقاولي الباطن والخدمات المتخصصة",
        "مصاريف النقل والوقود لسيارات الصيانة",
        "إيجارات المخازن ومقرات التشغيل",
        "رسوم تراخيص واختبارات فحص الأنظمة المعتمدة",
        "صيانة أدوات وعدد الورش والمعدات الثقيلة",
        "رسوم استخراج تصاريح العمل ومعدات السلامة (PPE)",
        "فواتير المرافق العامة (كهرباء ومياه وصيانة مقرات)",
        "مصاريف إدارية وعمومية",
        "أخرى"
    ]
}

MAIN_MENU = ["لوحة التحكم", "طلبات الخدمة وأوامر الصيانة", "الأصول والمعدات", "المواد وقطع الغيار", "حركة المخزون", "المشتريات", "مواقع العملاء", "عقود الصيانة للعملاء", "الموظفون", "الحضور والدوام", "الحسابات والفواتير", "التقارير"]
MENU_AREAS = {"لوحة التحكم":"dashboard", "طلبات الخدمة وأوامر الصيانة":"maintenance", "الأصول والمعدات":"maintenance", "المواد وقطع الغيار":"inventory", "حركة المخزون":"inventory", "المشتريات":"purchases", "مواقع العملاء":"buildings", "عقود الصيانة للعملاء":"contracts", "الموظفون":"hr", "الحضور والدوام":"hr", "الحسابات والفواتير":"finance", "التقارير":"reports"}
LEGACY_PERMISSIONS = {"مدير العقود والعملاء": ["dashboard", "maintenance", "buildings", "contracts", "reports"], "مشرف صيانة ميدانية": ["dashboard", "maintenance", "reports"], "مهندس دعم فني": ["dashboard", "maintenance", "reports"], "مسؤول مشتريات": ["dashboard", "purchases", "inventory", "reports"], "أمين مستودع": ["dashboard", "inventory", "purchases", "reports"], "محاسب": ["dashboard", "finance", "contracts", "reports"], "مسؤول موارد بشرية": ["dashboard", "hr", "reports"]}

st.set_page_config(page_title="TIC TAC | نظام إدارة خدمات الصيانة الخارجية", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');
:root {{ --navy:{NAVY}; --navy-dark:{NAVY_DARK}; --copper:{COPPER}; --cream:{CREAM}; --ink:{INK}; }}
*, html, body, [class*="css"] {{ font-family:'Cairo', Tahoma, Arial, sans-serif !important; }}
.stApp {{ background:linear-gradient(135deg, #fff 0%, {CREAM} 100%); color:{INK}; direction:rtl; font-family:'Cairo', sans-serif !important; }}
.block-container {{ max-width:1500px; padding:1.4rem clamp(.7rem, 3vw, 3rem) 3rem; font-family:'Cairo', sans-serif !important; }}
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg, {NAVY_DARK}, {NAVY}); border-left:4px solid {COPPER}; font-family:'Cairo', sans-serif !important; }}
section[data-testid="stSidebar"] * {{ color:#fff !important; font-family:'Cairo', sans-serif !important; }}
[data-testid="stHeader"] {{ background:transparent; }}
.logo-card {{ background:{WHITE}; border:1px solid #e7ded4; border-top:6px solid {COPPER}; border-radius:18px; padding:18px 24px; display:flex; align-items:center; gap:22px; box-shadow:0 8px 24px rgba(23,50,77,.08); margin-bottom:22px; font-family:'Cairo', sans-serif !important; }}
.logo-card img {{ width:110px; max-height:88px; object-fit:contain; border-radius:10px; }}
.logo-title {{ color:{NAVY}; font-size:clamp(1.35rem,3vw,2.35rem); font-weight:800; line-height:1.35; font-family:'Cairo', sans-serif !important; }}
.logo-subtitle {{ color:{COPPER}; font-size:.95rem; font-weight:700; font-family:'Cairo', sans-serif !important; }}
.metric-card {{ background:#fff; border-right:5px solid {COPPER}; border-radius:14px; padding:15px; min-height:105px; box-shadow:0 5px 18px rgba(23,50,77,.07); font-family:'Cairo', sans-serif !important; }}
.metric-label {{ color:{MUTED}; font-size:.9rem; font-family:'Cairo', sans-serif !important; }} 
.metric-value {{ color:{NAVY}; font-size:1.7rem; font-weight:800; margin-top:5px; font-family:'Cairo', sans-serif !important; }}
div.stButton > button, .stDownloadButton > button {{ background:{NAVY} !important; color:#fff !important; border:0 !important; border-radius:9px !important; min-height:2.55rem; font-weight:700; font-family:'Cairo', sans-serif !important; }}
div.stButton > button:hover, .stDownloadButton > button:hover {{ background:{COPPER} !important; }}
input, textarea, [data-baseweb="select"] > div {{ border-radius:8px !important; font-family:'Cairo', sans-serif !important; }}
[data-testid="stDataFrame"] {{ border:1px solid #e5e7eb; border-radius:10px; font-family:'Cairo', sans-serif !important; }}
</style>
""", unsafe_allow_html=True)

def conn():
    c = sqlite3.connect(DB_FILE, check_same_thread=False)
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL, employee_id INTEGER, permissions TEXT DEFAULT '', active INTEGER DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, national_id TEXT, phone TEXT, role TEXT, department TEXT, hire_date TEXT, salary REAL DEFAULT 0, status TEXT DEFAULT 'على رأس العمل', skills TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS buildings (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, client TEXT, address TEXT, contact_person TEXT, contact_phone TEXT, floors_count INTEGER DEFAULT 1, systems_installed TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY AUTOINCREMENT, building_id INTEGER, asset_code TEXT UNIQUE, name TEXT NOT NULL, system_type TEXT, location TEXT, manufacturer TEXT, model TEXT, serial_no TEXT, install_date TEXT, warranty_date TEXT, criticality TEXT DEFAULT 'متوسط', status TEXT DEFAULT 'يعمل', last_service TEXT, next_service TEXT, notes TEXT, FOREIGN KEY(building_id) REFERENCES buildings(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS pm_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, asset_id INTEGER, plan_name TEXT NOT NULL, frequency TEXT, next_due TEXT, checklist TEXT, assigned_to INTEGER, status TEXT DEFAULT 'نشط', notes TEXT, FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, building_id INTEGER, contract_no TEXT UNIQUE, contract_type TEXT, value REAL DEFAULT 0, services_included TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'ساري', notes TEXT, FOREIGN KEY(building_id) REFERENCES buildings(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY AUTOINCREMENT, item_code TEXT UNIQUE, barcode_sku TEXT, arabic_name TEXT NOT NULL, english_name TEXT, category TEXT, unit TEXT, quantity REAL DEFAULT 0, min_quantity REAL DEFAULT 0, reorder_point REAL DEFAULT 0, purchase_price REAL DEFAULT 0, avg_cost REAL DEFAULT 0, supplier TEXT, storage_location TEXT, shelf_no TEXT, manufacturer TEXT, part_no TEXT, model TEXT, serial_no TEXT, warranty_date TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_no TEXT UNIQUE, building_id INTEGER, asset_id INTEGER, location TEXT, room TEXT, system_type TEXT, job_type TEXT, priority TEXT, description TEXT, technician_id INTEGER, supervisor_id INTEGER, report_date TEXT, assignment_date TEXT, start_date TEXT, completion_date TEXT, sla_hours REAL DEFAULT 24, estimated_cost REAL DEFAULT 0, actual_cost REAL DEFAULT 0, status TEXT DEFAULT 'جديد', root_cause TEXT, corrective_action TEXT, safety_required INTEGER DEFAULT 0, materials_used TEXT, notes TEXT, FOREIGN KEY(building_id) REFERENCES buildings(id) ON DELETE SET NULL, FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS material_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, material_id INTEGER, transaction_type TEXT, quantity REAL, unit_cost REAL, reference TEXT, task_id INTEGER, warehouse_from TEXT, warehouse_to TEXT, date TEXT, notes TEXT, FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, po_no TEXT UNIQUE, item_name TEXT, category TEXT, quantity REAL, unit TEXT, price REAL, tax REAL DEFAULT 0, total_amount REAL, supplier TEXT, invoice_no TEXT, date TEXT, status TEXT DEFAULT 'مكتمل', notes TEXT);
        CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, status TEXT, date TEXT, work_hours REAL DEFAULT 8, notes TEXT, UNIQUE(emp_id,date), FOREIGN KEY(emp_id) REFERENCES employees(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS finance (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, category TEXT, description TEXT, amount REAL, date TEXT, reference TEXT, task_id INTEGER, contract_id INTEGER);
        """)
        user_columns = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "permissions" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT ''")
        cur = c.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            c.execute("INSERT INTO users(username,password_hash,full_name,role,permissions,created_at) VALUES(?,?,?,?,?,?)", ("admin", hash_password("ChangeMe@123"), "مدير النظام", "مدير النظام", "all", datetime.now().isoformat()))

def hash_password(value):
    return hashlib.pbkdf2_hmac("sha256", value.encode(), b"tictac-v4", 120000).hex()

def q(sql, params=()):
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)

def x(sql, params=()):
    with conn() as c:
        cur = c.execute(sql, params); c.commit(); return cur.lastrowid

def session_token(uid):
    raw = f"{uid}:{SESSION_SECRET}".encode(); return f"{uid}.{hmac.new(SESSION_SECRET.encode(), raw, hashlib.sha256).hexdigest()}"

def valid_token(token):
    try:
        uid, sig = token.split(".", 1); expected = hmac.new(SESSION_SECRET.encode(), f"{uid}:{SESSION_SECRET}".encode(), hashlib.sha256).hexdigest()
        return int(uid) if hmac.compare_digest(sig, expected) else None
    except (ValueError, TypeError): return None

def current_user():
    token = st.query_params.get("session")
    uid = valid_token(token) if token else st.session_state.get("uid")
    if uid:
        row = q("SELECT * FROM users WHERE id=? AND active=1", (uid,))
        if not row.empty:
            st.session_state.uid = int(uid); return row.iloc[0].to_dict()
    return None

def logout():
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

def login():
    user = current_user()
    if user: return user
    st.markdown('<div class="logo-card"><div class="logo-title">TIC TAC<br><span class="logo-subtitle">نظام إدارة خدمات وصيانة عقود العملاء الخارجية</span></div></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("### تسجيل الدخول")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True):
            row = q("SELECT * FROM users WHERE username=? AND password_hash=? AND active=1", (u.strip(), hash_password(p)))
            if not row.empty:
                uid = int(row.iloc[0]["id"])
                st.session_state.uid = uid
                st.query_params["session"] = session_token(uid)
                st.rerun()
            else: st.error("بيانات الدخول غير صحيحة أو الحساب غير نشط.")
    return None

def has_access(user, area):
    if user.get("role") == "مدير النظام":
        return True
    saved = str(user.get("permissions") or "").strip()
    permissions = set(saved.split("|")) if saved else set(LEGACY_PERMISSIONS.get(user.get("role"), ["dashboard"]))
    return area in permissions or "all" in permissions

def logo_header():
    img = ""
    if LOGO_FILE.exists(): img = f'<img src="data:image/jpeg;base64,{base64.b64encode(LOGO_FILE.read_bytes()).decode()}">' 
    st.markdown(f'<div class="logo-card">{img}<div><div class="logo-title">TIC TAC لخدمات الصيانة والتشغيل الخارجي</div><div class="logo-subtitle">External Maintenance Contracts & Facilities Service Provider</div></div></div>', unsafe_allow_html=True)

def exports(df, name, title=None):
    if df is None or df.empty: return
    c1, c2 = st.columns(2)
    with c1: st.download_button("تنزيل Excel", excel_bytes(df), f"{name}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        if REPORTLAB_OK: st.download_button("تنزيل PDF", pdf_bytes(df, title or name), f"{name}.pdf", "application/pdf", use_container_width=True)

def excel_bytes(df):
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer: df.to_excel(writer, index=False, sheet_name="Report")
    return bio.getvalue()

def pdf_bytes(df, title):
    bio = io.BytesIO(); doc = SimpleDocTemplate(bio, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=28, bottomMargin=24)
    styles = getSampleStyleSheet(); data = [[str(c) for c in df.columns]] + [[str(v)[:60] for v in row] for row in df.fillna("").astype(str).values.tolist()]
    table = Table(data, repeatRows=1); table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor(NAVY)), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .25, colors.HexColor("#D0D5DD")), ("FONTSIZE", (0,0), (-1,-1), 7), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    doc.build([Paragraph(title, styles["Title"]), Spacer(1, 12), table]); return bio.getvalue()

def report_page(title, sql, filename, params=()):
    st.subheader(title); df = q(sql, params); st.dataframe(df, use_container_width=True, hide_index=True); exports(df, filename, title)

def metric(label, value): return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>'

init_db()
user = login()
if not user: st.stop()
logo_header()

with st.sidebar:
    st.markdown(f"### مرحباً {user['full_name']}")
    st.caption(f"الصلاحية: {user['role']}")
    if st.button("تسجيل الخروج", use_container_width=True): logout()
    options = [label for label in MAIN_MENU if has_access(user, MENU_AREAS[label])]
    if user["role"] == "مدير النظام": options += ["إدارة المستخدمين"]
    menu = st.radio("القائمة الرئيسية", options or ["لوحة التحكم"])

if menu == "الحسابات والفواتير":
    st.title("الحسابات المالية والفواتير وإيرادات العقود")
    if not has_access(user, "finance"): 
        st.error("لا تملك الصلاحية.")
        st.stop()
    
    # نموذج تسجيل المعاملات المالية المربوط ديناميكياً
    with st.form("finance"):
        a, b = st.columns(2)
        with a: 
            typ = st.selectbox("نوع المعاملة المالية", ["إيراد", "مصروف"])
            # يتم تحديث التصنيفات تلقائياً بناءً على اختيار (إيراد أو مصروف)
            cat = st.selectbox("التصنيف المالي المخصص", FINANCE_CATEGORIES[typ])
            desc = st.text_input("بيان المعاملة المالية *")
        with b: 
            amount = st.number_input("المبلغ (ر.ق / ر.س)", 0.0)
            d = st.date_input("تاريخ المعاملة", date.today())
            ref = st.text_input("رقم الفاتورة أو المرجع المرتبط")
            
        if st.form_submit_button("تسجيل المعاملة بالحسابات", use_container_width=True) and desc.strip() and amount > 0: 
            x("INSERT INTO finance(type,category,description,amount,date,reference) VALUES(?,?,?,?,?,?)", (typ, cat, desc, amount, d.isoformat(), ref))
            st.success("تم حفظ المعاملة بنجاح")

    rev = float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='إيراد'").iloc[0,0])
    exp = float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='مصروف'").iloc[0,0])
    c1, c2, c3 = st.columns(3)
    c1.markdown(metric("إجمالي إيرادات العقود والخدمات", f"{rev:,.2f} ر.ق"), unsafe_allow_html=True)
    c2.markdown(metric("إجمالي المصروفات التشغيلية", f"{exp:,.2f} ر.ق"), unsafe_allow_html=True)
    c3.markdown(metric("صافي أرباح الشركة", f"{rev-exp:,.2f} ر.ق"), unsafe_allow_html=True)
    
    report_page("السجل المالي الشامل", "SELECT type AS 'النوع', category AS 'التصنيف', description AS 'البيان', amount AS 'المبلغ', date AS 'التاريخ', reference AS 'المرجع' FROM finance ORDER BY date DESC", "finance_report")

else:
    # بقية الأقسام تعمل بشكل طبيعي وفق القائمة المختارة
    st.title(menu)
    st.info("اختر قسم الحسابات والفواتير لاستعراض وتجربة الربط المالي المحدث.")
