import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="الحسابات | سكنات شكّور", layout="wide")

# --- 2. الربط ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ خطأ في الربط: تأكد من Secrets")
    st.stop()

# --- 3. تصميم RTL ---
st.markdown("""<style>* { direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }</style>""", unsafe_allow_html=True)

# --- 4. جلب البيانات (المصلح) ---
@st.cache_data(ttl=2)
def load_finance_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    # جلب البيانات من الجدول الجديد
    l = supabase.table("student_ledger").select("*").order('created_at', desc=True).execute()
    return s.data, t.data, l.data

try:
    s_list, t_list, ledger = load_finance_data()
except Exception as e:
    st.error(f"⚠️ فشل في جلب البيانات: {e}")
    st.stop()

st.title("💰 الإدارة المالية والكهرباء")

# --- 5. شجرة الكهرباء ---
with st.expander("⚡ توزيع فاتورة الكهرباء", expanded=True):
    apt_name = st.selectbox("🏘️ اختر الشقة:", [s['name'] for s in s_list])
    target_sakan = next(item for item in s_list if item["name"] == apt_name)
    
    # جلب طالبات الشقة
    stds = [s for s in t_list if s.get('sakan_id') == target_sakan['id']]
    
    if stds:
        with st.form("elec_form"):
            val = st.number_input("مبلغ الفاتورة الكلي", min_value=0.0)
            mon = st.selectbox("عن شهر:", [f"2026-{m:02d}" for m in range(1, 13)])
            share = round(val / len(stds), 2) if val > 0 else 0.0
            st.info(f"حصة كل طالبة: {share} د.أ")
            
            if st.form_submit_button("تثبيت وحفظ ✅"):
                for std in stds:
                    supabase.table("student_ledger").insert({
                        "student_id": std['id'], "type": "كهرباء", 
                        "amount_due": share, "bill_month": mon
                    }).execute()
                st.success("تم التوزيع بنجاح!")
                st.rerun()
    else: st.warning("الشقة فارغة")

# --- 6. السجل المالي ---
st.markdown("---")
st.subheader("📅 سجل الحسابات")
if ledger:
    df = pd.DataFrame(ledger)[['bill_month', 'type', 'amount_due', 'payment_status']]
    df.columns = ['الشهر', 'البند', 'المطلوب', 'الحالة']
    st.table(df)
else:
    st.info("لا توجد سجلات مالية بعد.")