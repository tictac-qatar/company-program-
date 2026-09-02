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
DB_FILE = str(APP_DIR / "tictac_pro_v4.db")
LOGO_FILE = APP_DIR / "IMG_7478.jpeg"
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

MAIN_MENU = ["لوحة التحكم", "طلبات الخدمة وأوامر الصيانة", "الأصول والمعدات", "المواد وقطع الغيار", "حركة المخزون", "المشتريات", "مواقع العملاء", "عقود الصيانة للعملاء", "الموظفون", "الحضور والدوام", "الحسابات والفواتير", "التقارير"]
MENU_AREAS = {"لوحة التحكم":"dashboard", "طلبات الخدمة وأوامر الصيانة":"maintenance", "الأصول والمعدات":"maintenance", "المواد وقطع الغيار":"inventory", "حركة المخزون":"inventory", "المشتريات":"purchases", "مواقع العملاء":"buildings", "عقود الصيانة للعملاء":"contracts", "الموظفون":"hr", "الحضور والدوام":"hr", "الحسابات والفواتير":"finance", "التقارير":"reports"}
LEGACY_PERMISSIONS = {"مدير العقود والعملاء": ["dashboard", "maintenance", "buildings", "contracts", "reports"], "مشرف صيانة ميدانية": ["dashboard", "maintenance", "reports"], "مهندس دعم فني": ["dashboard", "maintenance", "reports"], "مسؤول مشتريات": ["dashboard", "purchases", "inventory", "reports"], "أمين مستودع": ["dashboard", "inventory", "purchases", "reports"], "محاسب": ["dashboard", "finance", "contracts", "reports"], "مسؤول موارد بشرية": ["dashboard", "hr", "reports"]}

