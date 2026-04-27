import streamlit as st
from supabase import create_client, Client

# --- 1. هوية التطبيق (الإصدار 0.2 - النسخة النهائية) ---
VERSION = "0.2"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="نظام سكنات شكّور", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# --- 2. الربط بـ Supabase ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ يرجى ضبط Secrets في Streamlit Cloud.")
    st.stop()

# --- 3. تصميم الـ UI الفخم (لمسات المهندس محمد) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    * {{ 
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }}
    
    .main {{ background-color: #f4f7f6; }}
    
    /* تصميم بطاقة الطالبة */
    .student-card {{
        background: white; 
        padding: 20px; 
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        border-right: 10px solid #2E86C1;
        margin-bottom: 20px;
    }}
    
    /* تنبيه النواقص */
    .missing-badge {{
        background-color: #FDEDEC;
        color: #C0392B;
        padding: 2px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }}
    
    .footer {{
        text-align: center; 
        padding: 30px; 
        color: #95a5a6; 
        font-size: 13px;
        border-top: 1px solid #eee;
        margin-top: 50px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. نظام الدخول الصامت (بدون ذكر كلمة سجلات) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1; margin-top: 60px;'>🏢 نظام إدارة السكن</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("دخول للنظام", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                try:
                    # تسجيل بصمة الجهاز بصمت
                    ua = st.context.headers.get("User-Agent", "")
                    device = "iPhone" if "iPhone" in ua else "Android" if "Android" in ua else "PC"
                    supabase.table("login_logs").insert({"device_info": device}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 5. جلب البيانات ---
@st.cache_data(ttl=2)
def fetch_data():
    s_res = supabase.table("sakanat").select("*").order('name').execute()
    t_res = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_res.data, t_res.data

sakanat_list, student_list = fetch_data()

# --- 6. الواجهة الرئيسية ---
st.title("📋 لوحة التحكم")

# التبويبات الثلاثة
tab_main, tab_analytics, tab_dev = st.tabs(["👥 إدارة الطالبات", "📊 نظرة عامة", "🛠️ ركن المطور"])

with tab_main:
    # --- الميزة الـ Critical: رادار النواقص والبحث ---
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        search_q = st.text_input("🔍 بحث بالاسم:")
    with col_b:
        apt_filter = st.selectbox("🏠 الشقة:", ["الكل"] + [s['name'] for s in sakanat_list])
    with col_c:
        # ميزة الفلترة حسب النواقص
        filter_missing = st.toggle("⚠️ عرض النواقص فقط")

    # تطبيق الفلترة
    data = student_list
    if apt_filter != "الكل":
        data = [s for s in data if s.get('sakanat') and s['sakanat']['name'] == apt_filter]
    if search_q:
        data = [s for s in data if search_q.lower() in s['name'].lower()]
    
    # منطق رادار النواقص
    if filter_missing:
        data = [s for s in data if not (s.get('file_id') and s.get('file_contract') and s.get('file_kumbiala'))]

    if not data:
        st.info("لا توجد بيانات مطابقة لهذه المعايير.")

    for student in data:
        sid = str(student['id'])
        
        # فحص اكتمال الأوراق
        missing = []
        if not student.get('file_id'): missing.append("هوية")
        if not student.get('file_contract'): missing.append("عقد")
        if not student.get('file_kumbiala'): missing.append("كمبيالة")
        
        missing_text = f"<span class='missing-badge'>⚠️ نقص: {', '.join(missing)}</span>" if missing else "✅ مكتمل"

        st.markdown(f"""
            <div class="student-card">
                <div style="display: flex; justify-content: space-between;">
                    <h3 style="color:#2E86C1; margin:0;">👤 {student['name']}</h3>
                    <div>{missing_text}</div>
                </div>
                <p style="margin:8px 0; font-size:15px;">🏠 {student.get('sakanat', {}).get('name', 'N/A')} | 📞 {student['phone']}</p>
                <p style="color:#7f8c8d; font-size:14px;">📝 {student['notes'] if student['notes'] else 'لا ملاحظات'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c_wa, c_files, c_tools = st.columns([1, 2.5, 1])
        with c_wa:
            raw_p = str(student['phone']).replace(' ', '').replace('+', '')
            st.link_button("💬 WhatsApp", f"https://wa.me/962{raw_p[1:]}" if raw_p.startswith('07') else "#", use_container_width=True)
        
        with c_files:
            f_cols = st.columns(3)
            files_map = [("الهوية", "file_id"), ("العقد", "file_contract"), ("الكمبيالة", "file_kumbiala")]
            for i, (label, col_name) in enumerate(files_map):
                if student.get(col_name):
                    url = supabase.storage.from_("student_files").get_public_url(student[col_name])
                    f_cols[i].link_button(label, f"{url}?download=", key=f"f_{col_name}_{sid}", use_container_width=True)
                else:
                    f_cols[i].button(f"❌ {label}", disabled=True, key=f"n_{col_name}_{sid}", use_container_width=True)

        with c_tools:
            if st.button("⚙️ خيارات", key=f"btn_{sid}", use_container_width=True):
                st.session_state[f"show_{sid}"] = not st.session_state.get(f"show_{sid}", False)
            
            if st.session_state.get(f"show_{sid}", False):
                st.markdown("---")
                e_name = st.text_input("الاسم", student['name'], key=f"name_{sid}")
                e_phone = st.text_input("الهاتف", student['phone'], key=f"phone_{sid}")
                e_notes = st.text_area("الملاحظات", student['notes'], key=f"note_{sid}")
                
                c_sv, c_dl = st.columns(2)
                if c_sv.button("حفظ", key=f"sv_{sid}", use_container_width=True):
                    supabase.table("students").update({"name": e_name, "phone": e_phone, "notes": e_notes}).eq("id", sid).execute()
                    st.rerun()
                if c_dl.button("حذف", key=f"dl_{sid}", type="primary", use_container_width=True):
                    if st.checkbox("تأكيد الحذف؟", key=f"conf_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()

with tab_analytics:
    st.subheader("📊 ملخص السكن")
    s1, s2 = st.columns(2)
    s1.metric("إجمالي الطالبات", len(student_list))
    s2.metric("عدد الشقق", len(sakanat_list))
    
    # إحصائية الملفات الناقصة
    missing_any = [s for s in student_list if not (s.get('file_id') and s.get('file_contract') and s.get('file_kumbiala'))]
    st.error(f"⚠️ يوجد {len(missing_any)} طالبة لديهن نواقص في الأوراق الرسمية.")

with tab_dev:
    st.subheader("🛠️ ركن المطور")
    dev_key = st.text_input("أدخل رمز المطور للمتابعة:", type="password")
    if dev_key == DEV_LOG_PWD:
        st.success(f"مرحباً بك يا مهندس {DEV_NAME.split('-')[0]}.")
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            if logs.data:
                for l in logs.data:
                    st.write(f"🕒 `{l['login_time'][11:16]}` | الجهاز: **{l['device_info']}**")
        except: st.write("لا يوجد بيانات لعرضها.")

# --- 7. التذييل (Footer) ---
st.markdown(f"""
    <div class="footer">
        تم التطوير بواسطة <b>{DEV_NAME}</b> | © 2026<br>
        الإصدار المعتمد {VERSION}
    </div>
""", unsafe_allow_html=True)

if st.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()