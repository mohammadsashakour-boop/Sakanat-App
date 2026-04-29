import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات والتحقق من الهوية ---
VERSION = "3.1 Elite SaaS"
st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if not st.session_state["user_name"]:
    st.markdown("<h2 style='text-align: center; font-family: Cairo;'>🔐 الدخول للنظام المالي</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        name_input = st.text_input("ادخل اسمك (سيظهر في السجل)", placeholder="مثلاً: محمد...")
        if st.button("دخول 🚀", use_container_width=True):
            if name_input:
                st.session_state["user_name"] = name_input
                st.rerun()
    st.stop()

# --- 2. الاتصال والتنسيق البصري ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("⚠️ خطأ في الاتصال بالسيرفر")
    st.stop()

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; }
    
    /* تنسيق الجداول والبطاقات */
    .main-table { width: 100%; border-collapse: collapse; margin: 10px 0; background: white; border-radius: 8px; overflow: hidden; }
    .main-table th { background: #2e86de; color: white; padding: 12px; text-align: center; }
    .main-table td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; }
    .status-pill { padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .pill-green { background: #e9f7ef; color: #27ae60; }
    .pill-red { background: #fdedec; color: #e74c3c; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try: supabase.table("audit_logs").insert({"action": action, "details": details, "user_name": st.session_state["user_name"]}).execute()
    except: pass

# --- 3. جلب البيانات ---
def fetch_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").neq("is_deleted", True).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = fetch_data()

# --- 4. واجهة المستخدم ---
st.title("💼 مركز الإدارة المالية")

tabs = st.tabs(["📊 نظرة عامة", "➕ إصدار مطالبة", "🗓️ سجل الفواتير", "💰 التحصيل", "📜 السجل العام"])

# ==========================================
# التبويب 1: نظرة عامة (جدول ملخص الشقق)
# ==========================================
with tabs[0]:
    st.subheader("🏢 ملخص الأداء المالي لكل شقة")
    apt_summary = []
    for apt in s_data:
        apt_stds = [std['id'] for std in t_data if std['sakan_id'] == apt['id']]
        apt_l = [entry for entry in l_data if entry['student_id'] in apt_stds]
        
        due = sum([float(x.get('amount_due', 0)) for x in apt_l])
        paid = sum([float(x.get('amount_paid', 0)) for x in apt_l])
        rem = due - paid
        status = "✅ مستقر" if rem <= 0 else "⚠️ بانتظار تحصيل"
        
        apt_summary.append({
            "الشقة": apt['name'],
            "إجمالي المطلوب": f"{due:,.2f}",
            "المحصل": f"{paid:,.2f}",
            "المتبقي": f"{rem:,.2f}",
            "الحالة": status
        })
    
    if apt_summary:
        st.table(pd.DataFrame(apt_summary))
    else: st.info("لا توجد بيانات حالياً.")

# ==========================================
# التبويب 2: إصدار مطالبة (حل مشكلة التحديث اللحظي)
# ==========================================
with tabs[1]:
    st.subheader("📝 إنشاء فاتورة أو مصروف")
    
    # اختيار الشقة خارج الفورم لضمان تحديث قائمة الطالبات فوراً
    apt_sel_name = st.selectbox("🏘️ اختر الشقة المستهدفة:", [s['name'] for s in s_data], key="apt_trigger")
    selected_apt_obj = next(s for s in s_data if s['name'] == apt_sel_name)
    
    # تصفية الطالبات فورياً بناءً على الاختيار أعلاه
    current_apt_stds = [std for std in t_data if std['sakan_id'] == selected_apt_obj['id']]
    
    st.info(f"عدد الطالبات المكتشفات في هذه الشقة: {len(current_apt_stds)}")
    
    with st.form("new_pro_bill"):
        col1, col2 = st.columns(2)
        b_type = col1.selectbox("نوع العملية", ["كهرباء", "إيجار", "صيانة", "إنترنت", "خدمات"])
        total_v = col2.number_input("المبلغ الإجمالي (د.أ)", min_value=0.0)
        
        # ميزة الملاحظات والمالك
        col3, col4 = st.columns([2, 1])
        b_notes = col3.text_input("ملاحظات إضافية على الفاتورة", placeholder="مثلاً: صيانة المصعد، فاتورة شهر 4...")
        is_owner = col4.checkbox("على حساب المالك")
        
        shares = {}
        if not is_owner and current_apt_stds:
            st.write("⚖️ توزيع الذمم على الطالبات:")
            def_v = round(total_v / len(current_apt_stds), 2) if total_v > 0 else 0.0
            c_s1, c_s2 = st.columns(2)
            for i, std in enumerate(current_apt_stds):
                with (c_s1 if i % 2 == 0 else c_s2):
                    shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_v, key=f"s_val_{std['id']}")
        
        if st.form_submit_button("إصدار وتثبيت العملية ✅"):
            try:
                # 1. إدخال الفاتورة الأم
                final_notes = f"{b_notes} | {'(بذمة المالك)' if is_owner else '(بذمة الطالبات)'}"
                b_res = supabase.table("electricity_bills").insert({
                    "sakan_id": selected_apt_obj['id'], "total_amount": total_v, 
                    "bill_type": b_type, "bill_month": str(datetime.date.today().strftime("%Y-%m")),
                    "notes": final_notes
                }).execute()
                
                # 2. إدخال الذمم
                if not is_owner and shares:
                    b_id = b_res.data[0]['id']
                    l_entries = [{"student_id": sid, "bill_id": b_id, "type": b_type, "amount_due": amt, "status": "pending"} for sid, amt in shares.items()]
                    supabase.table("student_ledger").insert(l_entries).execute()
                
                log_action("إصدار فاتورة", f"أصدر {st.session_state['user_name']} {b_type} لـ {apt_sel_name} بمبلغ {total_v}")
                st.success("تم التثبيت بنجاح!")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

# ==========================================
# التبويب 3: سجل الفواتير
# ==========================================
with tabs[2]:
    for bill in b_data:
        is_owner_bill = "(بذمة المالك)" in (bill.get('notes') or "")
        st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-right:8px solid {'#10ac84' if is_owner_bill else '#2e86de'}; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <b>{bill.get('bill_type')} - {bill.get('sakanat',{}).get('name')}</b>
                    <span style="color:#2e86de;">{bill['total_amount']} د.أ</span>
                </div>
                <div style="font-size:12px; color:#777; margin-top:5px;">
                    📝 ملاحظات: {bill.get('notes', 'لا يوجد')} | 📅 {pd.to_datetime(bill['created_at']).strftime('%Y-%m-%d')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ حذف نهائي", key=f"del_b_{bill['id']}", type="primary"):
            supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
            log_action("حذف فاتورة", f"قام {st.session_state['user_name']} بحذف فاتورة {bill.get('bill_type')} لشقة {bill.get('sakanat',{}).get('name')}")
            st.rerun()

# ==========================================
# التبويب 4: التحصيل
# ==========================================
with tabs[3]:
    pending_list = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
    for p in pending_list:
        with st.container(border=True):
            cp1, cp2, cp3 = st.columns([2, 1, 1])
            cp1.write(f"👤 **{p['students']['name']}** | {p['type']}")
            rem = float(p['amount_due']) - float(p['amount_paid'])
            cp2.write(f"المتبقي: **{rem:,.2} د.أ**")
            if cp3.button("تم التحصيل ✅", key=f"pay_led_{p['id']}"):
                supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": st.session_state['user_name']}).execute()
                log_action("تحصيل", f"حصل {st.session_state['user_name']} مبلغ {rem} من {p['students']['name']}")
                st.rerun()

# ==========================================
# التبويب 5: السجل العام (X فعل Y)
# ==========================================
with tabs[4]:
    st.subheader("📜 سجل الرقابة والعمليات")
    logs = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(50).execute().data
    for g in logs:
        st.markdown(f"""
            <div style="border-bottom: 1px solid #eee; padding: 8px;">
                <span style="color:#2e86de; font-weight:bold;">👤 {g.get('user_name', 'System')}</span> 
                | <b>{g['action']}</b> | <small>{pd.to_datetime(g['created_at']).strftime('%H:%M | %Y-%m-%d')}</small><br>
                <span style="color:#555; font-size:13px;">{g['details']}</span>
            </div>
        """, unsafe_allow_html=True)