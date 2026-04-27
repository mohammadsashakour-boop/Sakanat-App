import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. الإعدادات ---
VERSION = "0.5"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="سكنات شكّور", 
    layout="wide", 
    initial_sidebar_state="collapsed" # تبدأ مخفية عشان ما تزعجك على الموبايل
)

# --- 2. الربط بالسيرفر ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ خطأ في الإعدادات السرية (Secrets).")
    st.stop()

# --- 3. تصميم CSS نظيف (يحافظ على استقرار الشاشة) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    
    /* تطبيق الخط العربي والاتجاه على النصوص فقط لضمان عدم تشوه الأيقونات */
    .stMarkdown, .stHeader, .stButton, .stTextInput, .stTextArea, .stSelectbox, p, h1, h2, h3 {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* تصميم البطاقة بشكل ثابت */
    .student-card {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-right: 8px solid #2E86C1;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. شاشة الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 دخول سكنات شكّور</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd_in = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        if st.button("دخول للنظام", use_container_width=True) or (pwd_in == ADMIN_PWD and pwd_in != ""):
            if pwd_in == ADMIN_PWD:
                st.session_state["logged_in"] = True
                st.rerun()
            elif pwd_in != "": 
                st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. وظيفة تسجيل الجهاز (مطورة لتفادي مسح الـ JS) ---
def log_device_now():
    if "device_logged" not in st.session_state:
        # نجلب معلومات الجهاز
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

# تشغيل التسجيل
log_device_now()

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
    st.write(f"المطور: **{DEV_NAME}**")
    search_q = st.text_input("🔍 بحث (اسم/هاتف):")
    st.markdown("---")
    
    # إصلاح ركن المطور واللوجز
    st.markdown("### 🛠️ ركن المطور")
    dev_key = st.text_input("رمز المطور", type="password")
    if dev_key == DEV_LOG_PWD:
        st.success("أهلاً يا مطور")
        try:
            # زر للتحديث اليدوي للوجز
            if st.button("تحديث وعرض اللوجز 🔄"):
                st.session_state.pop("device_logged", None) # نجبره يحاول يسجل مرة ثانية
                st.rerun()
            
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
            for l in logs.data:
                st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
        except Exception as e:
            st.write("خطأ في جلب اللوجز")
            
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية (Tabs) ---
tab1, tab2 = st.tabs(["👥 الطالبات", "📊 ملخص"])

with tab1:
    # فلترة
    choice = st.selectbox("📍 تصفية الشقق:", ["الكل"] + [s['name'] for s in s_list])
    
    filtered = t_list
    if choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower() or search_q in str(s['phone'])]

    for s in filtered:
        sid = str(s['id'])
        # واتساب
        p = str(s['phone']).replace(' ', '').replace('+', '')
        wa = f"https://wa.me/962{p[1:]}" if p.startswith('07') else f"https://wa.me/{p}"

        # كرت الطالبة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0;">🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 <b>ملاحظات:</b> {s['notes'] if s['notes'] else 'لا يوجد'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار
        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c1: st.link_button("💬 واتساب", wa, use_container_width=True)
        with c2:
            f_cols = st.columns(3)
            files = [("هوية", 'file_id'), ("عقد", 'file_contract'), ("كمبيالة", 'file_kumbiala')]
            for i, (lab, col_name) in enumerate(files):
                path = s.get(col_name)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    f_cols[i].link_button(lab, f"{url}?download=", use_container_width=True)
                else: f_cols[i].button(f"❌ {lab}", key=f"x_{col_name}_{sid}", disabled=True, use_container_width=True)
        
        with c3:
            with st.popover("⚙️ خيارات"):
                st.write("🛠️ **تعديل**")
                n_v = st.text_input("الاسم", s['name'], key=f"n_{sid}")
                p_v = st.text_input("الهاتف", s['phone'], key=f"p_{sid}")
                m_v = st.text_area("ملاحظات", s['notes'], key=f"m_{sid}")
                if st.button("حفظ", key=f"s_{sid}"):
                    supabase.table("students").update({"name": n_v, "phone": p_v, "notes": m_v}).eq("id", sid).execute()
                    st.rerun()
                st.markdown("---")
                if st.checkbox("تأكيد الحذف؟", key=f"c_{sid}"):
                    if st.button("حذف نهائي", key=f"d_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab2:
    st.metric("إجمالي الطالبات", len(t_list))
    st.metric("عدد الشقق", len(s_list))

st.caption(f"Developed by {DEV_NAME} | v{VERSION}")