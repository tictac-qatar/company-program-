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
ROLES = ["مدير النظام", "مدير صيانة المباني", "مدير العمليات", "مدير الموقع", "مشرف صيانة", "مهندس صيانة", "فني كهرباء", "فني تكييف HVAC", "فني سباكة", "فني مكافحة حريق", "فني مصاعد", "فني مولدات", "فني BMS", "فني CCTV وأمن", "فني شبكات", "فني مدني", "مسؤول سلامة HSE", "أمين مستودع", "محاسب", "مسؤول مشتريات", "مسؤول موارد بشرية", "سائق", "فني صيانة عامة"]
DEPARTMENTS = ["الإدارة", "الصيانة التشغيلية", "الفنيون والمهندسون", "السلامة HSE", "المستودعات", "المشتريات", "المالية والحسابات", "الموارد البشرية"]
CATEGORIES = ["مواد كهربائية", "مواد تكييف HVAC", "مواد سباكة وصرف", "مضخات وقطع غيار", "مكافحة وإنذار الحريق", "مولدات و UPS", "مصاعد", "BMS وتحكم", "CCTV وأمن", "شبكات واتصالات", "نجارة وأبواب", "ألومنيوم وزجاج", "دهانات", "جبس وأسقف", "عزل", "أعمال مدنية وبناء", "حدادة ولحام", "معدات مطابخ", "مواد نظافة", "معدات سلامة PPE", "قطع غيار عامة", "أخرى"]
UNITS = ["قطعة", "متر", "متر مربع", "متر مكعب", "كيلو", "لتر", "جالون", "علبة", "كرتون", "رول", "طقم", "وحدة"]
STATUSES = ["جديد", "تم التعيين", "قيد العمل", "بانتظار قطع غيار", "مكتمل", "ملغي"]

MAIN_MENU = ["لوحة التحكم", "أوامر الصيانة", "المخزون", "المشتريات", "المباني والعملاء", "العقود"]
MENU_AREAS = {"لوحة التحكم":"dashboard", "أوامر الصيانة":"maintenance", "المخزون":"inventory", "المشتريات":"purchases", "المباني والعملاء":"buildings", "العقود":"contracts"}
LEGACY_PERMISSIONS = {"مدير صيانة المباني": ["dashboard", "maintenance", "buildings", "contracts"], "مشرف صيانة": ["dashboard", "maintenance"], "مهندس صيانة": ["dashboard", "maintenance"], "مسؤول مشتريات": ["dashboard", "purchases", "inventory"], "أمين مستودع": ["dashboard", "inventory", "purchases"], "محاسب": ["dashboard", "finance", "contracts"]}

