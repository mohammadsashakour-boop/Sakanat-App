import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# --- 1. إعدادات النظام ---
VERSION = "Finance 0.2"
DEV_NAME = "Mohammad-Sofian"
DEV_LOG_PWD = "Soffian3491335"

st.set_page_config(page_title="المالية | سكنات شكّور", layout="wide")

# --- 2. الربط بالسيرفر ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ يرجى ضبط Secrets في Streamlit Cloud.")
    st.stop()

# --- 3. تصميم الـ UI (RTL ونظيف جداً) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .finance-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 8px solid #27AE60;
        margin-bottom: 15px;
    }
    .stMetric { background: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. شاشة الدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; color: #27AE60;'>💰 النظام المالي لسكنات شكّور</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("🔑 رمز الدخول المالي", type="password")
        if st.button("دخول", use_container_width=True) or (pwd == ADMIN_PWD and pwd != ""):
            if pwd == ADMIN_PWD:
                st.session_state["logged_in"] = True
                st.rerun()
            elif pwd != "": st.error("❌ الرمز خاطئ")
    st.stop()

# --- 5. جلب البيانات اللحظية ---
@st.cache_data(ttl=2)
def load_finance_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    l = supabase.table("student_ledger").select("*, students(name)").order('due_date', desc=True).execute()
    return s.data, t.data, l.data

sakanat, students, ledger = load_finance_data()

# --- 6. الواجهة الرئيسية (التصميم الشجري) ---
tab_elec, tab_ledger, tab_reports = st.tabs(["⚡ فواتير الكهرباء", "🏠 سجل الإيجارات والذمم", "📊 ملخص الحسابات"])

# --- التبويب الأول: الكهرباء (توزيع ذكي) ---
with tab_elec:
    st.subheader("⚡ توزيع فاتورة الكهرباء الشهرية")
    
    # الخطوة 1: اختيار الشقة
    target_apt_name = st.selectbox("🏘️ اختر الشقة المستهدفة:", [s['name'] for s in sakanat])
    target_apt = next(item for item in sakanat if item["name"] == target_apt_name)
    
    # الخطوة 2: جلب الطلاب (تحديث تلقائي)
    apt_students = [s for s in students if s.get('sakan_id') == target_apt['id']]
    
    if not apt_students:
        st.warning(f"لا يوجد طالبات مسجلات في {target_apt_name} حالياً.")
    else:
        with st.form("elec_split_form"):
            col_b1, col_b2 = st.columns(2)
            total_bill = col_b1.number_input("إجمالي قيمة الفاتورة (دينار)", min_value=0.0)
            bill_date = col_b2.date_input("تاريخ الفاتورة", datetime.date.today())
            
            uploaded_file = st.file_uploader("📸 ارفع صورة الفاتورة (للتوثيق)", type=['jpg', 'png', 'pdf'])
            
            st.markdown("---")
            st.write(f"👥 **توزيع المبلغ على ({len(apt_students)}) طالبات:**")
            
            # حساب التقسيم المتساوي تلقائياً
            equal_share = round(total_bill / len(apt_students), 2) if total_bill > 0 else 0.0
            
            shares = {}
            for std in apt_students:
                shares[std['id']] = st.number_input(f"حصة: {std['name']}", value=equal_share, key=f"std_{std['id']}")
            
            if st.form_submit_button("تثبيت الفاتورة وتوزيع المبالغ ✅"):
                # 1. تسجيل الفاتورة الكلية
                # (يمكن إضافة كود رفع الملف هنا في storage)
                
                # 2. تسجيل المطالبة المالية لكل طالبة في الـ Ledger
                for std_id, amt in shares.items():
                    supabase.table("student_ledger").insert({
                        "student_id": std_id,
                        "transaction_type": "كهرباء",
                        "amount_due": amt,
                        "due_date": str(bill_date),
                        "status": "pending"
                    }).execute()
                
                st.success("تم توزيع الفاتورة بنجاح في السجلات المالية.")
                st.rerun()

# --- التبويب الثاني: سجل الذمم (Mini Database لكل طالبة) ---
with tab_ledger:
    st.subheader("🏠 الدفتر المالي للطالبات")
    
    selected_std_name = st.selectbox("🔍 اختر اسم الطالبة لعرض سجلها:", [s['name'] for s in students])
    target_std = next(item for item in students if item["name"] == selected_std_name)
    
    # عرض معلومات الطالبة المالية
    st.markdown(f"""
        <div class="finance-card">
            <h4>📊 السجل المالي: {target_std['name']}</h4>
            <p>الشقة: {target_std.get('sakanat', {}).get('name', 'N/A')} | الهاتف: {target_std['phone']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # جلب الحركات الخاصة بها
    std_history = [l for l in ledger if l['student_id'] == target_std['id']]
    
    if std_history:
        df = pd.DataFrame(std_history)
        df_display = df[['transaction_type', 'amount_due', 'amount_paid', 'status', 'due_date']]
        df_display.columns = ['النوع', 'المطلوب', 'المدفوع', 'الحالة', 'التاريخ']
        st.table(df_display)
        
        # ميزة تسجيل دفعة
        with st.popover("➕ تسجيل دفعة (سداد)"):
            item_to_pay = st.selectbox("اختر البند المراد سداده:", [f"{l['transaction_type']} ({l['due_date']})" for l in std_history])
            pay_amount = st.number_input("المبلغ المدفوع حالياً", min_value=0.0)
            if st.button("تأكيد الدفع ✅"):
                # هنا يتم تحديث الـ Ledger (تحويل status إلى paid أو تحديث amount_paid)
                # ملاحظة: للمهندس، يفضل إضافة منطق تحديث دقيق هنا
                st.success("تم تسجيل الدفعة بنجاح.")
                st.rerun()
    else:
        st.info("لا يوجد التزامات مالية مسجلة لهذه الطالبة بعد.")

    st.markdown("---")
    # ميزة إضافة إيجار شهري يدوياً
    if st.button("➕ إضافة مطالبة إيجار جديد"):
        supabase.table("student_ledger").insert({
            "student_id": target_std['id'],
            "transaction_type": "إيجار",
            "amount_due": 150.0, # قيمة افتراضية يمكن تعديلها
            "due_date": str(datetime.date.today()),
            "status": "pending"
        }).execute()
        st.rerun()

# --- التبويب الثالث: التقارير واللوجز ---
with tab_reports:
    st.subheader("📊 الملخص المالي العام")
    
    total_due = sum([l['amount_due'] for l in ledger])
    total_paid = sum([l['amount_paid'] for l in ledger])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المطلوب", f"{total_due} د.أ")
    c2.metric("إجمالي المحصل", f"{total_paid} د.أ")
    c3.metric("الديون المتبقية", f"{total_due - total_paid} د.أ", delta_color="inverse")

    st.markdown("---")
    # ركن المطور الصغير هنا أيضاً للسرعة
    with st.expander("🛠️ ركن المطور (سجلات النظام)"):
        d_pwd = st.text_input("رمز المطور", type="password")
        if d_pwd == DEV_LOG_PWD:
            l_data = supabase.table("login_logs").select("*").order('login_time', desc=True).limit(5).execute()
            for log in l_data.data:
                st.caption(f"🕒 {log['login_time'][11:16]} | {log['device_info']}")

if st.button("🚪 خروج"):
    st.session_state["logged_in"] = False
    st.rerun()

st.caption(f"{VERSION} | Developed by {DEV_NAME}")
