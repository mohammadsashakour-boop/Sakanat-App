import streamlit as st
from supabase import create_client, Client

# --- 1. هوية التطبيق (الإصدار 0.2) ---
VERSION = "0.2"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(
    page_title="نظام سكنات شكّور v0.2", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="🏢"
)

# --- 2. الربط بالسيرفر (Supabase) ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ يرجى ضبط الإعدادات السرية (Secrets) في Streamlit Cloud.")
    st.stop()

# --- 3. اللمسات الشخصية (تصميم CSS احترافي) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* توحيد الخط والاتجاه */
    * {{ 
        font-family: 'Cairo', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }}
    
    .main {{ background-color: #f0f2f6; }}
    
    /* تصميم بطاقة الطالبة "البريميوم" */
    .student-card {{
        background: white; 
        padding: 22px; 
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        border-right: 10px solid #2E86C1;
        margin-bottom: 20px;
        transition: 0.3s;
    }}
    .student-card:hover {{
        transform: scale(1.01);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }}
    
    /* تنسيق التبويبات */
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #ffffff; 
        border-radius: 10px 10px 0 0; 
        padding: 12px 30px;
        font-weight: bold;
        color: #2E86C1;
    }}
    
    /* تذييل الصفحة */
    .footer {{
        text-align: center; 
        padding: 20px; 
        color: #7f8c8d; 
        font-size: 14px;
        border-top: 1px solid #ddd;
        margin-top: 50px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. نظام الدخول وتسجيل الجهاز ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1; margin-top: 50px;'>🏢 نظام سكنات شكّــــــــور</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        if st.button("دخول للنظام", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                # تسجيل الجهاز (لوجز السيرفر)
                try:
                    ua = st.context.headers.get("User-Agent", "جهاز مجهول")
                    device = "iPhone 📱" if "iPhone" in ua else "Android 📱" if "Android" in ua else "PC 💻"
                    supabase.table("login_logs").insert({"device_info": device}).execute()
                except: pass
                st.rerun()
            elif pwd != "": st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 5. وظيفة جلب البيانات ---
@st.cache_data(ttl=2)
def load_app_data():
    sakanat = supabase.table("sakanat").select("*").order('name').execute()
    students = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return sakanat.data, students.data

s_data, t_data = load_app_data()

# --- 6. الواجهة الرئيسية ---
st.markdown(f"<p style='text-align: left; color: gray;'>v{VERSION} | المتصل الآن: المسؤول</p>", unsafe_allow_html=True)
st.title("📋 لوحة التحكم والإدارة")

# التبويبات الثلاثة (بناءً على طلبك)
tab_list, tab_stats, tab_dev = st.tabs(["👥 إدارة الطالبات", "📊 إحصائيات السكن", "🛠️ ركن المطور"])

with tab_list:
    # أدوات البحث والفلترة
    c_search, c_filter = st.columns([2, 1])
    with c_search:
        search_q = st.text_input("🔍 ابحث عن اسم الطالبة:")
    with c_filter:
        apt_choice = st.selectbox("📍 اختر الشقة:", ["الكل"] + [s['name'] for s in s_data])

    # منطق التصفية
    filtered = t_data
    if apt_choice != "الكل":
        filtered = [s for s in t_data if s.get('sakanat') and s['sakanat']['name'] == apt_choice]
    if search_q:
        filtered = [s for s in filtered if search_q.lower() in s['name'].lower()]

    if not filtered:
        st.info("لا توجد بيانات مطابقة للبحث حالياً.")

    for student in filtered:
        sid = str(student['id'])
        # معالجة رقم الواتساب
        raw_p = str(student['phone']).replace(' ', '').replace('+', '')
        wa_url = f"https://wa.me/962{raw_p[1:]}" if raw_p.startswith('07') else "#"

        # عرض بطاقة الطالبة
        st.markdown(f"""
            <div class="student-card">
                <h3 style="color:#2E86C1; margin:0;">👤 {student['name']}</h3>
                <p style="margin:8px 0; font-size:16px;">🏠 {student.get('sakanat', {}).get('name', 'N/A')} | 📞 {student['phone']}</p>
                <p style="color:#5d6d7e; font-size:14px;">📝 <b>ملاحظات:</b> {student['notes'] if student['notes'] else 'لا يوجد ملاحظات مسجلة'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار التفاعلية
        col_wa, col_files, col_manage = st.columns([1, 2.5, 1])
        
        with col_wa:
            st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
            
        with col_files:
            f_cols = st.columns(3)
            file_types = [("🪪 الهوية", "file_id"), ("📜 العقد", "file_contract"), ("💵 الكمبيالة", "file_kumbiala")]
            for i, (label, db_col) in enumerate(file_types):
                if student.get(db_col):
                    url = supabase.storage.from_("student_files").get_public_url(student[db_col])
                    f_cols[i].link_button(label, f"{url}?download=", use_container_width=True, key=f"file_{db_col}_{sid}")
                else:
                    f_cols[i].button(f"❌ {label[2:]}", disabled=True, use_container_width=True, key=f"none_{db_col}_{sid}")

        with col_manage:
            if st.button("⚙️ خيارات", key=f"manage_{sid}", use_container_width=True):
                st.session_state[f"form_{sid}"] = not st.session_state.get(f"form_{sid}", False)

        # فورم التعديل والحذف
        if st.session_state.get(f"form_{sid}", False):
            with st.container():
                st.markdown("<div style='background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd;'>", unsafe_allow_html=True)
                st.subheader("✏️ تعديل بيانات الطالبة")
                e_name = st.text_input("الاسم", student['name'], key=f"en_{sid}")
                e_phone = st.text_input("الهاتف", student['phone'], key=f"ep_{sid}")
                e_notes = st.text_area("الملاحظات", student['notes'], key=f"em_{sid}")
                
                c_save, c_del = st.columns(2)
                if c_save.button("حفظ التغييرات ✅", key=f"es_{sid}", use_container_width=True):
                    supabase.table("students").update({"name": e_name, "phone": e_phone, "notes": e_notes}).eq("id", sid).execute()
                    st.success("تم التحديث بنجاح!")
                    st.rerun()
                
                if c_del.button("🗑️ حذف الطالبة", key=f"ed_{sid}", type="primary", use_container_width=True):
                    st.session_state[f"confirm_{sid}"] = True
                
                if st.session_state.get(f"confirm_{sid}", False):
                    st.warning("⚠️ هل أنت متأكد من حذف الطالبة نهائياً؟")
                    if st.button("نعم، متأكد ❌", key=f"final_del_{sid}"):
                        supabase.table("students").delete().eq("id", sid).execute()
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

with tab_stats:
    st.subheader("📊 نظرة عامة على السكن")
    s1, s2, s3 = st.columns(3)
    s1.metric("إجمالي الطالبات", len(t_data))
    s2.metric("عدد الشقق", len(s_data))
    s3.metric("حالة الخادم", "متصل ✅")
    # هنا يمكن إضافة رسومات بيانية لاحقاً لمهندسنا الطموح

with tab_dev:
    st.subheader("🛠️ ركن المطور")
    st.info("هذا القسم مخصص للمطور لمراقبة أداء النظام وسجلات الوصول.")
    d_pwd = st.text_input("أدخل رمز الوصول الخاص بالمطور:", type="password")
    if d_pwd == DEV_LOG_PWD:
        st.success("أهلاً بك يا بشمهندس محمد صفيان. تم التحقق من هويتك.")
        try:
            logs = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(10).execute()
            if logs.data:
                st.write("📋 **آخر 10 عمليات دخول للنظام:**")
                for log in logs.data:
                    st.write(f"🕒 `{log['login_time'][11:16]}` | الجهاز: **{log['device_info']}**")
            else:
                st.write("لا توجد سجلات دخول مسجلة حالياً.")
        except:
            st.error("خطأ في جلب السجلات. تأكد من أن الجدول `login_logs` متاح.")
    elif d_pwd != "":
        st.error("رمز المطور غير صحيح.")

# --- 7. التذييل (Footer) ---
st.markdown(f"""
    <div class="footer">
        تم تطوير هذا النظام بكل فخر بواسطة <b>{DEV_NAME}</b><br>
        سكنات شكّور للإدارة المتكاملة | جميع الحقوق محفوظة لعام 2026<br>
        الإصدار المعتمد {VERSION}
    </div>
""", unsafe_allow_html=True)

# زر تسجيل الخروج في الأسفل
if st.button("🚪 تسجيل الخروج من النظام", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()