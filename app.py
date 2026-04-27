import os
import subprocess
import sys
import streamlit as st

# --- الضربة القاضية: إجبار السيرفر على تثبيت المكتبات إذا نقصت ---
def install_requirements():
    try:
        from supabase import create_client, Client
        from streamlit_javascript import st_javascript
    except ImportError:
        # السيرفر مش لاقي المكتبات؟ نثبتهم يدوياً الآن
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "streamlit-javascript"])
        st.rerun() # إعادة تشغيل التطبيق بعد التثبيت

install_requirements()

# الآن نكمل الكود الطبيعي
from supabase import create_client, Client
from streamlit_javascript import st_javascript

# --- 1. الإعدادات والتعريفات ---
VERSION = "0.2"
DEV_NAME = "Mohammad-Sofian"

st.set_page_config(
    page_title=f"سكنات شكّور v{VERSION}", 
    layout="wide", 
    page_icon="🏢"
)

# --- 2. CSS احترافي (اللمسات الجمالية للمهندس محمد) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .main {{ background-color: #f4f7f9; }}
    
    /* تصميم البطاقة الاحترافي */
    .st-card {{
        background: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border-right: 8px solid #1f77b4;
        transition: transform 0.3s ease;
        margin-bottom: 20px;
    }}
    .st-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
    }}
    
    /* العدادات العلوية */
    .metric-container {{
        background: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    
    /* توقيع المطور العائم */
    .dev-signature {{
        position: fixed;
        bottom: 10px;
        left: 10px;
        background: rgba(255,255,255,0.9);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        color: #1f77b4;
        z-index: 1000;
        border: 1px solid #1f77b4;
        font-size: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات ---
URL = "https://ypubolmsmdypefkjboyw.supabase.co" 
KEY = "sb_publishable_81O6rLCOIcOqOUDlpswSrw_nfWT5qUi"
supabase: Client = create_client(URL, KEY)

# --- 4. ميزة تعقب الجهاز (Device Tracking) ---
def log_device():
    ua_string = st_javascript("window.navigator.userAgent")
    if ua_string and "logged_device" not in st.session_state:
        device_info = "جهاز غير معروف"
        if "Mobi" in ua_string:
            if "iPhone" in ua_string: device_info = "iPhone (Mobile)"
            elif "Samsung" in ua_string: device_info = "Samsung (Mobile)"
            else: device_info = "Android/Mobile"
        else:
            if "Windows" in ua_string: device_info = "Windows PC"
            elif "Macintosh" in ua_string: device_info = "MacBook"
        
        try:
            supabase.table("login_logs").insert({"device_info": device_info}).execute()
            st.session_state["logged_device"] = True
            return device_info
        except:
            return "Device Logged"
    return "Session Active"

# --- 5. نظام الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🏢 سكنات شكّـــــــــــــــور</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container():
            pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
            if st.button("🚀 دخول للنظام", use_container_width=True):
                if pwd == "Shakur2026!":
                    log_device()
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 6. جلب البيانات وتحليلها ---
@st.cache_data(ttl=5)
def load_all_data():
    s_res = supabase.table("sakanat").select("*").order('name').execute()
    t_res = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s_res.data, t_res.data

s_list, t_list = load_all_data()
s_names = [s['name'] for s in s_list]

# حساب النواقص (الميزة الجديدة)
missing_ids = sum(1 for s in t_list if not s.get('file_id'))
missing_contracts = sum(1 for s in t_list if not s.get('file_contract'))

# --- 7. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.title("⚙️ التحكم")
    st.write(f"المطور: **{DEV_NAME}**")
    st.write(f"الإصدار: `{VERSION}`")
    st.markdown("---")
    search_q = st.text_input("🔍 ابحث (اسم، هاتف، ملاحظة):")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 8. الواجهة الرئيسية والإحصائيات ---
st.title("📋 لوحة إدارة السكن")

# عرض الإحصائيات (الهدية الثانية)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("إجمالي الطالبات", len(t_list))
with c2: st.metric("الشقق", len(s_list))
with c3: st.metric("هويات ناقصة", missing_ids, delta_color="inverse")
with c4: st.metric("عقود ناقصة", missing_contracts, delta_color="inverse")

st.markdown("---")

# تصفية البيانات
s_choice = st.selectbox("📍 تصفية حسب الشقة:", ["جميع الشقق"] + s_names)
filtered = t_list
if s_choice != "جميع الشقق":
    filtered = [s for s in t_list if s.get('sakanat') and s['sakanat']['name'] == s_choice]
if search_q:
    filtered = [s for s in filtered if search_q.lower() in s['name'].lower() or search_q in str(s['phone']) or search_q in str(s['notes'])]

# --- 9. عرض بطاقات الطالبات ---
for student in filtered:
    sid = str(student['id'])
    
    # تنظيف رقم الهاتف للواتساب
    raw_p = str(student['phone'])
    wa_phone = raw_p.replace('+', '').replace(' ', '')
    if wa_phone.startswith('07'): wa_phone = "962" + wa_phone[1:]
    
    st.markdown(f"""
        <div class="st-card">
            <h3 style="color: #1f77b4; margin-bottom: 5px;">👤 {student['name']}</h3>
            <p style="margin: 0;">🏠 <b>الشقة:</b> {student.get('sakanat', {}).get('name', 'N/A')} | 📞 <b>الهاتف:</b> {student['phone']}</p>
            <p style="color: #666;">📝 {student['notes'] if student['notes'] else 'لا يوجد ملاحظات'}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # أزرار الإجراءات (تعديل، حذف، واتساب، ملفات)
    col_files, col_actions = st.columns([2.5, 1])
    
    with col_files:
        f_cols = st.columns(4) # أربعة أعمدة لإضافة الواتساب
        # زر الواتساب (الميزة الجديدة 1)
        f_cols[0].link_button("💬 WhatsApp", f"https://wa.me/{wa_phone}", use_container_width=True)
        
        labels = [("🪪 الهوية", 'file_id'), ("📜 العقد", 'file_contract'), ("💵 الكمبيالة", 'file_kumbiala')]
        for i, (lab, col) in enumerate(labels):
            path = student.get(col)
            if path:
                url = supabase.storage.from_("student_files").get_public_url(path)
                f_cols[i+1].link_button(lab, f"{url}?download=", use_container_width=True)
            else:
                f_cols[i+1].button(f"❌ {lab[2:]}", key=f"m_{col}_{sid}", disabled=True, use_container_width=True)

    with col_actions:
        b1, b2 = st.columns(2)
        with b1:
            with st.popover("✏️ تعديل"):
                en = st.text_input("الاسم", value=student['name'], key=f"n_{sid}")
                ep = st.text_input("الهاتف", value=student['phone'], key=f"p_{sid}")
                em = st.text_area("الملاحظات", value=student['notes'], key=f"m_{sid}")
                esk = st.selectbox("نقل للشقة", s_names, index=s_names.index(student['sakanat']['name']) if student.get('sakanat') else 0, key=f"sk_{sid}")
                if st.button("حفظ التغييرات ✅", key=f"sv_{sid}"):
                    target_id = [s['id'] for s in s_list if s['name'] == esk][0]
                    supabase.table("students").update({"name": en, "phone": ep, "notes": em, "sakan_id": target_id}).eq("id", sid).execute()
                    st.success("تم الحفظ")
                    st.rerun()
        with b2:
            if st.button("🗑️ حذف", key=f"del_{sid}"):
                if st.checkbox("تأكيد؟", key=f"c_{sid}"):
                    supabase.table("students").delete().eq("id", sid).execute()
                    st.rerun()

    st.markdown("<hr style='border: 0.1px solid #ddd;'>", unsafe_allow_html=True)

# --- 10. Footer والتوقيع ---
st.markdown(f'<div class="dev-signature">Developed by {DEV_NAME} | v{VERSION}</div>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #95a5a6; padding-top: 50px;'>نظام سكنات شكّور الإداري - 2026</p>", unsafe_allow_html=True)