st.set_page_config(page_title="TIC TAC | صيانة المباني", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');
:root {{ --navy:{NAVY}; --navy-dark:{NAVY_DARK}; --copper:{COPPER}; --cream:{CREAM}; --ink:{INK}; }}
*, html, body, [class*="css"] {{ font-family:'Cairo', Tahoma, Arial, sans-serif !important; }}
.stApp {{ background:linear-gradient(135deg, #fff 0%, {CREAM} 100%); color:{INK}; direction:rtl; font-family:'Cairo', sans-serif !important; }}
.block-container {{ max-width:1500px; padding:1.4rem clamp(.7rem, 3vw, 3rem) 3rem; }}
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg, {NAVY_DARK}, {NAVY}); border-left:4px solid {COPPER}; font-family:'Cairo', sans-serif !important; }}
section[data-testid="stSidebar"] * {{ color:#fff !important; font-family:'Cairo', sans-serif !important; }}
[data-testid="stHeader"] {{ background:transparent; }}
.logo-card {{ background:{WHITE}; border:1px solid #e7ded4; border-top:6px solid {COPPER}; border-radius:18px; padding:18px 24px; display:flex; align-items:center; gap:22px; box-shadow:0 8px 24px rgba(23,50,77,.08); margin-bottom:22px; }}
.logo-card img {{ width:110px; max-height:88px; object-fit:contain; border-radius:10px; }}
.logo-title {{ color:{NAVY}; font-size:clamp(1.35rem,3vw,2.35rem); font-weight:800; line-height:1.35; font-family:'Cairo', sans-serif !important; }}
.logo-subtitle {{ color:{COPPER}; font-size:.95rem; font-weight:700; font-family:'Cairo', sans-serif !important; }}
.metric-card {{ background:#fff; border-right:5px solid {COPPER}; border-radius:14px; padding:15px; min-height:105px; box-shadow:0 5px 18px rgba(23,50,77,.07); }}
.metric-label {{ color:{MUTED}; font-size:.9rem; font-family:'Cairo', sans-serif !important; }} .metric-value {{ color:{NAVY}; font-size:1.7rem; font-weight:800; margin-top:5px; font-family:'Cairo', sans-serif !important; }}
div.stButton > button, .stDownloadButton > button {{ background:{NAVY} !important; color:#fff !important; border:0 !important; border-radius:9px !important; min-height:2.55rem; font-weight:700; font-family:'Cairo', sans-serif !important; }}
div.stButton > button:hover, .stDownloadButton > button:hover {{ background:{COPPER} !important; }}
input, textarea, [data-baseweb="select"] > div {{ border-radius:8px !important; font-family:'Cairo', sans-serif !important; }}
[data-testid="stDataFrame"] {{ border:1px solid #e5e7eb; border-radius:10px; font-family:'Cairo', sans-serif !important; }}
.stCode, code, pre, textarea, input {{ color: {INK} !important; font-family:'Cairo', sans-serif !important; }}
.stCodeBlock {{ background-color: {WHITE} !important; color: {INK} !important; border: 1px solid #e7ded4; }}
@media (max-width: 700px) {{ .block-container {{ padding:.7rem .55rem 2rem; }} .logo-card {{ flex-direction:column; text-align:center; padding:14px; }} .logo-card img {{ width:150px; }} [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; gap:.5rem; }} [data-testid="stHorizontalBlock"] > div {{ min-width:calc(50% - .5rem) !important; flex:1 1 calc(50% - .5rem) !important; }} section[data-testid="stSidebar"] {{ width: min(85vw, 320px); }} .stDataFrame {{ font-size:.75rem; }} }}
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
    st.markdown('<div class="logo-card"><div class="logo-title">TIC TAC<br><span class="logo-subtitle">نظام إدارة صيانة المباني والمرافق</span></div></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("### تسجيل الدخول")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
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
    vals = [q("SELECT COUNT(*) n FROM tasks").iloc[0,0], q("SELECT COUNT(*) n FROM tasks WHERE status NOT IN ('مكتمل','ملغي')").iloc[0,0], q("SELECT COUNT(*) n FROM buildings").iloc[0,0], q("SELECT COUNT(*) n FROM materials WHERE quantity<=min_quantity").iloc[0,0]]
    cols = st.columns(4)
    for c, label, val in zip(cols, ["إجمالي البلاغات", "بلاغات مفتوحة", "المباني", "مخزون منخفض"], vals): c.markdown(metric(label, val), unsafe_allow_html=True)
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

elif menu == "المخزون":
    st.title("إدارة المخزون وقطع الغيار")
    if not has_access(user,"inventory"): st.error("لا تملك صلاحية الوصول لهذا القسم."); st.stop()
    
    tab1, tab2 = st.tabs(["قائمة المواد وقطع الغيار", "حركة المخزون"])
    
    with tab1:
        with st.form("material"):
            a,b=st.columns(2)
            with a: code=st.text_input("كود المادة *"); name=st.text_input("الاسم العربي *"); english=st.text_input("الاسم الإنجليزي"); category=st.selectbox("التصنيف",CATEGORIES); unit=st.selectbox("الوحدة",UNITS); qty=st.number_input("الرصيد",0.0); minimum=st.number_input("الحد الأدنى",0.0)
            with b: reorder=st.number_input("حد إعادة الطلب",0.0); price=st.number_input("سعر الشراء",0.0); cost=st.number_input("متوسط التكلفة",0.0); supplier=st.text_input("المورد"); storage=st.text_input("المستودع / الرف"); part=st.text_input("رقم القطعة / الموديل")
            notes=st.text_area("ملاحظات"); submit=st.form_submit_button("حفظ المادة",use_container_width=True)
            if submit and code.strip() and name.strip():
                try: x("INSERT INTO materials(item_code,arabic_name,english_name,category,unit,quantity,min_quantity,reorder_point,purchase_price,avg_cost,supplier,storage_location,part_no,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(code,name,english,category,unit,qty,minimum,reorder,price,cost,supplier,storage,part,notes)); st.success("تم حفظ المادة")
                except sqlite3.IntegrityError: st.error("كود المادة موجود مسبقاً")
        df_mat=q("SELECT item_code AS 'الكود',arabic_name AS 'المادة',category AS 'التصنيف',unit AS 'الوحدة',quantity AS 'الرصيد',min_quantity AS 'الحد الأدنى',supplier AS 'المورد',storage_location AS 'الموقع' FROM materials ORDER BY id DESC")
        st.dataframe(df_mat,use_container_width=True,hide_index=True); exports(df_mat,"materials","المواد وقطع الغيار")

    with tab2:
        mats=q("SELECT id,item_code,arabic_name,quantity FROM materials"); mm={f"{r['item_code']} - {r['arabic_name']} (الرصيد {r['quantity']})":r['id'] for _,r in mats.iterrows()}
        with st.form("transaction"):
            selected=st.selectbox("المادة",list(mm) or ["لا توجد مواد"]); typ=st.selectbox("نوع الحركة",["إضافة شراء","صرف لأمر صيانة","مرتجع","تسوية زيادة","تسوية نقص"]); qty_t=st.number_input("الكمية",0.01); cost_t=st.number_input("سعر الوحدة",0.0); ref=st.text_input("المرجع"); notes_t=st.text_area("ملاحظات الحركة")
            if st.form_submit_button("تنفيذ الحركة",use_container_width=True) and mm:
                mid=mm[selected]; old=float(q("SELECT quantity FROM materials WHERE id=?",(mid,)).iloc[0,0]); new=old+qty_t if typ in ["إضافة شراء","مرتجع","تسوية زيادة"] else old-qty_t
                if new<0: st.error("الرصيد غير كافٍ")
                else: x("UPDATE materials SET quantity=? WHERE id=?",(new,mid)); x("INSERT INTO material_transactions(material_id,transaction_type,quantity,unit_cost,reference,date,notes) VALUES(?,?,?,?,?,?,?)",(mid,typ,qty_t,cost_t,ref,date.today().isoformat(),notes_t)); st.success(f"تم تحديث الرصيد إلى {new}")
        df_trans=q("SELECT mt.transaction_type AS 'الحركة',m.arabic_name AS 'المادة',mt.quantity AS 'الكمية',mt.unit_cost AS 'السعر',mt.reference AS 'المرجع',mt.date AS 'التاريخ' FROM material_transactions mt LEFT JOIN materials m ON m.id=mt.material_id ORDER BY mt.id DESC")
        st.dataframe(df_trans,use_container_width=True,hide_index=True); exports(df_trans,"inventory_transactions","حركة المخزون")

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
    if not has_access(user,"maintenance") and not has_access(user,"purchases"): st.error("لا تملك الصلاحية."); st.stop()
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

elif menu == "إدارة المستخدمين":
    st.title("إدارة المستخدمين والصلاحيات")
    if user["role"] != "مدير النظام": st.error("هذه الصفحة للمدير فقط."); st.stop()
    st.caption("حدد الأقسام التي يستطيع المستخدم رؤيتها من القائمة الرئيسية. مدير النظام يملك جميع الصلاحيات تلقائياً.")
    with st.form("user"):
        a,b=st.columns(2)
        with a:
            username=st.text_input("اسم المستخدم *")
            password=st.text_input("كلمة المرور *",type="password")
            full=st.text_input("الاسم الظاهر *")
        with b:
            account_type=st.selectbox("نوع الحساب",["مستخدم مخصص","مدير النظام"])
            selected_sections=st.multiselect("صلاحيات القائمة الرئيسية", MAIN_MENU, default=["لوحة التحكم"])
        if st.form_submit_button("إضافة المستخدم",use_container_width=True):
            if not username.strip() or not password or not full.strip():
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور والاسم الظاهر.")
            elif account_type != "مدير النظام" and not selected_sections:
                st.error("اختر قسماً واحداً على الأقل للمستخدم.")
            else:
                permissions="all" if account_type == "مدير النظام" else "|".join(dict.fromkeys([MENU_AREAS[s] for s in selected_sections] + ["dashboard"]))
                try:
                    x("INSERT INTO users(username,password_hash,full_name,role,permissions,active,created_at) VALUES(?,?,?,?,?,1,?)",(username.strip(),hash_password(password),full,account_type,permissions,datetime.now().isoformat()))
                    st.success("تمت إضافة المستخدم والصلاحيات بنجاح.")
                except sqlite3.IntegrityError: st.error("اسم المستخدم موجود مسبقاً.")

    st.markdown("### المستخدمون المسجلون وإدارة الحسابات")
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
st.sidebar.caption("TIC TAC • Building Maintenance • v4.0")
