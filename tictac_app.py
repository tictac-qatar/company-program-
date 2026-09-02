import base64
import hashlib
import hmac
import io
import os
import secrets
import smtplib
import sqlite3
from email.message import EmailMessage
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

APP_DIR = Path(__file__).resolve().parent
DB_FILE = str(APP_DIR / "tictac_pro_v4.db")
LOGO_FILE = APP_DIR / "IMG_7478.JPG"
SESSION_SECRET = os.environ.get("TICTAC_SESSION_SECRET", "change-this-secret-in-production")
GMAIL_ADDRESS = os.environ.get("TICTAC_GMAIL_ADDRESS", "Tictac.qatar@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("TICTAC_GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL = os.environ.get("TICTAC_NOTIFY_EMAIL", "Tictac.qatar@gmail.com")

# Brand palette sampled from the supplied TIC TAC logo.
NAVY = "#17324D"
NAVY_DARK = "#0E2236"
COPPER = "#A96343"
COPPER_LIGHT = "#C98A68"
CREAM = "#F7F3EC"
INK = "#17212B"
MUTED = "#667085"
WHITE = "#FFFFFF"

SPECIALTIES = ["الكهرباء", "HVAC والتكييف", "السباكة", "الصرف الصحي", "مضخات المياه", "مكافحة الحريق", "إنذار الحريق", "المولدات", "UPS", "المصاعد", "BMS", "CCTV", "Access Control", "الشبكات والاتصالات", "الأبواب والأقفال", "نجارة", "ألومنيوم وزجاج", "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية", "حدادة ولحام", "معدات مطابخ", "نظافة", "HSE", "أخرى"]
ROLES = ["مدير النظام", "مدير صيانة المباني", "مدير العمليات", "مدير الموقع", "مشرف صيانة", "مهندس صيانة", "فني كهرباء", "فني تكييف HVAC", "فني سباكة", "فني مكافحة حريق", "فني مصاعد", "فني مولدات", "فني BMS", "فني CCTV وأمن", "فني شبكات", "فني مدني", "مسؤول سلامة HSE", "أمين مستودع", "محاسب", "مسؤول مشتريات", "مسؤول موارد بشرية", "سائق", "فني صيانة عامة"]
DEPARTMENTS = ["الإدارة", "الصيانة التشغيلية", "الفنيون والمهندسون", "السلامة HSE", "المستودعات", "المشتريات", "المالية والحسابات", "الموارد البشرية"]
CATEGORIES = ["مواد كهربائية", "مواد تكييف HVAC", "مواد سباكة وصرف", "مضخات وقطع غيار", "مكافحة وإنذار الحريق", "مولدات و UPS", "مصاعد", "BMS وتحكم", "CCTV وأمن", "شبكات واتصالات", "نجارة وأبواب", "ألومنيوم وزجاج", "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية وبناء", "حدادة ولحام", "معدات مطابخ", "مواد نظافة", "معدات سلامة PPE", "قطع غيار عامة", "أخرى"]
UNITS = ["قطعة", "متر", "متر مربع", "متر مكعب", "كيلو", "لتر", "جالون", "علبة", "كرتون", "رول", "طقم", "وحدة"]
STATUSES = ["جديد", "تم التعيين", "قيد العمل", "بانتظار قطع غيار", "مكتمل", "ملغي"]
MAIN_MENU = ["لوحة التحكم", "أوامر الصيانة", "الأصول والمعدات", "المواد وقطع الغيار", "حركة المخزون", "المشتريات", "المباني والعملاء", "العقود", "الموظفون", "الحسابات والمالية", "التقارير"]
MENU_AREAS = {"لوحة التحكم":"dashboard", "أوامر الصيانة":"maintenance", "الأصول والمعدات":"maintenance", "المواد وقطع الغيار":"inventory", "حركة المخزون":"inventory", "المشتريات":"purchases", "المباني والعملاء":"buildings", "العقود":"contracts", "الموظفون":"hr", "الحسابات والمالية":"finance", "التقارير":"reports"}
LEGACY_PERMISSIONS = {"مدير صيانة المباني": ["dashboard", "maintenance", "buildings", "contracts", "reports"], "مشرف صيانة": ["dashboard", "maintenance", "reports"], "مهندس صيانة": ["dashboard", "maintenance", "reports"], "مسؤول مشتريات": ["dashboard", "purchases", "inventory", "reports"], "أمين مستودع": ["dashboard", "inventory", "purchases", "reports"], "محاسب": ["dashboard", "finance", "contracts", "reports"], "مسؤول موارد بشرية": ["dashboard", "hr", "reports"]}

st.set_page_config(page_title="TIC TAC | صيانة المباني", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
:root {{ --navy:{NAVY}; --navy-dark:{NAVY_DARK}; --copper:{COPPER}; --cream:{CREAM}; --ink:{INK}; }}
html, body, [class*="css"] {{ font-family:'Cairo', Tahoma, Arial, sans-serif !important; }}
.stApp {{ background:linear-gradient(135deg, #fff 0%, {CREAM} 100%); color:{INK}; direction:rtl; }}
.block-container {{ max-width:1500px; padding:1.4rem clamp(.7rem, 3vw, 3rem) 3rem; }}
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg, {NAVY_DARK}, {NAVY}); border-left:4px solid {COPPER}; }}
section[data-testid="stSidebar"] * {{ color:#fff !important; }}
[data-testid="stHeader"] {{ background:transparent; }}
.logo-card {{ background:{WHITE}; border:1px solid #e7ded4; border-top:6px solid {COPPER}; border-radius:18px; padding:18px 24px; display:flex; align-items:center; gap:22px; box-shadow:0 8px 24px rgba(23,50,77,.08); margin-bottom:22px; }}
.logo-card img {{ width:110px; max-height:88px; object-fit:contain; border-radius:10px; }}
.logo-title {{ color:{NAVY}; font-size:clamp(1.35rem,3vw,2.35rem); font-weight:800; line-height:1.35; }}
.logo-subtitle {{ color:{COPPER}; font-size:.95rem; font-weight:700; }}
.metric-card {{ background:#fff; border-right:5px solid {COPPER}; border-radius:14px; padding:15px; min-height:105px; box-shadow:0 5px 18px rgba(23,50,77,.07); }}
.metric-label {{ color:{MUTED}; font-size:.9rem; }} .metric-value {{ color:{NAVY}; font-size:1.7rem; font-weight:800; margin-top:5px; }}
div.stButton > button, .stDownloadButton > button {{ background:{NAVY} !important; color:#fff !important; border:0 !important; border-radius:9px !important; min-height:2.55rem; font-weight:700; }}
div.stButton > button:hover, .stDownloadButton > button:hover {{ background:{COPPER} !important; }}
input, textarea, [data-baseweb="select"] > div {{ border-radius:8px !important; }}
[data-testid="stDataFrame"] {{ border:1px solid #e5e7eb; border-radius:10px; }}
@media (max-width: 700px) {{ .block-container {{ padding:.7rem .55rem 2rem; }} .logo-card {{ flex-direction:column; text-align:center; padding:14px; }} .logo-card img {{ width:150px; }} [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; gap:.5rem; }} [data-testid="stHorizontalBlock"] > div {{ min-width:calc(50% - .5rem) !important; flex:1 1 calc(50% - .5rem) !important; }} section[data-testid="stSidebar"] {{ width: min(85vw, 320px); }} .stDataFrame {{ font-size:.75rem; }} }}
</style>
""", unsafe_allow_html=True)


def conn():
    c = sqlite3.connect(DB_FILE, check_same_thread=False)
    c.execute("PRAGMA foreign_keys=ON")
    return c


def hash_password(value):
    return hashlib.pbkdf2_hmac("sha256", value.encode(), b"tictac-v4", 120000).hex()


def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL, employee_id INTEGER, permissions TEXT DEFAULT '', active INTEGER DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, action TEXT NOT NULL, table_name TEXT, record_id INTEGER, details TEXT, event_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL);
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
            
        # تحديث أو إنشاء حساب الـ admin بكلمة المرور الجديدة Azoz@123 تلقائياً
        c.execute("""
            INSERT INTO users(username, password_hash, full_name, role, permissions, active, created_at)
            VALUES(?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(username) DO UPDATE SET 
                password_hash = excluded.password_hash,
                active = 1,
                permissions = 'all'
        """, ("admin", hash_password("Azoz@123"), "مدير النظام", "مدير النظام", "all", datetime.now().isoformat()))
        c.commit()


def q(sql, params=()):
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)


def audit_event(action, table_name="", record_id=None, details="", user_id=None, username=None):
    try:
        uid = user_id if user_id is not None else st.session_state.get("uid")
        uname = username
        if uname is None and uid:
            row = q("SELECT username FROM users WHERE id=?", (uid,))
            uname = row.iloc[0, 0] if not row.empty else ""
        with conn() as c:
            c.execute("INSERT INTO audit_logs(user_id,username,action,table_name,record_id,details,event_at) VALUES(?,?,?,?,?,?,?)", (uid, uname or "", action, table_name, record_id, details, datetime.now().astimezone().isoformat(timespec="seconds")))
            c.commit()
    except Exception:
        pass


def x(sql, params=()):
    with conn() as c:
        cur = c.execute(sql, params); c.commit(); result = cur.lastrowid
    normalized = " ".join(sql.strip().split()).upper()
    if normalized.startswith("INSERT INTO") or normalized.startswith("UPDATE ") or normalized.startswith("DELETE FROM"):
        parts = sql.strip().split()
        table = parts[2] if normalized.startswith("INSERT INTO") else parts[1]
        audit_event("تعديل بيانات", table, result, f"SQL: {sql.strip().splitlines()[0][:180]}")
    return result


def send_login_email(username, full_name):
    if not GMAIL_APP_PASSWORD:
        audit_event("إشعار دخول - لم يتم الإرسال", "users", details="لم يتم ضبط TICTAC_GMAIL_APP_PASSWORD")
        return False
    now = datetime.now().astimezone()
    msg = EmailMessage()
    msg["Subject"] = "إشعار دخول إلى نظام TIC TAC"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL
    msg.set_content(f"تم الدخول إلى نظام TIC TAC\n\nاسم المستخدم: {username}\nالاسم: {full_name}\nالتاريخ: {now.strftime('%Y-%m-%d')}\nالوقت: {now.strftime('%H:%M:%S %Z')}\n")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        audit_event("إشعار دخول - فشل الإرسال", "users", details=str(exc)[:300])
        return False


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
    st.session_state.clear(); st.query_params.clear(); st.rerun()


def login():
    user = current_user()
    if user: return user
    st.markdown('<div class="logo-card"><div class="logo-title">TIC TAC<br><span class="logo-subtitle">نظام إدارة صيانة المباني والمرافق</span></div></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("### تسجيل الدخول")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True):
            row = q("SELECT * FROM users WHERE username=? AND password_hash=? AND active=1", (u.strip(), hash_password(p)))
            if not row.empty:
                uid = int(row.iloc[0]["id"]); st.session_state.uid = uid
                login_username = str(row.iloc[0]["username"]); login_name = str(row.iloc[0]["full_name"])
                audit_event("تسجيل دخول", "users", uid, f"المستخدم: {login_name}", user_id=uid, username=login_username)
                send_login_email(login_username, login_name)
                st.query_params.session = session_token(uid); st.rerun()
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
    st.markdown(f'<div class="logo-card">{img}<div><div class="logo-title">TIC TAC لصيانة المباني</div><div class="logo-subtitle">Building Maintenance & Facilities Management</div></div></div>', unsafe_allow_html=True)


def exports(df, name, title=None):
    if df is None or df.empty: return
    c1, c2 = st.columns(2)
    with c1: st.download_button("تنزيل Excel", excel_bytes(df), f"{name}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        if REPORTLAB_OK: st.download_button("تنزيل PDF", pdf_bytes(df, title or name), f"{name}.pdf", "application/pdf", use_container_width=True)
        else: st.warning("ثبّت reportlab لتفعيل PDF: pip install reportlab")


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

if menu == "لوحة التحكم":
    st.title("لوحة التحكم")
    vals = [q("SELECT COUNT(*) n FROM tasks").iloc[0,0], q("SELECT COUNT(*) n FROM tasks WHERE status NOT IN ('مكتمل','ملغي')").iloc[0,0], q("SELECT COUNT(*) n FROM buildings").iloc[0,0], q("SELECT COUNT(*) n FROM assets").iloc[0,0], q("SELECT COUNT(*) n FROM materials WHERE quantity<=min_quantity").iloc[0,0]]
    cols = st.columns(5)
    for c, label, val in zip(cols, ["إجمالي البلاغات", "بلاغات مفتوحة", "المباني", "الأصول", "مخزون منخفض"], vals): c.markdown(metric(label, val), unsafe_allow_html=True)
    st.markdown("### البلاغات المفتوحة ذات الأولوية")
    df = q("SELECT ticket_no AS 'البلاغ', priority AS 'الأولوية', status AS 'الحالة', description AS 'الوصف', report_date AS 'التاريخ' FROM tasks WHERE status NOT IN ('مكتمل','ملغي') ORDER BY id DESC LIMIT 20")
    st.dataframe(df, use_container_width=True, hide_index=True); exports(df, "open_tasks", "البلاغات المفتوحة")

elif menu == "أوامر الصيانة":
    st.title("أوامر الصيانة والبلاغات")
    if not has_access(user, "maintenance"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    buildings = q("SELECT id,name FROM buildings"); assets = q("SELECT id,name,asset_code FROM assets"); emps = q("SELECT id,name,role FROM employees WHERE status='على رأس العمل'")
    bm = {r['name']: r['id'] for _,r in buildings.iterrows()}; am = {f"{r['asset_code']} - {r['name']}":r['id'] for _,r in assets.iterrows()}; em = {f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    with st.form("new_task"):
        a,b = st.columns(2); ticket = f"TICK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
        with a:
            bname = st.selectbox("المبنى *", list(bm) or ["لا توجد مبانٍ"]); location=st.text_input("الموقع / الطابق"); room=st.text_input("الغرفة / المساحة"); system=st.selectbox("التخصص", SPECIALTIES); job=st.selectbox("نوع العمل", ["بلاغ عطل","صيانة وقائية PM","صيانة تصحيحية CM","طوارئ","فحص دوري","تركيب واستبدال"]); priority=st.selectbox("الأولوية", ["عادي","متوسط","عالي","طوارئ قصوى"])
        with b:
            aname=st.selectbox("الأصل المرتبط", ["بدون أصل"]+list(am)); tech=st.selectbox("الفني", ["بدون تعيين"]+list(em)); sup=st.selectbox("المشرف", ["بدون تعيين"]+list(em)); status=st.selectbox("الحالة", STATUSES); sla=st.number_input("SLA بالساعات", 1.0, 720.0, 24.0); safety=st.checkbox("يتطلب تصريح / إجراء سلامة")
        desc=st.text_area("وصف العطل والأعمال المطلوبة *"); root=st.text_area("السبب الجذري"); action=st.text_area("الإجراء التصحيحي"); notes=st.text_area("ملاحظات")
        if st.form_submit_button("حفظ أمر الصيانة", use_container_width=True) and bm:
            x("INSERT INTO tasks(ticket_no,building_id,asset_id,location,room,system_type,job_type,priority,description,technician_id,supervisor_id,report_date,assignment_date,sla_hours,status,root_cause,corrective_action,safety_required,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ticket,bm[bname],am.get(aname),location,room,system,job,priority,desc,em.get(tech),em.get(sup),date.today().isoformat(),date.today().isoformat(),sla,status,root,action,int(safety),notes)); st.success(f"تم إنشاء البلاغ {ticket}")
    st.markdown("### سجل البلاغات")
    df=q("SELECT t.ticket_no AS 'البلاغ', b.name AS 'المبنى', t.system_type AS 'التخصص', t.priority AS 'الأولوية', t.status AS 'الحالة', t.report_date AS 'التاريخ', t.description AS 'الوصف' FROM tasks t LEFT JOIN buildings b ON b.id=t.building_id ORDER BY t.id DESC")
    st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"maintenance_tasks","أوامر الصيانة")

elif menu == "الأصول والمعدات":
    st.title("الأصول والمعدات")
    if not has_access(user,"maintenance"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    buildings=q("SELECT id,name FROM buildings"); bm={r['name']:r['id'] for _,r in buildings.iterrows()}; assets=q("SELECT id,asset_code,name FROM assets"); am={f"{r['asset_code']} - {r['name']}":r['id'] for _,r in assets.iterrows()}
    tab1,tab2=st.tabs(["إضافة أصل", "قائمة الأصول"])
    with tab1:
        with st.form("asset"):
            a,b=st.columns(2)
            with a: code=st.text_input("كود الأصل *"); name=st.text_input("اسم الأصل *"); bn=st.selectbox("المبنى",list(bm) or ["بدون"]); system=st.selectbox("النظام",SPECIALTIES); loc=st.text_input("الموقع"); critical=st.selectbox("الأهمية",["منخفض","متوسط","حرج"])
            with b: manufacturer=st.text_input("الشركة المصنعة"); model=st.text_input("الموديل"); serial=st.text_input("الرقم التسلسلي"); install=st.date_input("تاريخ التركيب",date.today()); warranty=st.date_input("انتهاء الضمان",date.today()+timedelta(days=365)); status=st.selectbox("الحالة",["يعمل","متوقف","تحت الإصلاح","خارج الخدمة"])
            notes=st.text_area("ملاحظات"); submitted=st.form_submit_button("حفظ الأصل",use_container_width=True)
            if submitted and code.strip() and name.strip():
                try: x("INSERT INTO assets(building_id,asset_code,name,system_type,location,manufacturer,model,serial_no,install_date,warranty_date,criticality,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(bm.get(bn),code,name,system,loc,manufacturer,model,serial,install.isoformat(),warranty.isoformat(),critical,status,notes)); st.success("تم حفظ الأصل")
                except sqlite3.IntegrityError: st.error("كود الأصل مستخدم مسبقاً")
    with tab2:
        df=q("SELECT a.asset_code AS 'الكود',a.name AS 'الأصل',b.name AS 'المبنى',a.system_type AS 'النظام',a.location AS 'الموقع',a.criticality AS 'الأهمية',a.status AS 'الحالة',a.warranty_date AS 'الضمان' FROM assets a LEFT JOIN buildings b ON b.id=a.building_id ORDER BY a.id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"assets","الأصول")

elif menu == "المواد وقطع الغيار":
    st.title("المواد وقطع الغيار")
    if not has_access(user,"inventory"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    with st.form("material"):
        a,b=st.columns(2)
        with a: code=st.text_input("كود المادة *"); name=st.text_input("الاسم العربي *"); english=st.text_input("الاسم الإنجليزي"); category=st.selectbox("التصنيف",CATEGORIES); unit=st.selectbox("الوحدة",UNITS); qty=st.number_input("الرصيد",0.0); minimum=st.number_input("الحد الأدنى",0.0)
        with b: reorder=st.number_input("حد إعادة الطلب",0.0); price=st.number_input("سعر الشراء",0.0); cost=st.number_input("متوسط التكلفة",0.0); supplier=st.text_input("المورد"); storage=st.text_input("المستودع / الرف"); part=st.text_input("رقم القطعة / الموديل")
        notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ المادة",use_container_width=True)
        if submit and code.strip() and name.strip():
            try: x("INSERT INTO materials(item_code,arabic_name,english_name,category,unit,quantity,min_quantity,reorder_point,purchase_price,avg_cost,supplier,storage_location,part_no,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(code,name,english,category,unit,qty,minimum,reorder,price,cost,supplier,storage,part,notes)); st.success("تم حفظ المادة")
            except sqlite3.IntegrityError: st.error("كود المادة موجود مسبقاً")
    df=q("SELECT item_code AS 'الكود',arabic_name AS 'المادة',category AS 'التصنيف',unit AS 'الوحدة',quantity AS 'الرصيد',min_quantity AS 'الحد الأدنى',supplier AS 'المورد',storage_location AS 'الموقع' FROM materials ORDER BY id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"materials","المواد وقطع الغيار")

elif menu == "حركة المخزون":
    st.title("حركة المخزون")
    if not has_access(user,"inventory"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    mats=q("SELECT id,item_code,arabic_name,quantity FROM materials"); mm={f"{r['item_code']} - {r['arabic_name']} (الرصيد {r['quantity']})":r['id'] for _,r in mats.iterrows()}
    with st.form("transaction"):
        selected=st.selectbox("المادة",list(mm) or ["لا توجد مواد"]); typ=st.selectbox("نوع الحركة",["إضافة شراء","صرف لأمر صيانة","مرتجع","تسوية زيادة","تسوية نقص"]); qty=st.number_input("الكمية",0.01); cost=st.number_input("سعر الوحدة",0.0); ref=st.text_input("المرجع"); notes=st.text_area("ملاحظات")
        if st.form_submit_button("تنفيذ الحركة",use_container_width=True) and mm:
            mid=mm[selected]; old=float(q("SELECT quantity FROM materials WHERE id=?",(mid,)).iloc[0,0]); new=old+qty if typ in ["إضافة شراء","مرتجع","تسوية زيادة"] else old-qty
            if new<0: st.error("الرصيد غير كافٍ")
            else: x("UPDATE materials SET quantity=? WHERE id=?",(new,mid)); x("INSERT INTO material_transactions(material_id,transaction_type,quantity,unit_cost,reference,date,notes) VALUES(?,?,?,?,?,?,?)",(mid,typ,qty,cost,ref,date.today().isoformat(),notes)); st.success(f"تم تحديث الرصيد إلى {new}")
    df=q("SELECT mt.transaction_type AS 'الحركة',m.arabic_name AS 'المادة',mt.quantity AS 'الكمية',mt.unit_cost AS 'السعر',mt.reference AS 'المرجع',mt.date AS 'التاريخ' FROM material_transactions mt LEFT JOIN materials m ON m.id=mt.material_id ORDER BY mt.id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"inventory_transactions","حركة المخزون")

elif menu == "المشتريات":
    st.title("المشتريات")
    if not has_access(user,"purchases"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    with st.form("purchase"):
        a,b=st.columns(2)
        with a: item=st.text_input("الصنف أو الخدمة *"); category=st.selectbox("التصنيف",CATEGORIES); qty=st.number_input("الكمية",0.01); unit=st.selectbox("الوحدة",UNITS); price=st.number_input("سعر الوحدة",0.0)
        with b: tax=st.number_input("الضريبة",0.0); supplier=st.text_input("المورد *"); invoice=st.text_input("الفاتورة"); status=st.selectbox("الحالة",["مسودة","بانتظار الموافقة","قيد الشحن","مكتمل","ملغي"])
        notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ أمر الشراء",use_container_width=True)
        if submit and item.strip() and supplier.strip():
            po=f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"; total=qty*price+tax; x("INSERT INTO purchases(po_no,item_name,category,quantity,unit,price,tax,total_amount,supplier,invoice_no,date,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(po,item,category,qty,unit,price,tax,total,supplier,invoice,date.today().isoformat(),status,notes));
            if status not in ["مسودة","ملغي"]: x("INSERT INTO finance(type,category,description,amount,date,reference) VALUES('مصروف','شراء مواد وقطع غيار',?,?,?,?)",(f"أمر شراء {po} - {item}",total,date.today().isoformat(),po))
            st.success(f"تم حفظ {po}")
    report_page("سجل المشتريات","SELECT po_no AS 'رقم PO',item_name AS 'الصنف',quantity AS 'الكمية',total_amount AS 'الإجمالي',supplier AS 'المورد',date AS 'التاريخ',status AS 'الحالة' FROM purchases ORDER BY id DESC","purchases")

elif menu == "المباني والعملاء":
    st.title("المباني والعملاء")
    with st.form("building"):
        a,b=st.columns(2)
        with a: name=st.text_input("اسم المبنى *"); client=st.text_input("العميل / المالك *"); address=st.text_input("العنوان"); contact=st.text_input("مسؤول التواصل")
        with b: phone=st.text_input("الهاتف"); floors=st.number_input("عدد الطوابق",1); systems=st.text_area("الأنظمة الموجودة")
        notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ المبنى",use_container_width=True)
        if submit and name.strip() and client.strip(): x("INSERT INTO buildings(name,client,address,contact_person,contact_phone,floors_count,systems_installed,notes) VALUES(?,?,?,?,?,?,?,?)",(name,client,address,contact,phone,floors,systems,notes)); st.success("تم الحفظ")
    report_page("قائمة المباني","SELECT name AS 'المبنى',client AS 'العميل',address AS 'العنوان',contact_person AS 'المسؤول',contact_phone AS 'الهاتف',floors_count AS 'الطوابق' FROM buildings ORDER BY id DESC","buildings")

elif menu == "العقود":
    st.title("عقود الصيانة")
    if not has_access(user,"maintenance") and not has_access(user,"finance"): st.error("لا تملك الصلاحية."); st.stop()
    buildings=q("SELECT id,name FROM buildings"); bm={r['name']:r['id'] for _,r in buildings.iterrows()}
    with st.form("contract"):
        a,b=st.columns(2)
        with a: no=st.text_input("رقم العقد *"); bn=st.selectbox("المبنى",list(bm) or ["بدون"]); typ=st.selectbox("نوع العقد",["شاملة","وقائية","إدارة مرافق FM","أخرى"]); value=st.number_input("القيمة",0.0)
        with b: start=st.date_input("البداية",date.today()); end=st.date_input("النهاية",date.today()+timedelta(days=365)); status=st.selectbox("الحالة",["ساري","منتهي","قيد التجديد","ملغي"])
        services=st.text_area("الخدمات المشمولة"); notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ العقد",use_container_width=True)
        if submit and no.strip():
            try: cid=x("INSERT INTO contracts(building_id,contract_no,contract_type,value,services_included,start_date,end_date,status,notes) VALUES(?,?,?,?,?,?,?,?,?)",(bm.get(bn),no,typ,value,services,start.isoformat(),end.isoformat(),status,notes)); x("INSERT INTO finance(type,category,description,amount,date,reference,contract_id) VALUES('إيراد','عقود صيانة',?,?,?,?,?)",(f"عقد {no}",value,start.isoformat(),no,cid)); st.success("تم حفظ العقد")
            except sqlite3.IntegrityError: st.error("رقم العقد موجود")
    report_page("العقود","SELECT c.contract_no AS 'العقد',b.name AS 'المبنى',c.contract_type AS 'النوع',c.value AS 'القيمة',c.start_date AS 'البداية',c.end_date AS 'النهاية',c.status AS 'الحالة' FROM contracts c LEFT JOIN buildings b ON b.id=c.building_id ORDER BY c.id DESC","contracts")

elif menu == "الموظفون":
    st.title("الموظفون")
    if not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    with st.form("employee"):
        a,b=st.columns(2)
        with a: name=st.text_input("اسم الموظف *"); nid=st.text_input("الرقم الشخصي"); phone=st.text_input("الهاتف"); role=st.selectbox("الوظيفة",ROLES); dept=st.selectbox("القسم",DEPARTMENTS)
        with b: hire=st.date_input("تاريخ التعيين",date.today()); salary=st.number_input("الراتب",0.0); status=st.selectbox("الحالة",["على رأس العمل","إجازة","موقوف","منتهي الخدمة"]); skills=st.text_input("المهارات")
        notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ الموظف",use_container_width=True)
        if submit and name.strip(): x("INSERT INTO employees(name,national_id,phone,role,department,hire_date,salary,status,skills,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(name,nid,phone,role,dept,hire.isoformat(),salary,status,skills,notes)); st.success("تم الحفظ")
    report_page("الموظفون","SELECT name AS 'الموظف',role AS 'الوظيفة',department AS 'القسم',phone AS 'الهاتف',salary AS 'الراتب',status AS 'الحالة' FROM employees ORDER BY id DESC","employees")

elif menu == "الحضور والدوام":
    st.title("الحضور والدوام")
    if not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    emps=q("SELECT id,name,role FROM employees WHERE status='على رأس العمل'"); em={f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    with st.form("attendance"):
        en=st.selectbox("الموظف",list(em) or ["لا يوجد"]); status=st.selectbox("الحالة",["حاضر","غائب","إجازة","مرضي","مهمة خارجية","تأخير"]); d=st.date_input("التاريخ",date.today()); hours=st.number_input("ساعات العمل",0.0,24.0,8.0); notes=st.text_input("ملاحظات")
        if st.form_submit_button("تسجيل الحضور",use_container_width=True) and em:
            try: x("INSERT INTO attendance(emp_id,status,date,work_hours,notes) VALUES(?,?,?,?,?)",(em[en],status,d.isoformat(),hours,notes)); st.success("تم التسجيل")
            except sqlite3.IntegrityError: st.error("تم التسجيل مسبقاً لهذا الموظف والتاريخ")
    report_page("تقرير الحضور","SELECT e.name AS 'الموظف',a.status AS 'الحالة',a.date AS 'التاريخ',a.work_hours AS 'الساعات',a.notes AS 'ملاحظات' FROM attendance a LEFT JOIN employees e ON e.id=a.emp_id ORDER BY a.date DESC","attendance")

elif menu == "الحسابات والمالية":
    st.title("الحسابات والمالية")
    if not has_access(user,"finance"): st.error("لا تملك الصلاحية."); st.stop()
    with st.form("finance"):
        a,b=st.columns(2)
        with a: typ=st.selectbox("النوع",["إيراد","مصروف"]); cat=st.selectbox("التصنيف",["عقود صيانة","رواتب وأجور","شراء مواد وقطع غيار","مصاريف تشغيلية","إصلاحات طارئة","أخرى"]); desc=st.text_input("البيان *")
        with b: amount=st.number_input("المبلغ",0.0); d=st.date_input("التاريخ",date.today()); ref=st.text_input("المرجع")
        if st.form_submit_button("حفظ المعاملة",use_container_width=True) and desc.strip() and amount>0: x("INSERT INTO finance(type,category,description,amount,date,reference) VALUES(?,?,?,?,?,?)",(typ,cat,desc,amount,d.isoformat(),ref)); st.success("تم الحفظ")
    rev=float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='إيراد'").iloc[0,0]); exp=float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='مصروف'").iloc[0,0]); c1,c2,c3=st.columns(3); c1.markdown(metric("الإيرادات",f"{rev:,.2f} ر.ق"),unsafe_allow_html=True); c2.markdown(metric("المصروفات",f"{exp:,.2f} ر.ق"),unsafe_allow_html=True); c3.markdown(metric("صافي الربح",f"{rev-exp:,.2f} ر.ق"),unsafe_allow_html=True)
    report_page("السجل المالي","SELECT type AS 'النوع',category AS 'التصنيف',description AS 'البيان',amount AS 'المبلغ',date AS 'التاريخ',reference AS 'المرجع' FROM finance ORDER BY date DESC","finance")

elif menu == "التقارير":
    st.title("التقارير والتصدير")
    if not has_access(user,"maintenance") and not has_access(user,"finance") and not has_access(user,"inventory") and not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    choice=st.selectbox("نوع التقرير",["أوامر الصيانة","الأصول","المواد","حركة المخزون","المشتريات","المباني","العقود","الموظفون","الحضور","المالية","سجل المراقبة"])
    reports={"أوامر الصيانة":("SELECT * FROM tasks ORDER BY id DESC","report_tasks"),"الأصول":("SELECT * FROM assets ORDER BY id DESC","report_assets"),"المواد":("SELECT * FROM materials ORDER BY id DESC","report_materials"),"حركة المخزون":("SELECT * FROM material_transactions ORDER BY id DESC","report_inventory"),"المشتريات":("SELECT * FROM purchases ORDER BY id DESC","report_purchases"),"المباني":("SELECT * FROM buildings ORDER BY id DESC","report_buildings"),"العقود":("SELECT * FROM contracts ORDER BY id DESC","report_contracts"),"الموظفون":("SELECT * FROM employees ORDER BY id DESC","report_employees"),"الحضور":("SELECT * FROM attendance ORDER BY id DESC","report_attendance"),"المالية":("SELECT * FROM finance ORDER BY id DESC","report_finance")}
    reports["سجل المراقبة"]=("SELECT event_at AS 'التاريخ والوقت',username AS 'المستخدم',action AS 'العملية',table_name AS 'القسم / الجدول',record_id AS 'رقم السجل',details AS 'التفاصيل' FROM audit_logs ORDER BY id DESC","audit_log")
    sql,name=reports[choice]; df=q(sql); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,name,choice)

elif menu == "إدارة المستخدمين":
    st.title("إدارة المستخدمين والصلاحيات")
    if user["role"] != "مدير النظام": st.error("هذه الصفحة للمدير فقط."); st.stop()
    emps=q("SELECT id,name,role FROM employees"); em={f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    st.caption("حدد الأقسام التي يستطيع المستخدم رؤيتها من القائمة الرئيسية. مدير النظام يملك جميع الصلاحيات تلقائياً.")
    with st.form("user"):
        a,b=st.columns(2)
        with a:
            username=st.text_input("اسم المستخدم *")
            password=st.text_input("كلمة المرور *",type="password")
            full=st.text_input("الاسم الظاهر *")
        with b:
            account_type=st.selectbox("نوع الحساب",["مستخدم مخصص","مدير النظام"])
            employee=st.selectbox("الموظف المرتبط",["بدون"]+list(em))
            selected_sections=st.multiselect("صلاحيات القائمة الرئيسية", MAIN_MENU, default=["لوحة التحكم"])
        if st.form_submit_button("إضافة المستخدم",use_container_width=True):
            if not username.strip() or not password or not full.strip():
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور والاسم الظاهر.")
            elif account_type != "مدير النظام" and not selected_sections:
                st.error("اختر قسماً واحداً على الأقل للمستخدم.")
            else:
                permissions="all" if account_type == "مدير النظام" else "|".join(dict.fromkeys([MENU_AREAS[s] for s in selected_sections] + ["dashboard"]))
                try:
                    x("INSERT INTO users(username,password_hash,full_name,role,employee_id,permissions,active,created_at) VALUES(?,?,?,?,?,?,1,?)",(username.strip(),hash_password(password),full,account_type,em.get(employee),permissions,datetime.now().isoformat()))
                    audit_event("إضافة مستخدم", "users", details=f"تمت إضافة: {username.strip()} بالصلاحيات: {permissions}")
                    st.success("تمت إضافة المستخدم والصلاحيات بنجاح.")
                except sqlite3.IntegrityError: st.error("اسم المستخدم موجود مسبقاً.")

    users=q("SELECT id,username,full_name,role,active FROM users ORDER BY id DESC")
    st.markdown("### المستخدمون المسجلون")
    display=users.rename(columns={"username":"المستخدم","full_name":"الاسم","role":"نوع الحساب","active":"الحالة"}).copy()
    display["الحالة"]=display["الحالة"].map({1:"نشط",0:"ملغى / معطل"})
    st.dataframe(display.drop(columns=["id"]),use_container_width=True,hide_index=True)
    exports(display.drop(columns=["id"]),"users","المستخدمون")

    names={f"{r['username']} — {r['full_name']}":int(r['id']) for _,r in users.iterrows() if int(r['id']) != int(user['id'])}
    if names:
        st.markdown("### إلغاء أو إعادة تفعيل مستخدم")
        selected_user=st.selectbox("اختر المستخدم",list(names))
        chosen_id=names[selected_user]
        chosen_active=int(users.loc[users["id"]==chosen_id,"active"].iloc[0])
        c1,c2=st.columns(2)
        with c1:
            if st.button("إلغاء / تعطيل المستخدم",use_container_width=True,disabled=not bool(chosen_active)):
                x("UPDATE users SET active=0 WHERE id=?",(chosen_id,)); audit_event("تعطيل مستخدم", "users", chosen_id, f"المستخدم: {selected_user}"); st.success("تم تعطيل المستخدم. لن يستطيع تسجيل الدخول."); st.rerun()
        with c2:
            if st.button("إعادة تفعيل المستخدم",use_container_width=True,disabled=bool(chosen_active)):
                x("UPDATE users SET active=1 WHERE id=?",(chosen_id,)); audit_event("إعادة تفعيل مستخدم", "users", chosen_id, f"المستخدم: {selected_user}"); st.success("تمت إعادة تفعيل المستخدم."); st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("TIC TAC • Building Maintenance • v4.0")
