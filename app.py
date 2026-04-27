import streamlit as st
from supabase import create_client, Client

# --- 1. الإعدادات ---
VERSION = "0.7"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(page_title="سكنات شكّور", layout="wide")

# --- 2. الربط ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ تأكد من Secrets")
    st.stop()

# --- 3. تصميم بسيط ومستقر (عشان ما تخرب الشاشة) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="st-"], p, h1, h2, h3 {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    .student-card {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-right: 5px solid #2E86C1;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 دخول سكنات شكّور</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                # تسجيل دخول جهاز (طريقة مباشرة)
                try:
                    supabase.table("login_logs").insert({"device_info": "دخول جديد"}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ خطأ")
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=2)
def load_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

s_list, t_list = load_data()

# --- 6. القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ الإدارة")
    search_q = st.text_input("🔍 بحث:")
    st.markdown("---")
    # اللوجز
    st.write("🛠️ ركن المطور")
    d_pwd = st.text_input("الرمز", type="password")
    if d_pwd == DEV_LOG_PWD:
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
            for l in logs.data:
                st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
        except: st.error("تأكد من وجود جدول login_logs")
    
    if st.button("🚪 خروج"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 7. العرض ---
tab1, tab2 = st.tabs(["👥 الطالبات", "📊 إحصائيات"])

with tab1:
    s_names = ["الكل"] + [s['name'] for s in s_list]
    choice = st.selectbox("📍 الشقة:", s_names)
    
    filtered = t_list
    if choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower()]

    for s in filtered:
        sid = str(s['id'])
        wa = f"https://wa.me/962{str(s['phone'])[1:]}" if str(s['phone']).startswith('07') else "#"

        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">{s['name']}</h3>
                <p>🏠 شقة: {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray;">📝 {s['notes'] if s['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: st.link_button("💬 واتساب", wa)
        with c2:
            fc = st.columns(3)
            files = [("هوية", 'file_id'), ("عقد", 'file_contract'), ("كمبيالة", 'file_kumbiala')]
            for i, (lab, col) in enumerate(files):
                if s.get(col):
                    url = supabase.storage.from_("student_files").get_public_url(s[col])
                    fc[i].link_button(lab, f"{url}?download=")
                else: fc[i].button(f"❌ {lab}", disabled=True)
        with c3:
            with st.popover("⚙️"):
                n_v = st.text_input("الاسم", s['name'], key=f"n{sid}")
                p_v = st.text_input("الهاتف", s['phone'], key=f"p{sid}")
                m_v = st.text_area("ملاحظات", s['notes'], key=f"m{sid}")
                if st.button("حفظ", key=f"s{sid}"):
                    supabase.table("students").update({"name":n_v, "phone":p_v, "notes":m_v}).eq("id", sid).execute()
                    st.rerun()
                if st.checkbox("حذف؟", key=f"c{sid}"):
                    if st.button("تأكيد", key=f"d{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab2:
    st.metric("إجمالي الطالبات", len(t_list))

st.caption(f"v{VERSION} | {DEV_NAME}")