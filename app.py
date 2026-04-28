import streamlit as st
from supabase import create_client, Client

# --- 1. الإعدادات والنسخة ---
VERSION = "0.2"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="سكنات شكّور v0.2", 
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
    st.error("⚠️ تأكد من إعدادات Secrets في Streamlit Cloud.")
    st.stop()

# --- 3. تصميم CSS (ثابت ومريح للعين) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .st-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }
    .status-badge {
        padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold;
    }
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
                    # تسجيل صامت للجهاز في ركن المطور
                    ua = st.context.headers.get("User-Agent", "")
                    dev = "iPhone" if "iPhone" in ua else "Android" if "Android" in ua else "PC"
                    supabase.table("login_logs").insert({"device_info": dev}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=2)
def load_full_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    # نجلب جميع الطلاب (المحذوفين وغير المحذوفين)
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

s_list, all_students = load_full_data()

# --- 6. الواجهة الرئيسية (التبويبات) ---
st.title("🏢 لوحة تحكم سكنات شكّور")

tab1, tab2, tab3, tab4 = st.tabs(["👥 إدارة الطالبات", "🗑️ سلة المحذوفات", "📊 الإحصائيات", "🛠️ ركن المطور"])

# --- التبويب الأول: الإدارة والنقل ---
with tab1:
    c1, c2 = st.columns([2, 1])
    search_q = c1.text_input("🔍 بحث بالاسم:")
    choice = c2.selectbox("📍 تصفية حسب الشقة:", ["الكل"] + [s['name'] for s in s_list])

    # تصفية الطالبات النشطات فقط (is_deleted == False)
    active_students = [s for s in all_students if not s.get('is_deleted', False)]
    
    filtered = active_students
    if choice != "الكل":
        filtered = [s for s in active_students if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower()]

    for s in filtered:
        sid = str(s['id'])
        wa = f"https://wa.me/962{str(s['phone'])[1:]}" if str(s['phone']).startswith('07') else "#"
        
        # تحسين (1): مؤشر اكتمال الملفات (الميزة التحسينية)
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
            if st.button("⚙️ خيارات", key=f"opt_{sid}", use_container_width=True):
                st.session_state[f"edit_{sid}"] = not st.session_state.get(f"edit_{sid}", False)

        if st.session_state.get(f"edit_{sid}", False):
            with st.container():
                st.info("إجراءات سريعة:")
                # ميزة نقل طالب إلى سكن آخر
                new_apt = st.selectbox("🚚 نقل إلى سكن جديد:", [s['name'] for s in s_list if s['name'] != s.get('sakanat', {}).get('name')], key=f"move_{sid}")
                if st.button("تأكيد النقل", key=f"btn_move_{sid}"):
                    target_apt = next(item for item in s_list if item["name"] == new_apt)
                    supabase.table("students").update({"sakan_id": target_apt['id']}).eq("id", sid).execute()
                    st.success(f"تم نقل الطالبة إلى {new_apt}")
                    st.rerun()
                
                st.markdown("---")
                # تعديل البيانات
                en = st.text_input("تعديل الاسم", s['name'], key=f"en_{sid}")
                em = st.text_area("تعديل الملاحظات", s['notes'], key=f"em_{sid}")
                if st.button("حفظ التعديلات ✅", key=f"sv_{sid}"):
                    supabase.table("students").update({"name": en, "notes": em}).eq("id", sid).execute()
                    st.rerun()
                
                # ميزة الحذف الناعم (النقل للسلة)
                if st.button("🗑️ نقل إلى سلة المحذوفات", key=f"soft_del_{sid}", type="primary"):
                    supabase.table("students").update({"is_deleted": True}).eq("id", sid).execute()
                    st.rerun()

# --- التبويب الثاني: سلة المحذوفات ---
with tab2:
    st.subheader("🗑️ سلة المحذوفات")
    deleted_ones = [s for s in all_students if s.get('is_deleted', False)]
    
    if not deleted_ones:
        st.info("السلة فارغة حالياً.")
    
    for ds in deleted_ones:
        dsid = str(ds['id'])
        st.markdown(f"""
            <div style="background:#F9EBEA; padding:15px; border-radius:10px; border-right:5px solid #C0392B; margin-bottom:10px;">
                <h4 style="margin:0;">👤 {ds['name']}</h4>
                <p style="font-size:13px; color:gray;">سكن سابق: {ds.get('sakanat', {}).get('name', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c_res, c_perm = st.columns(2)
        if c_res.button("🔄 استرجاع الطالبة", key=f"res_{dsid}", use_container_width=True):
            supabase.table("students").update({"is_deleted": False}).eq("id", dsid).execute()
            st.rerun()
        
        if c_perm.button("❌ حذف نهائي (للأبد)", key=f"perm_{dsid}", use_container_width=True):
            if st.checkbox("أنا متأكد، احذف البيانات نهائياً", key=f"chk_{dsid}"):
                supabase.table("students").delete().eq("id", dsid).execute()
                st.rerun()

# --- التبويب الثالث: الإحصائيات ---
with tab3:
    st.metric("إجمالي الطالبات النشطات", len(active_students))
    st.metric("عدد الشقق", len(s_list))

# --- التبويب الرابع: ركن المطور ---
with tab4:
    dev_code = st.text_input("أدخل رمز الوصول:", type="password")
    if dev_code == DEV_LOG_PWD:
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            for l in logs.data:
                st.write(f"🕒 {l['login_time'][11:16]} | الجهاز: **{l['device_info']}**")
        except: st.error("تأكد من وجود جدول login_logs")

# تسجيل الخروج
if st.button("🚪 تسجيل الخروج"):
    st.session_state["logged_in"] = False
    st.rerun()

st.caption(f"v{VERSION} | {DEV_NAME}")