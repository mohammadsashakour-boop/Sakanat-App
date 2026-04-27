import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. الإعدادات والنسخة ---
VERSION = "0.4"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="سكنات شكّور Pro", 
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_icon="🏢"
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

# --- 3. تصميم CSS (ثبات كامل وشامل) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="st-"], .main, button, input {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    .student-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }
    /* تحسين شكل التبويبات للموبايل */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6; border-radius: 10px 10px 0 0; padding: 10px 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. تعقب الجهاز (Logs) ---
def log_device():
    if "device_logged" not in st.session_state:
        ua = st_javascript("window.navigator.userAgent")
        if ua and ua != "null":
            device = "Unknown"
            if "iPhone" in str(ua): device = "iPhone 📱"
            elif "Android" in str(ua): device = "Android 📱"
            elif "Windows" in str(ua): device = "Windows PC 💻"
            try:
                supabase.table("login_logs").insert({"device_info": device}).execute()
                st.session_state["device_logged"] = True
            except: pass

# --- 5. شاشة الدخول (نسخة مصلحة تقنياً) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 سكنات شكّــــــــور</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    
    # تم إصلاح السطر هنا (إزالة := واستخدام c2 مباشرة)
    with c2:
        pwd_in = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        btn_login = st.button("دخول للنظام", use_container_width=True)
        
        # يدعم الدخول بالزر أو بالضغط على Enter
        if btn_login or (pwd_in == ADMIN_PWD and pwd_in != ""):
            if pwd_in == ADMIN_PWD:
                st.session_state["logged_in"] = True
                log_device()
                st.rerun()
            elif pwd_in != "": 
                st.error("❌ كلمة المرور خطأ")
    st.stop()
# --- 6. جلب البيانات ---
@st.cache_data(ttl=2)
def load_all_data():
    s_data = supabase.table("sakanat").select("*").order('name').execute()
    t_data = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_data.data, t_data.data

s_list, t_list = load_all_data()

# --- 7. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("⚙️ لوحة الإدارة")
    st.write(f"المطور: **{DEV_NAME}**")
    st.markdown("---")
    search_query = st.text_input("🔍 بحث (اسم / هاتف):")
    
    # إصلاح ركن المطور والـ Logs
    st.markdown("### 🛠️ ركن المطور")
    dev_key = st.text_input("رمز المطور", type="password", key="dev_access")
    
    # هذا الشرط سيجعل اللوجز تظهر فوراً عند كتابة الرمز الصحيح
    if dev_key == DEV_LOG_PWD:
        st.success("تم تأكيد هويتك كـ مطور")
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(7).execute()
            for l in logs.data:
                st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
            if st.button("تحديث السجلات 🔄"): st.rerun()
        except: st.write("لا يوجد سجلات متاحة.")
    
    st.markdown("---")
    if st.button("🚪 تسجيل خروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية (Tabs) ---
tab_list, tab_stats = st.tabs(["👥 إدارة الطالبات", "📊 إحصائيات"])

with tab_list:
    # الفلترة
    s_names = ["الكل"] + [s['name'] for s in s_list]
    s_choice = st.selectbox("📍 تصفية حسب الشقة:", s_names)
    
    filtered = t_list
    if s_choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_choice]
    if search_query:
        filtered = [s for s in filtered if search_query.lower() in s['name'].lower() or search_query in str(s['phone'])]

    for s in filtered:
        sid = str(s['id'])
        # واتساب
        phone = str(s['phone']).replace(' ', '').replace('+', '')
        wa = f"https://wa.me/962{phone[1:]}" if phone.startswith('07') else f"https://wa.me/{phone}"

        # بطاقة الطالبة الفخمة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0;">🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 <b>ملاحظات:</b> {s['notes'] if s['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار والعمليات
        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c1: st.link_button("💬 WhatsApp", wa, use_container_width=True)
        with c2:
            f_cols = st.columns(3)
            files = [("🪪 هوية", 'file_id'), ("📜 عقد", 'file_contract'), ("💵 كمبيالة", 'file_kumbiala')]
            for i, (lab, col) in enumerate(files):
                path = s.get(col)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    f_cols[i].link_button(lab, f"{url}?download=", use_container_width=True)
                else: f_cols[i].button(f"❌ {lab[3:]}", key=f"no_{col}_{sid}", disabled=True, use_container_width=True)
        
        with c3:
            # دمج الميزات (تعديل الاسم، الهاتف، الملاحظات) والحذف
            with st.popover("⚙️ خيارات"):
                st.write("📝 **تعديل البيانات**")
                up_name = st.text_input("الاسم", s['name'], key=f"un_{sid}")
                up_phone = st.text_input("الهاتف", s['phone'], key=f"up_{sid}")
                up_notes = st.text_area("الملاحظات", s['notes'], key=f"um_{sid}")
                if st.button("حفظ التعديلات ✅", key=f"ub_{sid}"):
                    supabase.table("students").update({"name": up_name, "phone": up_phone, "notes": up_notes}).eq("id", sid).execute()
                    st.rerun()
                st.markdown("---")
                st.write("🗑️ **منطقة الحذف**")
                if st.checkbox("تأكيد الحذف النهائي؟", key=f"dc_{sid}"):
                    if st.button("احذف الآن ❌", key=f"db_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab_stats:
    st.subheader("📊 ملخص السكن")
    st.metric("عدد الطالبات الحالي", len(t_list))
    st.metric("عدد الشقق المفعلة", len(s_list))

st.caption(f"Developed by {DEV_NAME} | v{VERSION}")