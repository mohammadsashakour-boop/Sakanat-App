import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript
import pandas as pd

# --- 1. الإعدادات والتعريفات ---
VERSION = "0.1"
DEV_NAME = "Mohammad-Sofian"

st.set_page_config(
    page_title=f"سكنات شكّور v{VERSION}", 
    layout="wide", 
    page_icon="🏢"
)

# --- 2. جلب المفاتيح من الإعدادات السرية (Secrets) ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("⚠️ خطأ: تأكد من ضبط Secrets (URL, KEY, ADMIN_PASSWORD) في Streamlit Cloud.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 3. تصميم الواجهة وجماليات CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .main {{ background-color: #f4f7f9; }}
    
    /* تصميم بطاقة الطالبة */
    .student-card {{
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-right: 10px solid #2E86C1;
        margin-bottom: 20px; transition: 0.3s;
    }}
    .student-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
    
    /* تذييل الصفحة */
    .dev-footer {{ text-align: center; color: #7f8c8d; padding: 20px; font-size: 14px; border-top: 1px solid #ddd; margin-top: 50px; }}
    
    /* تحسين القائمة الجانبية للموبايل */
    [data-testid="stSidebar"] {{ background-color: #ffffff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. وظيفة تسجيل الدخول وتعقب الأجهزة (إصلاح اللوجز) ---
def log_device_info():
    # سحب معلومات الجهاز عبر JavaScript
    ua = st_javascript("window.navigator.userAgent")
    
    # التأكد من وصول المعلومة وتسجيلها مرة واحدة فقط في الجلسة
    if ua and ua != "null" and "logged_this_session" not in st.session_state:
        device = "جهاز غير معروف"
        if "iPhone" in str(ua): device = "iPhone 📱"
        elif "Android" in str(ua): device = "Android 📱"
        elif "Windows" in str(ua): device = "Windows PC 💻"
        elif "Macintosh" in str(ua): device = "MacBook 💻"

        try:
            supabase.table("login_logs").insert({"device_info": device}).execute()
            st.session_state["logged_this_session"] = True
        except:
            pass

# --- 5. نظام الدخول والحماية ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1; margin-top: 50px;'>🏢 سكنات شكّـــــــــــــــور</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
            if st.form_submit_button("دخول للنظام", use_container_width=True):
                if pwd == ADMIN_PWD:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة")
    st.markdown(f"<p style='text-align: center; color: gray;'>Version {VERSION} | Developed by {DEV_NAME}</p>", unsafe_allow_html=True)
    st.stop()

# تنفيذ تسجيل الجهاز بعد الدخول الناجح مباشرة
log_device_info()

# --- 6. جلب البيانات من السحابة ---
@st.cache_data(ttl=5)
def load_data():
    sakanat = supabase.table("sakanat").select("*").order('name').execute()
    students = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return sakanat.data, students.data

s_list, t_list = load_data()
s_names = [s['name'] for s in s_list]

# --- 7. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.title("🏢 سكنات شكّور")
    st.write(f"المطور: **{DEV_NAME}**")
    st.info(f"إصدار النظام: {VERSION}")
    st.markdown("---")
    search_q = st.text_input("🔍 بحث عن طالبة (اسم/هاتف/ملاحظة):")
    
    # عرض السجلات للمطور (اللوجز المصلحة)
    with st.expander("🛠️ سجلات الدخول (Logs)"):
        dev_key = st.text_input("رمز المطور", type="password")
        if dev_key == "Sofian2026":
            try:
                logs_data = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
                for log in logs_data.data:
                    st.caption(f"🕒 {log['login_time'][:16]} | {log['device_info']}")
            except:
                st.write("لا يوجد سجلات حالياً.")
                
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية والعرض ---
st.title("📋 إدارة بيانات الطالبات")

# تبويبات لتنظيم الشاشة على الموبايل
tab_list, tab_stats = st.tabs(["👥 قائمة الطالبات", "📊 إحصائيات السكن"])

with tab_list:
    # فلترة حسب الشقة
    s_choice = st.selectbox("📍 تصفية حسب الشقة:", ["الكل"] + s_names)
    
    filtered = t_list
    if s_choice != "الكل":
        filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in str(s).lower()]

    if not filtered:
        st.warning("لا توجد بيانات تطابق البحث.")
    
    for s in filtered:
        sid = str(s['id'])
        
        # تحضير رابط الواتساب
        raw_phone = str(s['phone']).replace(' ', '').replace('+', '')
        wa_link = f"https://wa.me/962{raw_phone[1:]}" if raw_phone.startswith('07') else f"https://wa.me/{raw_phone}"

        # بطاقة الطالبة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color: #2E86C1; margin:0;">👤 {s['name']}</h3>
                <p style="margin:5px 0;">🏠 <b>الشقة:</b> {s.get('sakanat', {}).get('name', 'N/A')} | 📞 <b>الهاتف:</b> {s['phone']}</p>
                <p style="color: #5D6D7E; font-size:14px;">📝 <b>ملاحظات:</b> {s['notes'] if s['notes'] else 'لا يوجد ملاحظات مسجلة'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # أزرار الإجراءات
        col_wa, col_files, col_actions = st.columns([1, 2.5, 1.5])
        
        with col_wa:
            st.link_button("💬 WhatsApp", wa_link, use_container_width=True)
            
        with col_files:
            f_cols = st.columns(3)
            file_labels = [("🪪 الهوية", 'file_id'), ("📜 العقد", 'file_contract'), ("💵 الكمبيالة", 'file_kumbiala')]
            for i, (label, col_name) in enumerate(file_labels):
                path = s.get(col_name)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    # ميزة ?download= لفتح الملفات بنجاح
                    f_cols[i].link_button(label, f"{url}?download=", use_container_width=True)
                else:
                    f_cols[i].button(f"❌ {label[2:]}", key=f"none_{col_name}_{sid}", disabled=True, use_container_width=True)

        with col_actions:
            m_cols = st.columns(2)
            # زر التعديل
            with m_cols[0].popover("✏️ تعديل"):
                new_n = st.text_input("الاسم", value=s['name'], key=f"edit_n_{sid}")
                new_p = st.text_input("الهاتف", value=s['phone'], key=f"edit_p_{sid}")
                new_m = st.text_area("الملاحظات", value=s['notes'], key=f"edit_m_{sid}")
                if st.button("حفظ ✅", key=f"save_{sid}"):
                    supabase.table("students").update({"name": new_n, "phone": new_p, "notes": new_m}).eq("id", sid).execute()
                    st.success("تم التحديث!")
                    st.rerun()
            
            # زر الحذف مع التأكيد (طلبك الخاص)
            with m_cols[1].popover("🗑️ حذف"):
                st.error("هل أنت متأكد من الحذف؟")
                confirm = st.checkbox("نعم، احذف الطالبة نهائياً", key=f"confirm_{sid}")
                if confirm:
                    if st.button("حذف الآن ❌", key=f"delete_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

with tab_stats:
    st.subheader("📊 ملخص السكن")
    st.metric("إجمالي عدد الطالبات", len(t_list))
    st.metric("عدد الشقق المفعلة", len(s_list))

# --- 9. تذييل الصفحة (Footer) ---
st.markdown(f"""
    <div class="dev-footer">
        نظام سكنات شكّور - جميع الحقوق محفوظة لعام 2026<br>
        <b>Designed & Developed by {DEV_NAME} | Version {VERSION}</b>
    </div>
""", unsafe_allow_html=True)