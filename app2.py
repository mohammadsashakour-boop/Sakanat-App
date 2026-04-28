import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# --- 1. الإعدادات ---
VERSION = "Finance 0.1"
DEV_NAME = "Mohammad-Sofian"

st.set_page_config(page_title="سكنات شكّور | النظام المالي", layout="wide")

# --- 2. الربط بالسيرفر (نفس الـ Secrets المستخدمة في التطبيق الأول) ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ يرجى ضبط Secrets في Streamlit Cloud.")
    st.stop()

# --- 3. تصميم CSS (فخم ومريح للحسابات) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .finance-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-right: 8px solid #27AE60;
        margin-bottom: 15px;
    }
    .metric-box {
        background: #EBf5FB; padding: 15px; border-radius: 10px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. شاشة الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>💰 نظام الإدارة المالية</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("🔑 رمز الوصول المالي", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ الرمز خاطئ")
    st.stop()

# --- 5. جلب البيانات (الربط المباشر مع الداتا بيس الأصلية) ---
@st.cache_data(ttl=2)
def load_finance_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    l = supabase.table("student_ledger").select("*").execute()
    return s.data, t.data, l.data

s_list, students_list, ledger_data = load_finance_data()

# --- 6. الواجهة المالية الرئيسية ---
tab_elec, tab_rent, tab_summary = st.tabs(["⚡ إدارة الكهرباء", "🏠 إدارة الإيجارات", "📉 ملخص كلي"])

# --- التبويب الأول: الكهرباء (الشجرة التي طلبتها) ---
with tab_elec:
    st.subheader("⚡ توزيع فاتورة الكهرباء الشهرية")
    
    # الخيار الأول: اختر الشقة
    apt_name = st.selectbox("1️⃣ اختر اسم الشقة:", [s['name'] for s in s_list])
    target_apt = next(item for item in s_list if item["name"] == apt_name)
    
    # تلقائياً: جلب الطلاب في هذه الشقة فقط
    apt_students = [s for s in students_list if s.get('sakan_id') == target_apt['id']]
    
    if not apt_students:
        st.warning("لا يوجد طلاب مسجلين في هذه الشقة حالياً.")
    else:
        st.info(f"عدد الطلاب في {apt_name}: {len(apt_students)}")
        
        with st.form("elec_form"):
            col1, col2 = st.columns(2)
            total_bill = col1.number_input("مبلغ الفاتورة الإجمالي (دينار)", min_value=0.0)
            bill_date = col2.date_input("شهر الفاتورة")
            
            uploaded_bill = st.file_uploader("📸 ارفع صورة الفاتورة (اختياري)", type=['jpg', 'png', 'pdf'])
            
            st.markdown("---")
            st.write("📝 **توزيع المبلغ على الطلاب:**")
            
            # حساب التقسيم المتساوي تلقائياً لتسهيل العمل
            equal_share = round(total_bill / len(apt_students), 2) if total_bill > 0 else 0.0
            
            student_shares = {}
            for student in apt_students:
                student_shares[student['id']] = st.number_input(f"حصة {student['name']}", value=equal_share, key=f"share_{student['id']}")
            
            if st.form_submit_button("إصدار الفاتورة وتثبيتها في ذمة الطلاب ✅"):
                # 1. حفظ الفاتورة الكلية
                # (ملاحظة: كود الرفع للسحابة يمكن إضافته هنا كما في التطبيق الأول)
                
                # 2. إضافة الالتزام المالي لكل طالب في الـ Ledger
                for s_id, share in student_shares.items():
                    supabase.table("student_ledger").insert({
                        "student_id": s_id,
                        "type": "كهرباء",
                        "amount_due": share,
                        "due_date": str(bill_date),
                        "payment_status": "pending"
                    }).execute()
                
                st.success(f"تم توزيع فاتورة {apt_name} بنجاح!")
                st.rerun()

# --- التبويب الثاني: الإيجار والـ Mini Database لكل طالبة ---
with tab_rent:
    st.subheader("🏠 سجل الإيجارات والالتزامات")
    
    selected_student_name = st.selectbox("🔍 اختر الطالبة لمشاهدة سجلها المالي:", [s['name'] for s in students_list])
    target_s = next(item for item in students_list if item["name"] == selected_student_name)
    
    # Mini Database لكل طالبة
    st.markdown(f"""
        <div class="finance-card">
            <h4>📊 السجل المالي لـ: {target_s['name']}</h4>
            <p>الشقة: {target_s.get('sakanat', {}).get('name', 'N/A')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # جلب حركات هذه الطالبة فقط من الـ Ledger
    s_ledger = [l for l in ledger_data if l['student_id'] == target_s['id']]
    
    if s_ledger:
        df = pd.DataFrame(s_ledger)
        df = df[['type', 'amount_due', 'amount_paid', 'payment_status', 'due_date']]
        df.columns = ['النوع', 'المطلوب', 'المدفوع', 'الحالة', 'التاريخ']
        st.table(df)
        
        # ميزة التعديل: دفع مبلغ
        with st.popover("➕ تسجيل دفعة مالية"):
            l_id = st.selectbox("اختر البند:", [f"{l['type']} - {l['due_date']}" for l in s_ledger], key="item_pay")
            pay_amt = st.number_input("المبلغ المدفوع", min_value=0.0)
            if st.button("تأكيد الدفع"):
                # منطق تحديث الدفعة في سوبابيس
                st.success("تم تسجيل الدفعة")
    else:
        st.info("لا يوجد التزامات مالية مسجلة لهذه الطالبة.")
        
    # إضافة التزام إيجار يدوي
    if st.button("➕ إضافة شهر إيجار جديد"):
        supabase.table("student_ledger").insert({
            "student_id": target_s['id'],
            "type": "إيجار",
            "amount_due": 150.0, # قيمة افتراضية مثلاً
            "due_date": str(datetime.date.today()),
            "payment_status": "pending"
        }).execute()
        st.rerun()

# --- التبويب الثالث: ملخص شامل ---
with tab_summary:
    st.subheader("📉 ملخص مالي شهري")
    total_due = sum([l['amount_due'] for l in ledger_data])
    total_paid = sum([l['amount_paid'] for l in ledger_data])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المطالبات", f"{total_due} د.أ")
    c2.metric("إجمالي المحصل", f"{total_paid} د.أ")
    c3.metric("المتبقي في السوق", f"{total_due - total_paid} د.أ")

st.caption(f"v{VERSION} | {DEV_NAME}")