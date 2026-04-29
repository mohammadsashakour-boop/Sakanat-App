import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات ونظام الدخول بالاسم ---
VERSION = "3.5 Final Elite"
st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if not st.session_state["user_name"]:
    st.markdown("<h2 style='text-align: center;'>🔐 بوابة الدخول المالية</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        name_input = st.text_input("ادخل اسمك للمتابعة", placeholder="مثلاً: محمد، أحمد...")
        if st.button("دخول 🚀", use_container_width=True):
            if name_input:
                st.session_state["user_name"] = name_input
                st.rerun()
    st.stop()

# الاتصال بالسيرفر
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("⚠️ خطأ في الاتصال بالسيرفر")
    st.stop()

# --- 2. التنسيق البصري الاحترافي ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; height: 0 !important; }
    
    .bill-card {
        background: white; border-radius: 12px; padding: 18px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 12px;
        border-right: 8px solid #2e86de;
    }
    .owner-card { border-right: 8px solid #10ac84; background: #f0fdf4; }
    .date-tag { background: #eef2f7; padding: 3px 10px; border-radius: 5px; font-size: 12px; color: #555; font-weight: bold; }
    .status-active { color: #2e86de; font-weight: bold; }
    .status-paid { color: #10ac84; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try:
        supabase.table("audit_logs").insert({
            "action": action, "details": details, "user_name": st.session_state["user_name"]
        }).execute()
    except: pass

# --- 3. جلب البيانات ---
def fetch_all():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").neq("is_deleted", True).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone, sakan_id)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*, student_ledger(student_id, type, bill_month, students(name))").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = fetch_all()

# --- 4. واجهة المستخدم ---
st.title("💼 المركز المالي المتكامل")
st.caption(f"المسؤول: {st.session_state['user_name']} | الإصدار: {VERSION}")

tabs = st.tabs(["📊 نظرة عامة", "➕ إصدار مطالبة", "🗓️ إدارة الفواتير", "💰 تحصيل الطالبات", "📜 السجل المالي"])

# ==========================================
# التبويب 1: نظرة عامة
# ==========================================
with tabs[0]:
    st.subheader("🏢 الموقف المالي للشقق")
    summary = []
    for apt in s_data:
        std_ids = [std['id'] for std in t_data if std['sakan_id'] == apt['id']]
        ledger = [x for x in l_data if x['student_id'] in std_ids]
        due = sum([float(x.get('amount_due', 0)) for x in ledger])
        paid = sum([float(x.get('amount_paid', 0)) for x in ledger])
        summary.append({
            "الشقة": apt['name'], "المطلوب": f"{due:,.2f}", "المحصل": f"{paid:,.2f}", "المتبقي": f"{due-paid:,.2f}", "الحالة": "✅" if (due-paid) <= 0 else "⚠️"
        })
    st.table(pd.DataFrame(summary))

# ==========================================
# التبويب 2: إصدار مطالبة (مع التواريخ التفصيلية)
# ==========================================
with tabs[1]:
    st.subheader("📝 إصدار فاتورة أو مصروف جديد")
    apt_sel = st.selectbox("🏘️ اختر الشقة المستهدفة:", [s['name'] for s in s_data], key="apt_main")
    target_apt = next(s for s in s_data if s['name'] == apt_sel)
    stds_in_apt = [std for std in t_data if std['sakan_id'] == target_apt['id']]
    
    st.info(f"عدد الطالبات في {apt_sel}: {len(stds_in_apt)}")
    
    with st.form("new_bill_form"):
        col1, col2, col3 = st.columns(3)
        b_type = col1.selectbox("النوع", ["إيجار", "كهرباء", "صيانة", "إنترنت", "أخرى"])
        total_v = col2.number_input("المبلغ الإجمالي", min_value=0.0)
        # ميزة اختيار الشهر المالي بدقة
        b_month = col3.selectbox("شهر المستحق", [f"{m:02d}-2026" for m in range(1, 13)])
        
        due_d = st.date_input("تاريخ الاستحقاق (أخر موعد للدفع)")
        b_notes = st.text_area("الملاحظات (اختياري)")
        is_owner = st.checkbox("🚩 هذا المصروف على المالك بالكامل")
        
        shares = {}
        if not is_owner and stds_in_apt:
            st.write("⚖️ توزيع المبلغ على الطالبات:")
            def_v = round(total_v / len(stds_in_apt), 2) if total_v > 0 else 0.0
            for std in stds_in_apt:
                shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_v, key=f"s_{std['id']}")
        
        if st.form_submit_button("إصدار وتثبيت ✅"):
            try:
                # 1. إدخال الفاتورة الأساسية
                final_n = f"{b_notes} | {'(مالك)' if is_owner else '(طالبات)'}"
                res = supabase.table("electricity_bills").insert({
                    "sakan_id": target_apt['id'], "total_amount": total_v, 
                    "bill_type": b_type, "bill_month": b_month, "due_date": str(due_d),
                    "notes": final_n
                }).execute()
                
                # 2. إدخال الذمم مع التواريخ التفصيلية
                if not is_owner and shares:
                    b_id = res.data[0]['id']
                    l_recs = [{
                        "student_id": sid, "bill_id": b_id, "type": b_type, 
                        "amount_due": amt, "bill_month": b_month, "due_date": str(due_d)
                    } for sid, amt in shares.items()]
                    supabase.table("student_ledger").insert(l_recs).execute()
                
                log_action("إصدار", f"أصدر {st.session_state['user_name']} {b_type} لـ {apt_sel} لشهر {b_month}")
                st.success("تم الحفظ بنجاح")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

# ==========================================
# التبويب 3: سجل العمليات (مع تواريخ الاستحقاق)
# ==========================================
with tabs[2]:
    st.subheader("🗓️ الفواتير والمصاريف الصادرة")
    for bill in b_data:
        is_owner_bill = "(مالك)" in (bill.get('notes') or "")
        card_style = "owner-card" if is_owner_bill else ""
        
        st.markdown(f"""
            <div class="bill-card {card_style}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{bill.get('bill_type')} - {bill.get('sakanat',{}).get('name')}</h3>
                    <span style="font-size:18px; font-weight:bold; color:#2e86de;">{bill['total_amount']:,.2f} د.أ</span>
                </div>
                <div style="margin-top:10px;">
                    <span class="date-tag">🗓️ شهر: {bill.get('bill_month')}</span>
                    <span class="date-tag">⌛ استحقاق: {bill.get('due_date')}</span>
                </div>
                <div style="font-size:13px; color:#666; margin-top:8px;">
                    📝 ملاحظات: {bill.get('notes', '')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ حذف نهائي", key=f"del_{bill['id']}", type="primary"):
            supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
            log_action("حذف", f"قام {st.session_state['user_name']} بحذف فاتورة {bill.get('bill_type')} بقيمة {bill['total_amount']}")
            st.rerun()

# ==========================================
# التبويب 4: تحصيل الطالبات (تاريخ ومسمى واضح)
# ==========================================
with tabs[3]:
    st.subheader("💰 تحصيل الذمم المالية")
    f_apt = st.selectbox("🔍 تصفية حسب الشقة:", ["الكل"] + [s['name'] for s in s_data])
    
    p_list = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
    if f_apt != "الكل":
        s_id = next(s['id'] for s in s_data if s['name'] == f_apt)
        p_list = [l for l in p_list if l['students']['sakan_id'] == s_id]

    if not p_list: st.success("لا توجد مبالغ مطلوبة حالياً")
    else:
        for p in p_list:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                # المسمى الواضح الذي طلبته
                full_label = f" {p['type']} - شهر {p.get('bill_month', 'غير محدد')}"
                c1.markdown(f"👤 **{p['students']['name']}** <br> <small>{full_label} | استحقاق: {p.get('due_date')}</small>", unsafe_allow_html=True)
                
                rem = float(p['amount_due']) - float(p['amount_paid'])
                c2.write(f"المتبقي: **{rem:,.2f}**")
                
                if c3.button("تم التحصيل ✅", key=f"pay_{p['id']}"):
                    supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                    supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": st.session_state['user_name']}).execute()
                    log_action("تحصيل مالي", f"استلم {st.session_state['user_name']} مبلغ {rem} من {p['students']['name']} مقابل {full_label}")
                    st.rerun()

# ==========================================
# التبويب 5: السجل المالي العام (X فعل Y بالتاريخ)
# ==========================================
with tabs[4]:
    sub_tab1, sub_tab2 = st.tabs(["💵 سجل المقبوضات (كشف حساب)", "🛠️ سجل النظام (Audit)"])
    
    with sub_tab1:
        if not p_data: st.info("لا توجد دفعات مسجلة")
        else:
            for pay in p_data:
                p_dt = pd.to_datetime(pay['payment_date']).strftime('%Y-%m-%d | %H:%M')
                std_n = pay.get('student_ledger', {}).get('students', {}).get('name', 'مجهول')
                b_tp = pay.get('student_ledger', {}).get('type', 'ذمة')
                b_mo = pay.get('student_ledger', {}).get('bill_month', '-')
                
                st.markdown(f"""
                <div style="background:#f9fffb; border-right:5px solid #10ac84; padding:10px; margin-bottom:5px; border-radius:5px;">
                    <b>📅 {p_dt}</b> | المسؤول: <span style='color:#2e86de;'>{pay['recorded_by']}</span> <br>
                    تم استلام مبلغ <span style='color:#10ac84; font-weight:bold;'>{pay['amount_paid']:,.2f} د.أ</span> 
                    من الطالبة <b>{std_n}</b> عن (<b>{b_tp} - شهر {b_mo}</b>)
                </div>
                """, unsafe_allow_html=True)

    with sub_tab2:
        logs = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(50).execute().data
        for g in logs:
            g_dt = pd.to_datetime(g['created_at']).strftime('%H:%M | %Y-%m-%d')
            st.markdown(f"""
            <div style="background:#f1f2f6; border-right:5px solid #2e86de; padding:10px; margin-bottom:5px; border-radius:5px;">
                <b>{g_dt}</b> | المسؤول: 👤 {g.get('user_name', 'System')} | <b>{g['action']}</b>: {g['details']}
            </div>
            """, unsafe_allow_html=True)