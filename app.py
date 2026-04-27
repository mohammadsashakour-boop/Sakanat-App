import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. الإعدادات والتعريفات ---
VERSION = "0.1"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335" # كلمة السر الجديدة للمطور

st.set_page_config(
    page_title=f"سكنات شكّور v{VERSION}", 
    layout="wide", 
    initial_sidebar_state="collapsed", # تبدأ القائمة الجانبية مخفية لتجنب الإزعاج
    page_icon="🏢"
)

# --- 2. جلب المفاتيح من السيرفر ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("⚠️ يرجى ضبط Secrets (URL, KEY, ADMIN_PASSWORD) في Streamlit Cloud.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 3. تصميم الواجهة (CSS المطور للموبايل) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* توحيد الخط في كل الموقع */
    html, body, [class*="st-"], .main, button, input {{
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }}

    /* تحسين الشاشة الجانبية ومنع التشوه */
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-left: 1px solid #e0e0e0;
        min-width: 250px !important;
    }}
    
    /* منع تداخل الخطوط في الموبايل */
    .stMarkdown, .stText {{
        line-height: 1.6 !important;
    }}

    /* تصميم بطاقة الطالبة الأنيق */
    .student-card {{
        background: white; 
        padding: 18px; 
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
        border-right: 6px solid #2E86C1;
        margin-bottom: 15px;
    }}

    /* تحسين شكل الأزرار */
    .stButton>button {{
        border-radius: 8px !important;
        font-weight: bold !important;
    }}

    /* تذييل الصفحة */
    .dev-footer {{ 
        text-align: center; 
        color: #95a5a6; 
        padding: 20px; 
        font-size: 13px; 
        border-top: 1px solid #eee;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. تسجيل الجهاز (اللوجز) ---
def log_device():
    ua = st_javascript("window.navigator.userAgent")
    if ua and ua != "null" and "logged_this_session" not in st.session_state:
        device = "جهاز غير معروف"
        if "iPhone" in str(ua): device = "iPhone 📱"
        elif "Android" in str(ua): device = "Android 📱"
        elif "Windows" in str(ua): device = "Windows PC 💻"
        
        try:
            supabase.table("login_logs").insert({"device_info": device}).execute()
            st.session_state["logged_this_session"] = True
        except: pass

# --- 5. شاشة الدخول (صديقة للـ Enter) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; color: #2E86C1; margin-top: 50px;'>🏢 سكنات شكّــــــــــــور</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd_input = st.text_input("🔑 كلمة المرور", type="password")
        login_btn = st.button("دخول", use_container_width=True)
        
        # يدعم الضغط على الزر أو Enter
        if login_btn or (pwd_input == ADMIN_PWD and pwd_input != ""):
            if pwd_input == ADMIN_PWD:
                st.session_state["logged_in"] = True
                log_device()
                st.rerun()
            elif pwd_input != "":
                st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 6. جلب البيانات ---
@st.cache_data(ttl=5)
def load_data():
    s_data = supabase.table("sakanat").select("*").order('name').execute()
    t_data = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_data.data, t_data.data

sakanat_list, student_list = load_data()

# --- 7. القائمة الجانبية (Fixed Sidebar) ---
with st.sidebar:
    st.title("⚙️ الإدارة")
    st.write(f"المطور: **{DEV_NAME}**")
    st.markdown("---")
    search_q = st.text_input("🔍 بحث سريع:")
    
    # قسم اللوجز المطور (بكلمة السر الجديدة)
    with st.expander("🛠️ سجلات المطور"):
        dev_key = st.text_input("رمز المطور", type="password", key="dev_key_input")
        if dev_key == DEV_LOG_PWD:
            try:
                logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
                for l in logs.data:
                    st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
            except: st.write("لا يوجد سجلات")
    
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. العرض الرئيسي (Tabs) ---
tab_main, tab_info = st.tabs(["👥 الطالبات", "📊 إحصائيات"])

with tab_main:
    # فلترة
    s_names = ["الكل"] + [s['name'] for s in sakanat_list]
    choice = st.selectbox("📍 تصفية حسب الشقة:", s_names)
    
    filtered = student_list
    if choice != "الكل":
        filtered = [s for s in student_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in str(s).lower()]

    for s in filtered:
        sid = str(s['id'])
        # معالجة رابط واتساب
        p = str(s['phone']).replace(' ', '').replace('+', '')
        wa_url = f"https://wa.me/962{p[1:]}" if p.startswith('07') else f"https://wa.me/{p}"

        # كرت الطالبة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0; font-size:15px;">🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:#7f8c8d; font-size:13px;">📝 {s['notes'] if s['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار (مرتبة للموبايل)
        c1, c2, c3 = st.columns([1.2, 2.5, 1.2])
        with c1: st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
        with c2:
            sub_cols = st.columns(3)
            files = [("🪪", 'file_id'), ("📜", 'file_contract'), ("💵", 'file_kumbiala')]
            for i, (label, col_name) in enumerate(files):
                path = s.get(col_name)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    sub_cols[i].link_button(label, f"{url}?download=", use_container_width=True)
                else: sub_cols[i].button(f"❌", key=f"n_{col_name}_{sid}", disabled=True, use_container_width=True)
        with c3:
            with st.popover("🗑️", use_container_width=True):
                if st.checkbox("تأكيد الحذف؟", key=f"conf_{sid}"):
                    if st.button("حذف نهائي", key=f"del_{sid}", type="primary"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab_info:
    st.metric("إجمالي الطالبات", len(student_list))
    st.metric("عدد الشقق", len(sakanat_list))

# --- 9. التوقيع ---
st.markdown(f"<div class='dev-footer'>Designed by {DEV_NAME} | v{VERSION}</div>", unsafe_allow_html=True)