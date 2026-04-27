import streamlit as st
from supabase import create_client, Client

# --- 1. الإعدادات ---
VERSION = "0.9"
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
    st.error("⚠️ تأكد من ضبط Secrets")
    st.stop()

# --- 3. تصميم نظيف جداً (RTL فقط) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .st-card {
        background: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. شاشة الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 دخول نظام السكن</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                # تسجيل دخول جهاز (بسيط جداً)
                try:
                    agent = st.context.headers.get("User-Agent", "جهاز مجهول")
                    dev = "iPhone" if "iPhone" in agent else "Android" if "Android" in agent else "PC"
                    supabase.table("login_logs").insert({"device_info": dev}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=2)
def load_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

s_list, t_list = load_data()

# --- 6. الواجهة الرئيسية (بدون Sidebar) ---
st.title("🏢 إدارة سكنات شكّور")

# وضعنا كل شيء في تبويبات عشان الموبايل يكون سهل
tab1, tab2, tab3 = st.tabs(["👥 الطالبات", "📊 الإحصائيات", "🛠️ ركن المطور"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        search_q = st.text_input("🔍 بحث بالاسم:")
    with col_b:
        choice = st.selectbox("📍 تصفية الشقق:", ["الكل"] + [s['name'] for s in s_list])

    filtered = t_list
    if choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower()]

    for s in filtered:
        sid = str(s['id'])
        wa = f"https://wa.me/962{str(s['phone'])[1:]}" if str(s['phone']).startswith('07') else "#"

        st.markdown(f"""
            <div class="st-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p>🏠 شقة: {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray;">📝 {s['notes'] if s['notes'] else 'لا يوجد ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2.5, 1.2])
        with c1: st.link_button("💬 واتساب", wa, use_container_width=True)
        with c2:
            fc = st.columns(3)
            files = [("هوية", 'file_id'), ("عقد", 'file_contract'), ("كمبيالة", 'file_kumbiala')]
            for i, (lab, col_n) in enumerate(files):
                if s.get(col_n):
                    url = supabase.storage.from_("student_files").get_public_url(s[col_n])
                    fc[i].link_button(lab, f"{url}?download=", key=f"f_{col_n}_{sid}")
                else:
                    fc[i].button(f"❌ {lab}", disabled=True, key=f"no_{col_n}_{sid}")
        with c3:
            with st.popover("⚙️ خيارات", use_container_width=True):
                n_v = st.text_input("الاسم", s['name'], key=f"n_{sid}")
                p_v = st.text_input("الهاتف", s['phone'], key=f"p_{sid}")
                m_v = st.text_area("الملاحظات", s['notes'], key=f"m_{sid}")
                if st.button("حفظ ✅", key=f"s_{sid}"):
                    supabase.table("students").update({"name": n_v, "phone": p_v, "notes": m_v}).eq("id", sid).execute()
                    st.rerun()
                if st.checkbox("تأكيد الحذف؟", key=f"c_{sid}"):
                    if st.button("حذف نهائي", key=f"d_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab2:
    st.metric("إجمالي الطالبات", len(t_list))
    st.metric("عدد الشقق", len(s_list))

with tab3:
    st.subheader("🛠️ سجلات الدخول")
    dev_code = st.text_input("أدخل رمز المطور لرؤية اللوجز:", type="password")
    if dev_code == DEV_LOG_PWD:
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            if logs.data:
                for l in logs.data:
                    st.write(f"🕒 {l['login_time'][11:16]} | الجهاز: **{l['device_info']}**")
            else: st.info("لا يوجد سجلات بعد.")
        except: st.error("تأكد من وجود جدول login_logs في سوبابيس.")

if st.button("🚪 تسجيل الخروج"):
    st.session_state["logged_in"] = False
    st.rerun()