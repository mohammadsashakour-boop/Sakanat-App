import streamlit as st
from supabase import create_client, Client
from streamlit_javascript import st_javascript
import pandas as pd

# --- 1. الإعدادات الأساسية ---
VERSION = "0.3"
DEV_NAME = "Mohammad-Sofian"

st.set_page_config(page_title=f"سكنات شكّور Pro v{VERSION}", layout="wide", page_icon="🏢")

# --- 2. جلب المفاتيح من السيرفر (Secrets) ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("⚠️ خطأ في الإعدادات السرية (Secrets). تأكد من وضعها في Streamlit Cloud.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 3. تصميم الواجهة (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .main {{ background-color: #f8fafc; }}
    .st-card {{
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-right: 10px solid #2E86C1;
        margin-bottom: 20px;
    }}
    .dev-tag {{
        position: fixed; bottom: 10px; left: 10px; background: #2E86C1;
        color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; z-index: 1000;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. تعقب الأجهزة والدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🏢 نظام إدارة سكنات شكّور</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("🔑 كلمة المرور الإدارية", type="password")
        if st.button("🚀 دخول آمن", use_container_width=True):
            if pwd == ADMIN_PWD:
                # تعقب الجهاز
                ua = st_javascript("window.navigator.userAgent")
                device = "Mobile" if "Mobi" in str(ua) else "PC/Desktop"
                try: supabase.table("login_logs").insert({"device_info": device}).execute()
                except: pass
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 5. وظائف جلب البيانات ---
@st.cache_data(ttl=10)
def get_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").order('created_at', desc=True).execute()
    return s.data, t.data

sakanat, students = get_data()
df = pd.DataFrame(students) # تحويل البيانات لجدول لمعالجتها

# --- 6. القائمة الجانبية ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/609/609803.png", width=80)
    st.title("لوحة التحكم")
    st.write(f"المطور: **{DEV_NAME}**")
    st.markdown("---")
    search_query = st.text_input("🔍 ابحث عن طالبة/هاتف/ملاحظة:")
    st.markdown("---")
    # ميزة تصدير البيانات
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل كشف الطالبات (Excel)", data=csv, file_name="students_list.csv", mime="text/csv")

# --- 7. الإحصائيات الذكية ---
st.title("📊 ملخص حالة السكن")
c1, c2, c3, c4 = st.columns(4)
c1.metric("إجمالي الطالبات", len(students))
c2.metric("عدد الشقق", len(sakanat))
missing_docs = sum(1 for s in students if not s.get('file_id') or not s.get('file_contract'))
c3.metric("نواقص مستندات", missing_docs)
c4.metric("الإصدار", VERSION)

st.markdown("---")

# --- 8. العرض والفلترة ---
selected_sakan = st.selectbox("📍 تصفية حسب الشقة:", ["الكل"] + [s['name'] for s in sakanat])

filtered = students
if selected_sakan != "الكل":
    filtered = [s for s in students if s.get('sakanat') and s['sakanat']['name'] == selected_sakan]
if search_query:
    filtered = [s for s in filtered if search_query.lower() in str(s).lower()]

# عرض البطاقات
for s in filtered:
    sid = str(s['id'])
    # تنظيف رقم الواتساب
    phone = str(s['phone']).replace(' ', '').replace('+', '')
    if phone.startswith('07'): phone = "962" + phone[1:]

    with st.container():
        st.markdown(f"""
            <div class="st-card">
                <h3 style="margin:0; color:#2E86C1;">👤 {s['name']}</h3>
                <p style="margin:5px 0;">🏠 <b>الشقة:</b> {s.get('sakanat', {}).get('name', 'N/A')} | 📞 <b>الهاتف:</b> {s['phone']}</p>
                <p style="color:#7f8c8d; font-size:14px;">📝 <b>ملاحظات:</b> {s['notes'] if s['notes'] else 'لا يوجد'}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # الأزرار
        f_cols = st.columns([1,1,1,1,1,1])
        # زر واتساب
        f_cols[0].link_button("💬 WhatsApp", f"https://wa.me/{phone}")
        # الملفات
        labels = [("🪪 الهوية", 'file_id'), ("📜 العقد", 'file_contract'), ("💵 الكمبيالة", 'file_kumbiala')]
        for i, (lab, col) in enumerate(labels):
            path = s.get(col)
            if path:
                url = supabase.storage.from_("student_files").get_public_url(path)
                f_cols[i+1].link_button(lab, f"{url}?download=")
            else:
                f_cols[i+1].button(f"❌ {lab[2:]}", key=f"m_{col}_{sid}", disabled=True)
        
        # تعديل وحذف
        with f_cols[4].popover("✏️"):
            new_n = st.text_input("الاسم", value=s['name'], key=f"n_{sid}")
            if st.button("حفظ", key=f"sv_{sid}"):
                supabase.table("students").update({"name": new_n}).eq("id", sid).execute()
                st.rerun()
        
        if f_cols[5].button("🗑️", key=f"del_{sid}"):
            if st.checkbox("تأكيد؟", key=f"c_{sid}"):
                supabase.table("students").delete().eq("id", sid).execute()
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# توقيع المطور
st.markdown(f'<div class="dev-tag">Designed by {DEV_NAME}</div>', unsafe_allow_html=True)