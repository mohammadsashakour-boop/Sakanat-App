import streamlit as st
from supabase import create_client, Client

# --- 1. إعدادات النظام ---
VERSION = "1.0"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(page_title="سكنات شكّور", layout="wide")

# --- 2. الاتصال بـ Supabase ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ خطأ: تأكد من إعدادات Secrets.")
    st.stop()

# --- 3. تصميم نظيف جداً (RTL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .student-card {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-right: 8px solid #2E86C1;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. تسجيل الدخول واللوجز ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🏢 نظام سكنات شكّور</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                # تسجيل الجهاز فوراً
                try:
                    # قراءة بصمة الجهاز
                    ua = st.context.headers.get("User-Agent", "جهاز غير معروف")
                    device = "iPhone 📱" if "iPhone" in ua else "Android 📱" if "Android" in ua else "PC 💻"
                    supabase.table("login_logs").insert({"device_info": device}).execute()
                except: pass
                
                st.session_state["logged_in"] = True
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=2)
def get_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

s_list, t_list = get_data()

# --- 6. الواجهة الرئيسية (Tabs) ---
st.title("🏢 لوحة إدارة السكن")

tab1, tab2, tab3 = st.tabs(["👥 قائمة الطالبات", "📊 إحصائيات", "🔐 سجلات الدخول"])

with tab1:
    # فلترة وبحث
    f1, f2 = st.columns(2)
    with f1: s_search = st.text_input("🔍 بحث عن اسم:")
    with f2: s_filter = st.selectbox("📍 تصفية الشقة:", ["الكل"] + [s['name'] for s in s_list])

    data = t_list
    if s_filter != "الكل":
        data = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_filter]
    if s_search:
        data = [s for s in data if s_search.lower() in s['name'].lower()]

    for student in data:
        sid = str(student['id'])
        # رابط واتساب
        p = str(student['phone']).replace(' ', '').replace('+', '')
        wa = f"https://wa.me/962{p[1:]}" if p.startswith('07') else "#"

        # البطاقة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {student['name']}</h3>
                <p>🏠 {student.get('sakanat', {}).get('name', 'N/A')} | 📞 {student['phone']}</p>
                <p style="color:gray; font-size:14px;">📝 {student['notes'] if student['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار (مرتبة جداً للموبايل)
        col_wa, col_files, col_edit = st.columns([1, 2, 1.5])
        with col_wa:
            st.link_button("💬 واتساب", wa, use_container_width=True)
        with col_files:
            f_cols = st.columns(3)
            # زر الهوية
            if student.get('file_id'):
                u = supabase.storage.from_("student_files").get_public_url(student['file_id'])
                f_cols[0].link_button("🪪 هوية", f"{u}?download=", use_container_width=True)
            else: f_cols[0].button("❌ ه", key=f"no_id_{sid}", disabled=True)
            
            # زر العقد
            if student.get('file_contract'):
                u = supabase.storage.from_("student_files").get_public_url(student['file_contract'])
                f_cols[1].link_button("📜 عقد", f"{u}?download=", use_container_width=True)
            else: f_cols[1].button("❌ ع", key=f"no_co_{sid}", disabled=True)

            # زر الكمبيالة
            if student.get('file_kumbiala'):
                u = supabase.storage.from_("student_files").get_public_url(student['file_kumbiala'])
                f_cols[2].link_button("💵 كمب", f"{u}?download=", use_container_width=True)
            else: f_cols[2].button("❌ ك", key=f"no_ku_{sid}", disabled=True)

        with col_edit:
            # زر تعديل (يفتح فورم تحت الكرت)
            if st.button("✏️ تعديل / حذف", key=f"edit_btn_{sid}", use_container_width=True):
                st.session_state[f"show_edit_{sid}"] = not st.session_state.get(f"show_edit_{sid}", False)
            
            if st.session_state.get(f"show_edit_{sid}", False):
                with st.container():
                    st.info("تعديل البيانات:")
                    new_n = st.text_input("الاسم", student['name'], key=f"un_{sid}")
                    new_m = st.text_area("الملاحظات", student['notes'], key=f"um_{sid}")
                    if st.button("حفظ التعديل ✅", key=f"us_{sid}"):
                        supabase.table("students").update({"name": new_n, "notes": new_m}).eq("id", sid).execute()
                        st.rerun()
                    st.markdown("---")
                    if st.button("🗑️ حذف الطالبة نهائياً", key=f"del_{sid}", type="primary"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab2:
    st.metric("إجمالي الطالبات", len(t_list))
    st.metric("عدد الشقق", len(s_list))

with tab3:
    st.subheader("🔐 سجلات دخول الأجهزة")
    dev_key = st.text_input("أدخل رمز المطور:", type="password")
    if dev_key == DEV_LOG_PWD:
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            if logs.data:
                for l in logs.data:
                    st.write(f"🕒 {l['login_time'][11:16]} | الجهاز: **{l['device_info']}**")
            else: st.info("لا يوجد سجلات حالياً.")
        except: st.error("تأكد من وجود جدول login_logs في Supabase.")

if st.button("🚪 تسجيل الخروج"):
    st.session_state["logged_in"] = False
    st.rerun()