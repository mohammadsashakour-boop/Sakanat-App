import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. إعدادات الهوية والنسخة ---
VERSION = "0.2"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title=f"سكنات شكّور Pro", 
    layout="wide", 
    initial_sidebar_state="collapsed", # الحل لمشكلة الموبايل: القائمة تبدأ مخفية
    page_icon="🏢"
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

# --- 3. تصميم CSS احترافي (مضاد للتشويه على الموبايل) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* توحيد الخط والاتجاه */
    html, body, [class*="st-"], .main, button, input {{
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }}

    /* تصميم بطاقة الطالبة للموبايل والكمبيوتر */
    .student-card {{
        background: white; 
        padding: 20px; 
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); 
        border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }}

    /* إخفاء القائمة الجانبية المزعجة في الموبايل بلمسة جمالية */
    [data-testid="stSidebar"] {{
        min-width: 280px !important;
        background-color: #f8f9fa;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. تسجيل اللوجز (تعقب الجهاز) ---
def log_device():
    if "logged_this_session" not in st.session_state:
        ua = st_javascript("window.navigator.userAgent")
        if ua and ua != "null":
            device = "Unknown"
            if "iPhone" in str(ua): device = "iPhone 📱"
            elif "Android" in str(ua): device = "Android 📱"
            elif "Windows" in str(ua): device = "Windows PC 💻"
            try:
                supabase.table("login_logs").insert({"device_info": device}).execute()
                st.session_state["logged_this_session"] = True
            except: pass

# --- 5. شاشة الدخول (تعمل بالـ Enter) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🏢 نظام سكنات شكّور</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                log_device()
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 6. جلب البيانات من السحابة ---
@st.cache_data(ttl=5)
def load_data():
    s_res = supabase.table("sakanat").select("*").order('name').execute()
    t_res = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_res.data, t_res.data

s_list, t_list = load_data()

# --- 7. القائمة الجانبية (مبسطة جداً للموبايل) ---
with st.sidebar:
    st.title("⚙️ الإدارة")
    st.write(f"المطور: **{DEV_NAME}**")
    st.markdown("---")
    
    # إصلاح كبسة المطور (Logs)
    with st.expander("🛠️ سجلات المطور"):
        dev_pwd = st.text_input("رمز المطور", type="password")
        if st.button("عرض السجلات 📜"): # أضفنا زر للتأكد من التحديث
            if dev_pwd == DEV_LOG_PWD:
                try:
                    l_data = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
                    for l in l_data.data:
                        st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
                except: st.write("لا يوجد بيانات")
            else: st.error("رمز خاطئ")
            
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية (Tabs) ---
tab_students, tab_stats = st.tabs(["👥 قائمة الطالبات", "📊 إحصائيات السكن"])

with tab_students:
    # فلترة وبحث
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        s_choice = st.selectbox("📍 اختر الشقة:", ["الكل"] + [s['name'] for s in s_list])
    with col_f2:
        search_q = st.text_input("🔍 ابحث (اسم/هاتف):")

    filtered = t_list
    if s_choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower() or search_q in str(s['phone'])]

    for s in filtered:
        sid = str(s['id'])
        # معالجة الواتساب
        phone = str(s['phone']).replace(' ', '').replace('+', '')
        wa_url = f"https://wa.me/962{phone[1:]}" if phone.startswith('07') else f"https://wa.me/{phone}"

        # بطاقة الطالبة (تنسيق فخم)
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0; font-size:15px;">🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:#7f8c8d; font-size:13px;">📝 {s['notes'] if s['notes'] else 'لا يوجد ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # أزرار الإجراءات
        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c1: st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
        with c2:
            f_cols = st.columns(3)
            files = [("الهوية", 'file_id'), ("العقد", 'file_contract'), ("الكمبيالة", 'file_kumbiala')]
            for i, (lab, col) in enumerate(files):
                path = s.get(col)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    f_cols[i].link_button(f"👁️ {lab}", f"{url}?download=", use_container_width=True)
                else: f_cols[i].button(f"❌ {lab}", key=f"x_{col}_{sid}", disabled=True, use_container_width=True)
        with c3:
            # Popover للتعديل والحذف
            edit_col, del_col = st.columns(2)
            with edit_col.popover("✏️"):
                n_val = st.text_input("الاسم", s['name'], key=f"en_{sid}")
                m_val = st.text_area("ملاحظات", s['notes'], key=f"em_{sid}")
                if st.button("حفظ", key=f"es_{sid}"):
                    supabase.table("students").update({"name": n_val, "notes": m_val}).eq("id", sid).execute()
                    st.rerun()
            with del_col.popover("🗑️"):
                st.warning("حذف؟")
                if st.checkbox("تأكيد الحذف", key=f"dc_{sid}"):
                    if st.button("نعم، احذف", key=f"db_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab_stats:
    st.subheader("📊 ملخص البيانات")
    st.metric("إجمالي الطالبات", len(t_list))
    st.metric("عدد الشقق", len(s_list))

# --- 9. التوقيع ---
st.markdown(f"<div class='dev-footer'>Designed by {DEV_NAME} | v{VERSION}</div>", unsafe_allow_html=True)