st.set_page_config(page_title="TIC TAC | نظام إدارة خدمات الصيانة", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800&display=swap');
:root {{ --navy:{NAVY}; --navy-dark:{NAVY_DARK}; --copper:{COPPER}; --cream:{CREAM}; --ink:{INK}; }}
*, html, body, [class*="css"] {{ font-family:'Cairo', Tahoma, Arial, sans-serif !important; }}
.stApp {{ background:linear-gradient(135deg, #fff 0%, {CREAM} 100%); color:{INK}; direction:rtl; }}
.block-container {{ max-width:1500px; padding:1.5rem 2rem 3rem; }}
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg, {NAVY_DARK}, {NAVY}); border-left:4px solid {COPPER}; }}
section[data-testid="stSidebar"] * {{ color:#fff !important; }}
[data-testid="stHeader"] {{ background:transparent; }}

/* تدرج هرمي متناسق لأحجام الخطوط والعناوين */
h1 {{ font-size: 1.85rem !important; font-weight: 800 !important; color: {NAVY} !important; margin-bottom: 1rem !important; }}
h2 {{ font-size: 1.5rem !important; font-weight: 700 !important; color: {NAVY} !important; margin-top: 1rem !important; }}
h3 {{ font-size: 1.25rem !important; font-weight: 700 !important; color: {COPPER} !important; margin-top: 0.8rem !important; }}
p, span, label, div, .stMarkdown {{ font-size: 0.95rem !important; line-height: 1.6 !important; }}

.logo-card {{ background:{WHITE}; border:1px solid #e7ded4; border-top:6px solid {COPPER}; border-radius:14px; padding:16px 22px; display:flex; align-items:center; gap:20px; box-shadow:0 6px 20px rgba(23,50,77,.06); margin-bottom:20px; }}
.logo-card img {{ width:95px; max-height:75px; object-fit:contain; border-radius:8px; }}
.logo-title {{ color:{NAVY}; font-size:1.45rem; font-weight:800; line-height:1.3; }}
.logo-subtitle {{ color:{COPPER}; font-size:0.9rem; font-weight:700; margin-top:4px; }}

.metric-card {{ background:#fff; border-right:5px solid {COPPER}; border-radius:12px; padding:16px; min-height:100px; box-shadow:0 4px 15px rgba(23,50,77,.06); }}
.metric-label {{ color:{MUTED}; font-size:0.85rem !important; font-weight:600; }} 
.metric-value {{ color:{NAVY}; font-size:1.6rem !important; font-weight:800; margin-top:6px; }}

div.stButton > button, .stDownloadButton > button {{ background:{NAVY} !important; color:#fff !important; border:0 !important; border-radius:8px !important; min-height:2.4rem; font-size:0.95rem !important; font-weight:700 !important; }}
div.stButton > button:hover, .stDownloadButton > button:hover {{ background:{COPPER} !important; }}
input, textarea, [data-baseweb="select"] > div {{ border-radius:8px !important; font-size:0.95rem !important; }}
[data-testid="stDataFrame"] {{ border:1px solid #e5e7eb; border-radius:10px; }}
.stCode, code, pre, textarea, input {{ color: {INK} !important; }}
.stCodeBlock {{ background-color: {WHITE} !important; color: {INK} !important; border: 1px solid #e7ded4; }}

@media (max-width: 700px) {{ 
  .block-container {{ padding:1rem 0.75rem 2rem; }} 
  .logo-card {{ flex-direction:column; text-align:center; padding:12px; }} 
  .logo-card img {{ width:120px; }} 
  section[data-testid="stSidebar"] {{ width: min(85vw, 320px); }} 
  .stDataFrame {{ font-size:0.8rem; }} 
}}
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
    st.session_state.clear(); st.query_params.clear(); st.rerun()


def login():
    user = current_user()
    if user: return user
    
    img_html = ""
    if LOGO_FILE.exists():
        img_html = f'<div style="text-align: center; margin-bottom: 12px;"><img src="data:image/jpeg;base64,{base64.b64encode(LOGO_FILE.read_bytes()).decode()}" style="max-height: 90px; border-radius: 8px;"></div>'
    
    st.markdown(f'{img_html}<div class="logo-card"><div class="logo-title">TIC TAC<br><span class="logo-subtitle">       النظام التشغيلى      </span></div></div>', unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("### تسجيل الدخول")
        u = st.text_input("اسم المستخدم", key="login_username_field")
        p = st.text_input("كلمة المرور", type="password", key="login_password_secure_field")
        if st.button("دخول", use_container_width=True):
            row = q("SELECT * FROM users WHERE username=? AND password_hash=? AND active=1", (u.strip(), hash_password(p)))
            if not row.empty:
                uid = int(row.iloc[0]["id"]); st.session_state.uid = uid; st.query_params.session = session_token(uid); st.rerun()
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
    st.markdown(f'<div class="logo-card">{img}<div><div class="logo-title">TIC TAC لصيانة المباني</div><div class="logo-subtitle">For Building Maintenance</div></div></div>', unsafe_allow_html=True)


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
    st.title("لوحة التحكم لطلبات الصيانة")
    vals = [
        q("SELECT COUNT(*) n FROM materials").iloc[0,0],
        q("SELECT COUNT(*) n FROM purchases").iloc[0,0],
        q("SELECT COUNT(*) n FROM tasks").iloc[0,0],
        q("SELECT COUNT(*) n FROM contracts").iloc[0,0],
        q("SELECT COUNT(*) n FROM buildings").iloc[0,0]
    ]
    cols = st.columns(5)
    for c, label, val in zip(cols, ["المخزون وقطع الغيار", "المشتريات", "طلبات الخدمة وأوامر الصيانة", "العقود السارية", "مواقع العملاء"], vals):
        c.markdown(metric(label, val), unsafe_allow_html=True)
        
    st.markdown("### طلبات خدمات الصيانة النشطة للعملاء")
    df = q("SELECT ticket_no AS 'رقم الطلب', priority AS 'الأولوية', status AS 'حالة الطلب', description AS 'وصف الخدمة', report_date AS 'تاريخ الاستلام' FROM tasks WHERE status NOT IN ('مكتمل ومسلم للعميل','ملغي') ORDER BY id DESC LIMIT 20")
    st.dataframe(df, use_container_width=True, hide_index=True); exports(df, "client_service_requests", "طلبات الصيانة النشطة")

elif menu == "طلبات الخدمة وأوامر الصيانة":
    st.title("طلبات الخدمة وأوامر الصيانة الخارجية للعملاء")
    if not has_access(user, "maintenance"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    buildings = q("SELECT id,name,client FROM buildings"); assets = q("SELECT id,name,asset_code FROM assets"); emps = q("SELECT id,name,role FROM employees WHERE status='على رأس العمل'")
    bm = {f"{r['name']} (العميل: {r['client']})": r['id'] for _,r in buildings.iterrows()}; am = {f"{r['asset_code']} - {r['name']}":r['id'] for _,r in assets.iterrows()}; em = {f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    with st.form("new_task"):
        a,b = st.columns(2); ticket = f"SRV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
        with a:
            bname = st.selectbox("موقع العميل والمبنى *", list(bm) or ["لا توجد مواقع عملاء مسجلة"]); location=st.text_input("مكان العطل بالموقع / الطابق"); room=st.text_input("رقم الغرفة / القسم"); system=st.selectbox("تخصص الخدمة المطلوبة", SPECIALTIES); job=st.selectbox("نوع الطلب", ["طلب خدمة طارئة (Call-out)","عقد صيانة وقائية دورية PM","إصلاح تصحيحي CM","فحص واختبار فني","تركيب وتوريد وتركيب"]); priority=st.selectbox("أولوية الاستجابة", ["عادي","متوسط","عالي","طوارئ حرجة SLA"])
        with b:
            aname=st.selectbox("الأصل أو المعدة التابعة للعميل", ["بدون أصل محدد"]+list(am)); tech=st.selectbox("الفني المسؤول بالمنطقة", ["بدون تعيين"]+list(em)); sup=st.selectbox("مشرف الموقع", ["بدون تعيين"]+list(em)); status=st.selectbox("حالة الطلب", STATUSES); sla=st.number_input("مدة SLA بالاستجابة (ساعات)", 1.0, 720.0, 24.0); safety=st.checkbox("يتطلب تصريح عمل أمان (Permit to Work)")
        desc=st.text_area("تفاصيل بلاغ أو طلب خدمة العميل *"); root=st.text_area("السبب الجذري للأعطال"); action=st.text_area("الإجراءات الفنية المنفذة"); notes=st.text_area("ملاحظات خاصة بالفاتورة أو العميل")
        if st.form_submit_button("إصدار وتسجيل أمر العمل", use_container_width=True) and bm:
            x("INSERT INTO tasks(ticket_no,building_id,asset_id,location,room,system_type,job_type,priority,description,technician_id,supervisor_id,report_date,assignment_date,sla_hours,status,root_cause,corrective_action,safety_required,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ticket,bm[bname],am.get(aname),location,room,system,job,priority,desc,em.get(tech),em.get(sup),date.today().isoformat(),date.today().isoformat(),sla,status,root,action,int(safety),notes)); st.success(f"تم تسجيل طلب الخدمة برقم {ticket}")
    st.markdown("### سجل طلبات وخدمات العملاء")
    df=q("SELECT t.ticket_no AS 'رقم الطلب', b.client AS 'العميل', b.name AS 'الموقع', t.system_type AS 'التخصص', t.job_type AS 'نوع الطلب', t.status AS 'الحالة', t.report_date AS 'التاريخ', t.description AS 'الوصف' FROM tasks t LEFT JOIN buildings b ON b.id=t.building_id ORDER BY t.id DESC")
    st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"client_service_orders","أوامر الصيانة الخارجية")

elif menu == "الأصول والمعدات":
    st.title("أصول ومعدات العملاء بالمواقع الخارجية")
    if not has_access(user,"maintenance"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    buildings=q("SELECT id,name,client FROM buildings"); bm={f"{r['name']} (العميل: {r['client']})":r['id'] for _,r in buildings.iterrows()}; assets=q("SELECT id,asset_code,name FROM assets"); am={f"{r['asset_code']} - {r['name']}":r['id'] for _,r in assets.iterrows()}
    tab1,tab2=st.tabs(["تسجيل أصل للعميل", "قائمة أصول ومعدات العملاء"])
    with tab1:
        with st.form("asset"):
            a,b=st.columns(2)
            with a: code=st.text_input("كود الأصل أو الباركود *"); name=st.text_input("اسم المعدة أو الجهاز *"); bn=st.selectbox("موقع العميل",list(bm) or ["بدون"]); system=st.selectbox("النظام الفني",SPECIALTIES); loc=st.text_input("الموقع الدقيق داخل منشأة العميل"); critical=st.selectbox("درجة الحرجية",["منخفض","متوسط","حرج للعميل"])
            with b: manufacturer=st.text_input("الشركة المصنعة"); model=st.text_input("الموديل"); serial=st.text_input("الرقم التسلسلي"); install=st.date_input("تاريخ التركيب لدى العميل",date.today()); warranty=st.date_input("انتهاء ضمان المورد / الشركة",date.today()+timedelta(days=365)); status=st.selectbox("الحالة التشغيلية",["يعمل","متوقف","تحت الصيانة التعاقدية","خارج الخدمة"])
            notes=st.text_area("ملاحظات تفصيلية"); submitted=st.form_submit_button("حفظ الأصل",use_container_width=True)
            if submitted and code.strip() and name.strip():
                try: x("INSERT INTO assets(building_id,asset_code,name,system_type,location,manufacturer,model,serial_no,install_date,warranty_date,criticality,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(bm.get(bn),code,name,system,loc,manufacturer,model,serial,install.isoformat(),warranty.isoformat(),critical,status,notes)); st.success("تم حفظ الأصل بنجاح")
                except sqlite3.IntegrityError: st.error("كود الأصل مستخدم مسبقاً")
    with tab2:
        df=q("SELECT a.asset_code AS 'الكود',a.name AS 'الأصل',b.client AS 'العميل',b.name AS 'الموقع',a.system_type AS 'النظام',a.criticality AS 'الحرجية',a.status AS 'الحالة' FROM assets a LEFT JOIN buildings b ON b.id=a.building_id ORDER BY a.id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"client_assets","أصول العملاء")

elif menu == "المواد وقطع الغيار":
    st.title("المواد وقطع الغيار بمستودع الشركة")
    if not has_access(user,"inventory"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    with st.form("material"):
        a,b=st.columns(2)
        with a: code=st.text_input("كود الصنف *"); name=st.text_input("الاسم العربي *"); english=st.text_input("الاسم الإنجليزي"); category=st.selectbox("التصنيف",CATEGORIES); unit=st.selectbox("الوحدة",UNITS); qty=st.number_input("الرصيد الحالي",0.0); minimum=st.number_input("الحد الأدنى للمخزون",0.0)
        with b: reorder=st.number_input("نقطة إعادة الطلب",0.0); price=st.number_input("سعر التوريد",0.0); cost=st.number_input("متوسط التكلفة",0.0); supplier=st.text_input("المورد المعتمد"); storage=st.text_input("رقم المستودع والرف"); part=st.text_input("رقم القطعة البديلة (Part No)")
        notes=st.text_area("ملاحظات فنية"); submit=st.form_submit_button("حفظ الصنف بالمستودع",use_container_width=True)
        if submit and code.strip() and name.strip():
            try: x("INSERT INTO materials(item_code,arabic_name,english_name,category,unit,quantity,min_quantity,reorder_point,purchase_price,avg_cost,supplier,storage_location,part_no,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(code,name,english,category,unit,qty,minimum,reorder,price,cost,supplier,storage,part,notes)); st.success("تم حفظ الصنف")
            except sqlite3.IntegrityError: st.error("كود المادة موجود مسبقاً")
    df=q("SELECT item_code AS 'الكود',arabic_name AS 'المادة',category AS 'التصنيف',unit AS 'الوحدة',quantity AS 'الرصيد',min_quantity AS 'الحد الأدنى',supplier AS 'المورد',storage_location AS 'الموقع' FROM materials ORDER BY id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"materials_stock","مستودع قطع الغيار")

elif menu == "حركة المخزون":
    st.title("حركة المخزون والصرف على مواقع العملاء")
    if not has_access(user,"inventory"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    mats=q("SELECT id,item_code,arabic_name,quantity FROM materials"); mm={f"{r['item_code']} - {r['arabic_name']} (الرصيد {r['quantity']})":r['id'] for _,r in mats.iterrows()}
    with st.form("transaction"):
        selected=st.selectbox("الصنف أو قطعة الغيار",list(mm) or ["لا توجد مواد"]); typ=st.selectbox("نوع الحركة",["إضافة مشريات للمستودع","صرف قطع غيار لموقع عميل","مرتجع من موقع","تسوية زيادة","تسوية عجز"]); qty=st.number_input("الكمية",0.01); cost=st.number_input("سعر الوحدة",0.0); ref=st.text_input("مرجع أمر الصيانة أو رقم الإذن"); notes=st.text_area("ملاحظات الحركة")
        if st.form_submit_button("تنفيذ حركة المخزون",use_container_width=True) and mm:
            mid=mm[selected]; old=float(q("SELECT quantity FROM materials WHERE id=?",(mid,)).iloc[0,0]); new=old+qty if typ in ["إضافة مشريات للمستودع","مرتجع من موقع","تسوية زيادة"] else old-qty
            if new<0: st.error("الرصيد في المستودع غير كافٍ لعملية الصرف")
            else: x("UPDATE materials SET quantity=? WHERE id=?",(new,mid)); x("INSERT INTO material_transactions(material_id,transaction_type,quantity,unit_cost,reference,date,notes) VALUES(?,?,?,?,?,?,?)",(mid,typ,qty,cost,ref,date.today().isoformat(),notes)); st.success(f"تم تحديث رصيد الصنف ليصبح {new}")
    df=q("SELECT mt.transaction_type AS 'الحركة',m.arabic_name AS 'المادة',mt.quantity AS 'الكمية',mt.unit_cost AS 'السعر',mt.reference AS 'المرجع',mt.date AS 'التاريخ' FROM material_transactions mt LEFT JOIN materials m ON m.id=mt.material_id ORDER BY mt.id DESC"); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,"inventory_movement","حركة المخزون")

elif menu == "المشتريات":
    st.title("مشتريات مواد ومعدات مشاريع العملاء")
    if not has_access(user,"purchases"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    with st.form("purchase"):
        a,b=st.columns(2)
        with a: item=st.text_input("الصنف أو الخدمة المشتراة *"); category=st.selectbox("التصنيف",CATEGORIES); qty=st.number_input("الكمية",0.01); unit=st.selectbox("الوحدة",UNITS); price=st.number_input("سعر الوحدة",0.0)
        with b: tax=st.number_input("قيمة الضريبة",0.0); supplier=st.text_input("المورد الخارجي *"); invoice=st.text_input("رقم فاتورة المورد"); status=st.selectbox("حالة أمر الشراء",["مسودة","بانتظار الاعتماد المالي","قيد التوريد","مكتمل ومستلم","ملغي"])
        notes=st.text_area("ملاحظات الشراء"); submit=st.form_submit_button("حفظ أمر الشراء الخارجي",use_container_width=True)
        if submit and item.strip() and supplier.strip():
            po=f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"; total=qty*price+tax; x("INSERT INTO purchases(po_no,item_name,category,quantity,unit,price,tax,total_amount,supplier,invoice_no,date,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(po,item,category,qty,unit,price,tax,total,supplier,invoice,date.today().isoformat(),status,notes));
            if status not in ["مسودة","ملغي"]: x("INSERT INTO finance(type,category,description,amount,date,reference) VALUES('مصروف','شراء مواد وقطع غيار مشاريع العملاء',?,?,?,?)",(f"أمر شراء {po} - {item}",total,date.today().isoformat(),po))
            st.success(f"تم اعتماد وحفظ أمر الشراء برقم {po}")
    report_page("سجل مشتريات الشركة","SELECT po_no AS 'رقم PO',item_name AS 'الصنف',quantity AS 'الكمية',total_amount AS 'الإجمالي',supplier AS 'المورد',date AS 'التاريخ',status AS 'الحالة' FROM purchases ORDER BY id DESC","purchases_report")

elif menu == "مواقع العملاء":
    st.title("إدارة عملاء ومواقع الصيانة الخارجية")
    with st.form("building"):
        a,b=st.columns(2)
        with a: name=st.text_input("اسم الموقع / المبنى التابع للعميل *"); client=st.text_input("اسم العميل / الشركة المالكة *"); address=st.text_input("عنوان الموقع بالتفصيل"); contact=st.text_input("اسم مسؤول الاتصال لدى العميل")
        with b: phone=st.text_input("هاتف مسؤول العميل"); floors=st.number_input("عدد الطوابق أو الوحدات بالموقع",1); systems=st.text_area("الأنظمة الكهروميكانيكية المتعاقد عليها بالموقع")
        notes=st.text_area("ملاحظات تعاقدية خاصة بالعميل والموقع"); submit=st.form_submit_button("حفظ بيانات موقع العميل",use_container_width=True)
        if submit and name.strip() and client.strip(): x("INSERT INTO buildings(name,client,address,contact_person,contact_phone,floors_count,systems_installed,notes) VALUES(?,?,?,?,?,?,?,?)",(name,client,address,contact,phone,floors,systems,notes)); st.success("تم حفظ موقع العميل بنجاح")
    report_page("قائمة مواقع وعملاء الصيانة","SELECT name AS 'الموقع',client AS 'العميل',address AS 'العنوان',contact_person AS 'المسؤول',contact_phone AS 'الهاتف',floors_count AS 'الطوابق' FROM buildings ORDER BY id DESC","clients_buildings")

elif menu == "عقود الصيانة للعملاء":
    st.title("عقود الصيانة والتشغيل مع العملاء")
    if not has_access(user,"maintenance") and not has_access(user,"finance"): st.error("لا تملك الصلاحية."); st.stop()
    buildings=q("SELECT id,name,client FROM buildings"); bm={f"{r['name']} (العميل: {r['client']})":r['id'] for _,r in buildings.iterrows()}
    with st.form("contract"):
        a,b=st.columns(2)
        with a: no=st.text_input("رقم العقد مع العميل *"); bn=st.selectbox("موقع العميل المرتبط بالعقد",list(bm) or ["بدون"]); typ=st.selectbox("نوع عقد الصيانة",["صيانة شاملة قطع غيار وخدمة","صيانة وقائية دورية فقط","إدارة مرافق متكاملة FM","حسب الطلب Call-out"]); value=st.number_input("قيمة العقد السنوية / الإجمالية",0.0)
        with b: start=st.date_input("تاريخ بداية العقد",date.today()); end=st.date_input("تاريخ نهاية العقد",date.today()+timedelta(days=365)); status=st.selectbox("الحالة العقد",["ساري","منتهي","قيد التجديد","مفسوخ / ملغي"])
        services=st.text_area("نطاق الأعمال والخدمات المشمولة بالعقد"); notes=st.text_area("شروط الدفع والملاحظات المالية"); submit=st.form_submit_button("حفظ وإصدار العقد",use_container_width=True)
        if submit and no.strip():
            try: cid=x("INSERT INTO contracts(building_id,contract_no,contract_type,value,services_included,start_date,end_date,status,notes) VALUES(?,?,?,?,?,?,?,?,?)",(bm.get(bn),no,typ,value,services,start.isoformat(),end.isoformat(),status,notes)); x("INSERT INTO finance(type,category,description,amount,date,reference,contract_id) VALUES('إيراد','عقود صيانة عملاء',?,?,?,?,?)",(f"عقد صيانة عميل {no}",value,start.isoformat(),no,cid)); st.success("تم حفظ العقد وتسجيل إيراداته المتوقعة بالميزانية")
            except sqlite3.IntegrityError: st.error("رقم العقد مسجل مسبقاً")
    report_page("سجل عقود العملاء","SELECT c.contract_no AS 'رقم العقد',b.client AS 'العميل',b.name AS 'الموقع',c.contract_type AS 'النوع',c.value AS 'القيمة',c.start_date AS 'البداية',c.end_date AS 'النهاية',c.status AS 'الحالة' FROM contracts c LEFT JOIN buildings b ON b.id=c.building_id ORDER BY id DESC","client_contracts")

elif menu == "الموظفون":
    st.title("فريق العمل والكادر الفني والإداري")
    if not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    with st.form("employee"):
        a,b=st.columns(2)
        with a: name=st.text_input("اسم الموظف *"); nid=st.text_input("الرقم الشخصي"); phone=st.text_input("رقم الجوال"); role=st.selectbox("المسمى الوظيفي",ROLES); dept=st.selectbox("القسم الإداري",DEPARTMENTS)
        with b: hire=st.date_input("تاريخ التعيين",date.today()); salary=st.number_input("الراتب الشهري",0.0); status=st.selectbox("الحالة",["على رأس العمل","إجازة سنوية","موقوف","منتهي الخدمة"]); skills=st.text_input("المهارات التخصصية أو شهادات الاعتماد")
        notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ بيانات الموظف",use_container_width=True)
        if submit and name.strip(): x("INSERT INTO employees(name,national_id,phone,role,department,hire_date,salary,status,skills,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(name,nid,phone,role,dept,hire.isoformat(),salary,status,skills,notes)); st.success("تم حفظ بيانات الموظف")
    report_page("قائمة الموظفين","SELECT name AS 'الموظف',role AS 'الوظيفة',department AS 'القسم',phone AS 'الهاتف',salary AS 'الراتب',status AS 'الحالة' FROM employees ORDER BY id DESC","employees_report")

elif menu == "الحضور والدوام":
    st.title("حضور ودوام الكوادر الفنية والميدانية")
    if not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    emps=q("SELECT id,name,role FROM employees WHERE status='على رأس العمل'"); em={f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    with st.form("attendance"):
        en=st.selectbox("الموظف",list(em) or ["لا يوجد موظفون"]); status=st.selectbox("حالة الدوام",["حاضر بموقع الشركة أو المشروع","غائب","إجازة","مرضي","مهمة صيانة خارجية","تأخير عن الموعد"]); d=st.date_input("تاريخ اليوم",date.today()); hours=st.number_input("ساعات العمل الفعلية",0.0,24.0,8.0); notes=st.text_input("ملاحظات الحضور")
        if st.form_submit_button("تسجيل الحضور",use_container_width=True) and em:
            try: x("INSERT INTO attendance(emp_id,status,date,work_hours,notes) VALUES(?,?,?,?,?)",(em[en],status,d.isoformat(),hours,notes)); st.success("تم تسجيل الحضور بنجاح")
            except sqlite3.IntegrityError: st.error("تم تسجيل الحضور مسبقاً لهذا الموظف في هذا التاريخ")
    report_page("سجل الحضور والدوام","SELECT e.name AS 'الموظف',a.status AS 'الحالة',a.date AS 'التاريخ',a.work_hours AS 'الساعات',a.notes AS 'ملاحظات' FROM attendance a LEFT JOIN employees e ON e.id=a.emp_id ORDER BY a.date DESC","attendance_report")

elif menu == "الحسابات والفواتير":
    st.title("الحسابات المالية والفواتير وإيرادات العقود")
    if not has_access(user,"finance"): st.error("لا تملك الصلاحية."); st.stop()
    with st.form("finance"):
        a,b=st.columns(2)
        with a: typ=st.selectbox("نوع المعاملة المالية",["إيراد","مصروف"]); cat=st.selectbox("التصنيف المالي",["عقود صيانة عملاء","فواتير طلبات خدمة خارجية","رواتب وأجور الفنيين","شراء مواد وقطع غيار مشاريع","مصاريف تشغيلية ونقليات","إصلاحات ومقاولين باطن","أخرى"]); desc=st.text_input("بيان المعاملة المالية *")
        with b: amount=st.number_input("المبلغ (ر.ق / ر.س)",0.0); d=st.date_input("تاريخ المعاملة",date.today()); ref=st.text_input("رقم الفاتورة أو المرجع المرتبط")
        if st.form_submit_button("تسجيل المعاملة بالحسابات",use_container_width=True) and desc.strip() and amount>0: x("INSERT INTO finance(type,category,description,amount,date,reference) VALUES(?,?,?,?,?,?)",(typ,cat,desc,amount,d.isoformat(),ref)); st.success("تم حفظ المعاملة بنجاح")
    rev=float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='إيراد'").iloc[0,0]); exp=float(q("SELECT COALESCE(SUM(amount),0) n FROM finance WHERE type='مصروف'").iloc[0,0]); c1,c2,c3=st.columns(3); c1.markdown(metric("إجمالي إيرادات العقود والخدمات",f"{rev:,.2f} ر.ق"),unsafe_allow_html=True); c2.markdown(metric("إجمالي المصروفات التشغيلية",f"{exp:,.2f} ر.ق"),unsafe_allow_html=True); c3.markdown(metric("صافي أرباح الشركة",f"{rev-exp:,.2f} ر.ق"),unsafe_allow_html=True)
    report_page("السجل المالي الشامل","SELECT type AS 'النوع',category AS 'التصنيف',description AS 'البيان',amount AS 'المبلغ',date AS 'التاريخ',reference AS 'المرجع' FROM finance ORDER BY date DESC","finance_report")

elif menu == "التقارير":
    st.title("التقارير الإدارية والمالية الشاملة")
    if not has_access(user,"maintenance") and not has_access(user,"finance") and not has_access(user,"inventory") and not has_access(user,"hr"): st.error("لا تملك الصلاحية."); st.stop()
    choice=st.selectbox("اختر التقرير المطلوب استخراجه",["طلبات الصيانة الخارجية","أصول ومعدات العملاء","مستودع المواد","حركة المخزون والصرف","مشتريات الشركة","مواقع العملاء","عقود الصيانة","الموظفون","الحضور والدوام","الحسابات والمالية"])
    reports={"طلبات الصيانة الخارجية":("SELECT * FROM tasks ORDER BY id DESC","report_tasks"),"أصول ومعدات العملاء":("SELECT * FROM assets ORDER BY id DESC","report_assets"),"مستودع المواد":("SELECT * FROM materials ORDER BY id DESC","report_materials"),"حركة المخزون والصرف":("SELECT * FROM material_transactions ORDER BY id DESC","report_inventory"),"مشتريات الشركة":("SELECT * FROM purchases ORDER BY id DESC","report_purchases"),"مواقع العملاء":("SELECT * FROM buildings ORDER BY id DESC","report_buildings"),"عقود الصيانة":("SELECT * FROM contracts ORDER BY id DESC","report_contracts"),"الموظفون":("SELECT * FROM employees ORDER BY id DESC","report_employees"),"الحضور والدوام":("SELECT * FROM attendance ORDER BY id DESC","report_attendance"),"الحسابات والمالية":("SELECT * FROM finance ORDER BY id DESC","report_finance")}
    sql,name=reports[choice]; df=q(sql); st.dataframe(df,use_container_width=True,hide_index=True); exports(df,name,choice)

elif menu == "إدارة المستخدمين":
    st.title("إدارة المستخدمين وصلاحيات نظام الشركة الخارجية")
    if user["role"] != "مدير النظام": st.error("هذه الصفحة للمدير فقط."); st.stop()
    emps=q("SELECT id,name,role FROM employees"); em={f"{r['name']} ({r['role']})":r['id'] for _,r in emps.iterrows()}
    st.caption("حدد الأقسام التي يستطيع المستخدم رؤيتها من القائمة الرئيسية. مدير النظام يملك كافة الصلاحيات تلقائياً.")
    with st.form("user"):
        a,b=st.columns(2)
        with a:
            username=st.text_input("اسم المستخدم *")
            password=st.text_input("كلمة المرور *",type="password", key="create_user_password_secure_field")
            full=st.text_input("الاسم الظاهر *")
        with b:
            account_type=st.selectbox("نوع الحساب",["مستخدم مخصص","مدير النظام"])
            employee=st.selectbox("الموظف المرتبط بالحساب",["بدون"]+list(em))
            selected_sections=st.multiselect("صلاحيات القائمة الرئيسية", MAIN_MENU, default=["لوحة التحكم"])
        if st.form_submit_button("إضافة حساب المستخدم",use_container_width=True):
            if not username.strip() or not password or not full.strip():
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور والاسم الظاهر.")
            elif account_type != "مدير النظام" and not selected_sections:
                st.error("اختر قسماً واحداً على الأقل للمستخدم.")
            else:
                permissions="all" if account_type == "مدير النظام" else "|".join(dict.fromkeys([MENU_AREAS[s] for s in selected_sections] + ["dashboard"]))
                try:
                    x("INSERT INTO users(username,password_hash,full_name,role,employee_id,permissions,active,created_at) VALUES(?,?,?,?,?,?,1,?)",(username.strip(),hash_password(password),full,account_type,em.get(employee),permissions,datetime.now().isoformat()))
                    st.success("تمت إضافة المستخدم وتحديد صلاحياته بنجاح.")
                except sqlite3.IntegrityError: st.error("اسم المستخدم مسجل مسبقاً.")

    st.markdown("### المستخدمون المسجلون بالسيستم وإدارة الحسابات")
    users_list = q("SELECT id, username, full_name, role, active FROM users ORDER BY id DESC")
    
    header_cols = st.columns([2, 2, 1, 1, 1, 1])
    header_cols[0].markdown("**اسم المستخدم**")
    header_cols[1].markdown("**الاسم الظاهر**")
    header_cols[2].markdown("**نوع الحساب**")
    header_cols[3].markdown("**الحالة**")
    header_cols[4].markdown("**إزالة نهائية**")
    header_cols[5].markdown("**تعطيل / تفعيل**")
    st.markdown("---")

    for _, row in users_list.iterrows():
        uid_val = int(row["id"])
        is_me = (uid_val == int(user["id"]))
        
        cols = st.columns([2, 2, 1, 1, 1, 1])
        cols[0].text(row["username"])
        cols[1].text(row["full_name"])
        cols[2].text(row["role"])
        cols[3].text("نشط" if row["active"] == 1 else "معطل")
        
        if not is_me:
            if cols[4].button("حذف نهائي", key=f"del_{uid_val}", use_container_width=True):
                x("DELETE FROM users WHERE id=?", (uid_val,))
                st.success(f"تم حذف المستخدم {row['username']} بنجاح.")
                st.rerun()
            
            new_act = 0 if row["active"] == 1 else 1
            act_text = "تعطيل" if row["active"] == 1 else "تفعيل"
            if cols[5].button(act_text, key=f"toggle_{uid_val}", use_container_width=True):
                x("UPDATE users SET active=? WHERE id=?", (new_act, uid_val,))
                st.rerun()
        else:
            cols[4].text("(حسابك الحالي)")
            cols[5].text("-")

st.sidebar.markdown("---")
st.sidebar.caption("TIC TAC • External Services & Facilities • v4.0")
