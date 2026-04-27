import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. الإعدادات الأساسية ---
VERSION = "0.6"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="سكنات شكّور Pro", 
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
    st.error("⚠️ خطأ في الإعدادات السرية (Secrets).")
    st.stop()

# --- 3. تصميم CSS (لضمان جمالية الشاشة ومنع التشوه) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="st-"], .main, button, input {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    .student-card {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-right: 8px solid #2E86C1;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. وظيفة اللوجز (الطريقة السهلة والمضمونة عبر السيرفر) ---
def log_user_device():
    if "device_logged" not in st.session_state:
        try:
            # قراءة نوع الجهاز مباشرة من بيانات الطلب (Headers)
            # هذه الطريقة تعمل 100% على الموبايل والكمبيوتر فوراً
            user_agent = st.context.headers.get("User-Agent", "جهاز مجهول")
            
            device = "جهاز غير معروف"
            if "iPhone" in user_agent: device = "iPhone 📱"
            elif "Android" in user_agent: device = "Android 📱"
            elif "Windows" in user_agent: device = "Windows PC 💻"
            elif "Macintosh" in user_agent: device = "MacBook 💻"

            # تسجيل في سوبابيس
            supabase.table("login_logs").insert({"device_info": device}).execute()
            st.session_state["device_logged"] = True
        except:
            pass

# --- 5. شاشة الدخول ---
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
                log_user_device() # نسجل الجهاز لحظة ضغط الدخول
                st.rerun()
            elif pwd_in != "": 
                st.error("❌ كلمة المرور خطأ")
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
    st.write(f"المطور: **{DEV_NAME}**")
    search_q = st.text_input("🔍 بحث (اسم/هاتف):")
    st.markdown("---")
    
    # ركن المطور (اللوجز المضمونة)
    st.markdown("### 🛠️ ركن المطور")
    dev_key = st.text_input("رمز المطور", type="password")
    if dev_key == DEV_LOG_PWD:
        st.success("أهلاً يا مطور")
        try:
            # زر تحديث يدوي للوجز
            if st.button("تحديث السجلات 🔄"):
                st.rerun()
            
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            if logs.data:
                for l in logs.data:
                    st.caption(f"🕒 {l['login_time'][11:16]} | {l['device_info']}")
            else:
                st.write("لا يوجد سجلات حالياً.")
        except:
            st.error("خطأ في جلب السجلات. تأكد من وجود جدول login_logs")
            
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية (Tabs) ---
tab1, tab2 = st.tabs(["👥 قائمة الطالبات", "📊 ملخص السكن"])

with tab1:
    choice = st.selectbox("📍 تصفية الشقق:", ["الكل"] + [s['name'] for s in s_list])
    
    filtered = t_list
    if choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower() or search_q in str(s['phone'])]

    for s in filtered:
        sid = str(s['id'])
        phone = str(s['phone']).replace(' ', '').replace('+', '')
        wa = f"https://wa.me/962{phone[1:]}" if phone.startswith('07') else f"https://wa.me/{phone}"

        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0;">🏠 {s.get('sakanat', {}).get('name', 'N/A')} | 📞 {s['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 <b>ملاحظات:</b> {s['notes'] if s['notes'] else 'لا يوجد'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c1: st.link_button("💬 WhatsApp", wa, use_container_width=True)
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
                st.write("🛠️ **تعديل البيانات**")
                n_v = st.text_input("تعديل الاسم", s['name'], key=f"n_{sid}")
                p_v = st.text_input("تعديل الهاتف", s['phone'], key=f"p_{sid}")
                m_v = st.text_area("تعديل الملاحظات", s['notes'], key=f"m_{sid}")
                if st.button("حفظ التعديلات ✅", key=f"s_{sid}"):
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