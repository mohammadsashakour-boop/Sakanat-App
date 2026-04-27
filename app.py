import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. إعدادات الهوية ---
VERSION = "0.1"
DEV_NAME = "Mohammad-Sofian"

st.set_page_config(page_title=f"سكنات شكّور v{VERSION}", layout="wide", page_icon="🏢")

# --- 2. جلب الإعدادات السرية ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("⚠️ يرجى ضبط الإعدادات السرية (Secrets) في Streamlit Cloud.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 3. لمسات CSS الجمالية ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .main {{ background-color: #f4f7f9; }}
    .student-card {{
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-right: 8px solid #2E86C1;
        margin-bottom: 20px; transition: 0.3s;
    }}
    .student-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
    .dev-footer {{ text-align: center; color: #7f8c8d; padding: 20px; font-size: 14px; border-top: 1px solid #ddd; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. نظام الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🏢 نظام سكنات شكّـــــــــــــــور</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        if st.button("دخول للنظام", use_container_width=True):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
    st.markdown(f"<p style='text-align: center; color: gray;'>Version {VERSION} | Developed by {DEV_NAME}</p>", unsafe_allow_html=True)
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=5)
def load_data():
    s_res = supabase.table("sakanat").select("*").order('name').execute()
    t_res = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_res.data, t_res.data

s_list, t_list = load_data()
s_names = [s['name'] for s in s_list]

# --- 6. القائمة الجانبية ---
with st.sidebar:
    st.title("🏢 سكنات شكّور")
    st.write(f"المطور: **{DEV_NAME}**")
    st.info(f"الإصدار الحالي: {VERSION}")
    st.markdown("---")
    search_q = st.text_input("🔍 بحث (اسم، هاتف، ملاحظة):")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 7. الإحصائيات العلوية ---
st.title("📋 لوحة إدارة السكن")
c1, c2, c3 = st.columns(3)
c1.metric("إجمالي الطالبات", len(t_list))
c2.metric("عدد الشقق", len(s_list))
c3.metric("حالة النظام", "متصل ✅")
st.markdown("---")

# التصفية
s_choice = st.selectbox("📍 تصفية حسب الشقة:", ["الكل"] + s_names)
filtered = t_list
if s_choice != "الكل":
    filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_choice]
if search_q:
    filtered = [s for s in filtered if search_q.lower() in str(s).lower()]

# --- 8. عرض البطاقات ---
for student in filtered:
    sid = str(student['id'])
    
    # تنسيق رقم الواتساب
    raw_p = str(student['phone']).replace(' ', '').replace('+', '')
    wa_phone = "962" + raw_p[1:] if raw_p.startswith('07') else raw_p

    with st.container():
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color: #2E86C1; margin-bottom: 5px;">👤 {student['name']}</h3>
                <p>🏠 <b>الشقة:</b> {student.get('sakanat', {}).get('name', 'N/A')} | 📞 <b>الهاتف:</b> {student['phone']}</p>
                <p style="color: #5D6D7E;">📝 <b>ملاحظات:</b> {student['notes'] if student['notes'] else 'لا يوجد ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_files, col_manage = st.columns([2.5, 1.5])
        
        with col_files:
            f_cols = st.columns(4)
            # زر واتساب
            f_cols[0].link_button("💬 WhatsApp", f"https://wa.me/{wa_phone}", use_container_width=True)
            # الملفات
            labels = [("الهوية", 'file_id'), ("العقد", 'file_contract'), ("الكمبيالة", 'file_kumbiala')]
            for i, (lab, col) in enumerate(labels):
                path = student.get(col)
                if path:
                    url = supabase.storage.from_("student_files").get_public_url(path)
                    f_cols[i+1].link_button(f"👁️ {lab}", f"{url}?download=", use_container_width=True)
                else:
                    f_cols[i+1].button(f"❌ {lab}", key=f"m_{col}_{sid}", disabled=True, use_container_width=True)

        with col_manage:
            m_cols = st.columns(2)
            # التعديل
            with m_cols[0].popover("✏️ تعديل البيانات"):
                new_n = st.text_input("الاسم", value=student['name'], key=f"n_{sid}")
                new_p = st.text_input("الهاتف", value=student['phone'], key=f"p_{sid}")
                new_m = st.text_area("الملاحظات", value=student['notes'], key=f"m_{sid}")
                if st.button("حفظ ✅", key=f"sv_{sid}"):
                    supabase.table("students").update({"name": new_n, "phone": new_p, "notes": new_m}).eq("id", sid).execute()
                    st.success("تم التحديث")
                    st.rerun()
            
            # الحذف مع التأكيد (طلبك الجديد)
            with m_cols[1].popover("🗑️ حذف"):
                st.warning("هل أنت متأكد من حذف الطالبة؟")
                confirm = st.checkbox("نعم، متأكد من الحذف النهائي", key=f"conf_{sid}")
                if confirm:
                    if st.button("تأكيد الحذف ❌", key=f"del_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# --- 9. Footer ---
st.markdown(f"""
    <div class="dev-footer">
        نظام إدارة سكنات شكّور - جميع الحقوق محفوظة لعام 2026<br>
        <b>Designed & Developed by {DEV_NAME} | Version {VERSION}</b>
    </div>
""", unsafe_allow_html=True)