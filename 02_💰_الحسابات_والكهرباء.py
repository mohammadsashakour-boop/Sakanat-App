import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. إعدادات النظام ---
VERSION = "0.2.1"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="نظام سكنات شكّور المطور", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. الربط بالسيرفر ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ تأكد من ضبط Secrets في Streamlit Cloud.")
    st.stop()

# --- 3. تصميم CSS (ثبات كامل) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .st-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }
    .status-badge { padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. شاشة الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 نظام إدارة السكن</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                try:
                    ua = st.context.headers.get("User-Agent", "")
                    dev = "iPhone" if "iPhone" in ua else "Android" if "Android" in ua else "PC"
                    supabase.table("login_logs").insert({"device_info": dev}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. وظائف مساعدة (رفع وحذف الملفات) ---
def upload_file(file, student_name, file_type):
    file_ext = file.name.split('.')[-1]
    file_path = f"{student_name}_{file_type}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    res = supabase.storage.from_("student_files").upload(file_path, file.read())
    return file_path

def delete_file(file_path):
    try: supabase.storage.from_("student_files").remove([file_path])
    except: pass

# --- 6. جلب البيانات ---
@st.cache_data(ttl=2)
def load_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

s_list, all_students = load_data()

# --- 7. الواجهة الرئيسية ---
st.title("🏢 لوحة تحكم سكنات شكّور")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 إدارة الطالبات", "➕ إضافة طالبة", "🗑️ سلة المحذوفات", "📊 إحصائيات", "🛠️ ركن المطور"])

# --- التبويب الأول: الإدارة والنقل والملفات ---
with tab1:
    c1, c2, c3 = st.columns([2, 1, 1])
    search_q = c1.text_input("🔍 بحث بالاسم:")
    choice = c2.selectbox("📍 تصفية الشقق:", ["الكل"] + [s['name'] for s in s_list])
    filter_missing = c3.toggle("⚠️ عرض النواقص فقط")

    active_students = [s for s in all_students if not s.get('is_deleted', False)]
    filtered = active_students
    if choice != "الكل":
        filtered = [s for s in filtered if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower()]
    if filter_missing:
        filtered = [s for s in filtered if not all([s.get('file_id'), s.get('file_contract'), s.get('file_kumbiala')])]

    for s in filtered:
        sid = str(s['id'])
        wa = f"https://wa.me/962{str(s['phone'])[1:]}" if str(s['phone']).startswith('07') else "#"
        files_ok = all([s.get('file_id'), s.get('file_contract'), s.get('file_kumbiala')])
        status_html = "<span class='status-badge' style='background:#D4EFDF; color:#1D8348;'>✅ مكتمل</span>" if files_ok else "<span class='status-badge' style='background:#FADBD8; color:#943126;'>⚠️ نقص ملفات</span>"

        st.markdown(f"""
            <div class="st-card">
                <div style="display:flex; justify-content:space-between;">
                    <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                    {status_html}
                </div>
                <p>🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 {s['notes'] if s['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_wa, col_files, col_opts = st.columns([1, 2.5, 1])
        with col_wa: st.link_button("💬 WhatsApp", wa, use_container_width=True)
        with col_files:
            f_cols = st.columns(3)
            for i, (lab, col_n) in enumerate([("هوية", "file_id"), ("عقد", "file_contract"), ("كمبيالة", "file_kumbiala")]):
                if s.get(col_n):
                    u = supabase.storage.from_("student_files").get_public_url(s[col_n])
                    f_cols[i].link_button(lab, f"{u}?download=", key=f"f_{col_n}_{sid}")
                else: f_cols[i].button(f"❌ {lab}", disabled=True, key=f"n_{col_n}_{sid}")

        with col_opts:
            if st.button("⚙️ إعدادات", key=f"opt_{sid}", use_container_width=True):
                st.session_state[f"edit_{sid}"] = not st.session_state.get(f"edit_{sid}", False)

        if st.session_state.get(f"edit_{sid}", False):
            with st.expander("🛠️ تعديل البيانات والملفات", expanded=True):
                # 1. تعديل البيانات الأساسية
                c_e1, c_e2 = st.columns(2)
                en = c_e1.text_input("الاسم", s['name'], key=f"en_{sid}")
                ep = c_e2.text_input("الهاتف", s['phone'], key=f"ep_{sid}")
                em = st.text_area("الملاحظات", s['notes'], key=f"em_{sid}")
                if st.button("حفظ البيانات الأساسية ✅", key=f"sv_data_{sid}"):
                    supabase.table("students").update({"name": en, "phone": ep, "notes": em}).eq("id", sid).execute()
                    st.rerun()

                st.markdown("---")
                # 2. إدارة الملفات (إضافة، تبديل، حذف)
                st.write("📂 **إدارة المستندات:**")
                f1, f2, f3 = st.columns(3)
                cols_files = [("file_id", "هوية", f1), ("file_contract", "عقد", f2), ("file_kumbiala", "كمبيالة", f3)]
                
                for db_col, label, column in cols_files:
                    with column:
                        if s.get(db_col):
                            st.success(f"تم رفع {label}")
                            if st.button(f"حذف {label}", key=f"del_f_{db_col}_{sid}"):
                                delete_file(s[db_col])
                                supabase.table("students").update({db_col: None}).eq("id", sid).execute()
                                st.rerun()
                        else:
                            new_f = st.file_uploader(f"رفع {label}", key=f"up_{db_col}_{sid}")
                            if new_f:
                                f_path = upload_file(new_f, s['name'], db_col)
                                supabase.table("students").update({db_col: f_path}).eq("id", sid).execute()
                                st.rerun()

                st.markdown("---")
                # 3. نقل السكن والحذف
                c_m1, c_m2 = st.columns(2)
                new_apt = c_m1.selectbox("🚚 نقل لشقة أخرى:", [apt['name'] for apt in s_list if apt['name'] != s.get('sakanat', {}).get('name')], key=f"move_{sid}")
                if c_m1.button("تأكيد النقل", key=f"btn_move_{sid}"):
                    target = next(item for item in s_list if item["name"] == new_apt)
                    supabase.table("students").update({"sakan_id": target['id']}).eq("id", sid).execute()
                    st.rerun()
                
                if c_m2.button("🗑️ نقل للسلة", key=f"soft_del_{sid}", type="primary", use_container_width=True):
                    supabase.table("students").update({"is_deleted": True}).eq("id", sid).execute()
                    st.rerun()

# --- التبويب الثاني: إضافة طالبة جديدة ---
with tab2:
    st.subheader("➕ تسجيل طالبة جديدة")
    with st.form("add_student_form", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        new_name = col_n1.text_input("اسم الطالبة المزدوج*")
        new_phone = col_n2.text_input("رقم الهاتف*")
        new_apt_name = st.selectbox("الشقة*", [s['name'] for s in s_list])
        new_notes = st.text_area("ملاحظات إضافية")
        
        st.write("📄 رفع الملفات الأولية (اختياري):")
        f_id = st.file_uploader("رفع الهوية", type=['pdf', 'jpg', 'png'])
        f_con = st.file_uploader("رفع العقد", type=['pdf', 'jpg', 'png'])
        f_kum = st.file_uploader("رفع الكمبيالة", type=['pdf', 'jpg', 'png'])
        
        if st.form_submit_button("تسجيل الطالبة ✅"):
            if new_name and new_phone:
                target_apt = next(item for item in s_list if item["name"] == new_apt_name)
                
                # رفع الملفات
                p_id = upload_file(f_id, new_name, "id") if f_id else None
                p_con = upload_file(f_con, new_name, "contract") if f_con else None
                p_kum = upload_file(f_kum, new_name, "kumbiala") if f_kum else None
                
                supabase.table("students").insert({
                    "name": new_name, "phone": new_phone, "notes": new_notes,
                    "sakan_id": target_apt['id'], "is_deleted": False,
                    "file_id": p_id, "file_contract": p_con, "file_kumbiala": p_kum
                }).execute()
                st.success("تم تسجيل الطالبة بنجاح!")
                st.rerun()
            else: st.error("يرجى ملء الحقول المطلوبة (*)")

# --- التبويب الثالث: سلة المحذوفات ---
with tab3:
    st.subheader("🗑️ سلة المحذوفات")
    deleted_ones = [s for s in all_students if s.get('is_deleted', False)]
    if not deleted_ones: st.info("السلة فارغة.")
    for ds in deleted_ones:
        dsid = str(ds['id'])
        st.markdown(f"<div class='st-card' style='border-right-color:red;'><h4>👤 {ds['name']}</h4></div>", unsafe_allow_html=True)
        c_res, c_perm = st.columns(2)
        if c_res.button("🔄 استرجاع", key=f"res_{dsid}"):
            supabase.table("students").update({"is_deleted": False}).eq("id", dsid).execute()
            st.rerun()
        if c_perm.button("❌ حذف أبدي", key=f"perm_{dsid}"):
            if st.checkbox("تأكيد؟", key=f"chk_{dsid}"):
                supabase.table("students").delete().eq("id", dsid).execute()
                st.rerun()

# --- التبويب الرابع والخامس: إحصائيات وركن المطور ---
with tab4:
    st.metric("الطالبات النشطات", len(active_students))
    st.metric("إجمالي الشقق", len(s_list))

with tab5:
    dev_code = st.text_input("رمز الوصول:", type="password")
    if dev_code == DEV_LOG_PWD:
        logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
        for l in logs.data: st.write(f"🕒 {l['login_time'][11:16]} | الجهاز: {l['device_info']}")

if st.button("🚪 خروج"):
    st.session_state["logged_in"] = False
    st.rerun()

st.caption(f"v{VERSION} | {DEV_NAME}")
