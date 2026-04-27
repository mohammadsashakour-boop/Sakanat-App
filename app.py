import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. الإعدادات الأساسية ---
VERSION = "0.3"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="سكنات شكّور", 
    layout="wide", 
    initial_sidebar_state="collapsed", # تبدأ مخفية عشان ما تزعجك
    page_icon="🏢"
)

# --- 2. الربط بالسيرفر ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ خطأ في الإعدادات السرية.")
    st.stop()

# --- 3. تصميم CSS نظيف (بدون قلب الإيقونات) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    
    /* قلب النصوص فقط وليس الإيقونات لتجنب التشويه */
    .stMarkdown, .stHeader, .stButton, .stTextInput, .stSelectbox, p, h1, h2, h3 {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .student-card {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-right: 6px solid #2E86C1;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. وظيفة اللوجز ---
def log_device():
    if "device_logged" not in st.session_state:
        ua = st_javascript("window.navigator.userAgent")
        if ua and ua != "null":
            device = "جهاز غير معروف"
            if "iPhone" in str(ua): device = "iPhone 📱"
            elif "Android" in str(ua): device = "Android 📱"
            elif "Windows" in str(ua): device = "Windows PC 💻"
            try:
                supabase.table("login_logs").insert({"device_info": device}).execute()
                st.session_state["device_logged"] = True
            except: pass

# --- 5. شاشة الدخول (تدعم Enter) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 دخول سكنات شكّور</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        pwd = st.text_input("كلمة السر الإدارية", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                log_device()
                st.rerun()
            elif pwd != "": st.error("❌ كلمة السر خطأ")
    st.stop()

# --- 6. جلب البيانات ---
@st.cache_data(ttl=2)
def load_data():
    s_res = supabase.table("sakanat").select("*").order('name').execute()
    t_res = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_res.data, t_res.data

s_list, t_list = load_data()

# --- 7. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("⚙️ الإدارة")
    st.write(f"المطور: {DEV_NAME}")
    search_q = st.text_input("🔍 بحث بالاسم أو الهاتف:")
    st.markdown("---")
    
    # تصليح قسم المطور
    st.write("🛠️ ركن المطور")
    d_pwd = st.text_input("رمز المطور", type="password", key="dev_pwd")
    if d_pwd == DEV_LOG_PWD:
        try:
            l_data = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
            for l in l_data.data:
                st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
        except: st.write("لا يوجد سجلات")
    
    if st.button("🚪 تسجيل خروج"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية (Tabs) ---
tab1, tab2 = st.tabs(["👥 الطالبات", "📊 إحصائيات"])

with tab1:
    s_names = ["الكل"] + [s['name'] for s in s_list]
    choice = st.selectbox("📍 اختر الشقة:", s_names)

    filtered = t_list
    if choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower() or search_q in str(s['phone'])]

    for s in filtered:
        sid = str(s['id'])
        phone = str(s['phone']).replace(' ', '').replace('+', '')
        wa_url = f"https://wa.me/962{phone[1:]}" if phone.startswith('07') else f"https://wa.me/{phone}"

        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">{s['name']}</h3>
                <p>🏠 شقة: {s.get('sakanat', {}).get('name', 'N/A')} | 📞 هاتف: {s['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 ملاحظات: {s['notes'] if s['notes'] else 'لا يوجد'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: st.link_button("💬 واتساب", wa_url, use_container_width=True)
        with c2:
            f_cols = st.columns(3)
            files = [("الهوية", 'file_id'), ("العقد", 'file_contract'), ("الكمبيالة", 'file_kumbiala')]
            for i, (lab, col) in enumerate(files):
                path = s.get(col)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    f_cols[i].link_button(lab, f"{url}?download=", use_container_width=True)
                else: f_cols[i].button(f"❌ {lab}", key=f"n_{col}_{sid}", disabled=True, use_container_width=True)
        with c3:
            # دمج التعديل والحذف في بوب اوفر واحد عشان ما يتلخبط الموبايل
            with st.popover("⚙️ خيارات"):
                # التعديل
                new_n = st.text_input("تعديل الاسم", s['name'], key=f"en_{sid}")
                if st.button("حفظ الاسم", key=f"btn_s_{sid}"):
                    supabase.table("students").update({"name": new_n}).eq("id", sid).execute()
                    st.rerun()
                st.markdown("---")
                # الحذف
                if st.checkbox("تأكيد حذف الطالبة؟", key=f"c_{sid}"):
                    if st.button("حذف نهائي ❌", key=f"d_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab2:
    st.metric("عدد الطالبات", len(t_list))
    st.metric("عدد الشقق", len(s_list))

st.caption(f"تطوير {DEV_NAME} | v{VERSION}")