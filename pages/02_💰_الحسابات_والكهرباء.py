import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات والأمان الفائق ---
VERSION = "3.4 Ultimate SaaS"
st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

# نظام الدخول بالاسم لضبط المسؤولية
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if not st.session_state["user_name"]:
    st.markdown("<h2 style='text-align: center; font-family: Cairo;'>🔐 بوابة الإدارة المالية</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        name_input = st.text_input("ادخل اسمك لبدء العمل", placeholder="مثلاً: محمد، أحمد...")
        if st.button("دخول للنظام 🚀", use_container_width=True):
            if name_input:
                st.session_state["user_name"] = name_input
                st.rerun()
    st.stop()

# الاتصال بـ Supabase
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("⚠️ فشل الاتصال بالسيرفر، تأكد من الإعدادات.")
    st.stop()

# --- 2. التنسيق البصري الاحترافي (Professional UX) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; height: 0 !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: flex-start; }
    .stTabs [data-baseweb="tab"] { background: #f8f9fa; border-radius: 5px; padding: 10px 15px; }
    .stTabs [aria-selected="true"] { background: #2e86de !important; color: white !important; }

    /* بطاقات الفواتير */
    .bill-card {
        background: white; border-radius: 12px; padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;
        border-right: 8px solid #2e86de; transition: 0.3s;
    }
    .owner-card { border-right: 8px solid #10ac84; background: #f0fdf4; }
    .archived-card { border-right: 8px solid #95a5a6; opacity: 0.7; background: #f1f2f6; }
    .status-badge { padding: 3px 10px; border-radius: 15px; font-size: 11px; font-weight: bold; }
    .bg-active { background: #e3f2fd; color: #1976d2; }
    .bg-settled { background: #e8f5e9; color: #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try:
        supabase.table("audit_logs").insert({
            "action": action, "details": details, "user_name": st.session_state["user_name"]
        }).execute()
    except: pass

# --- 3. محرك البيانات ---
def fetch_all():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").neq("is_deleted", True).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone, sakan_id)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*, student_ledger(student_id, type, students(name))").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = fetch_all()

# --- 4. واجهة التطبيق ---
st.title("💼 إدارة الحسابات المالية الاحترافية")
st.caption(f"المسؤول الحالي: {st.session_state['user_name']}")

tabs = st.tabs(["📊 الملخص", "➕ إصدار مطالبة", "🗓️ العمليات النشطة", "💰 التحصيل", "📜 الأرشيف والحركات"])

# ==========================================
# التبويب 1: الملخص
# ==========================================
with tabs[0]:
    st.subheader("🏢 تقرير الشقق")
    summary = []
    for apt in s_data:
        std_ids = [std['id'] for std in t_data if std['sakan_id'] == apt['id']]
        ledger = [x for x in l_data if x['student_id'] in std_ids]
        due = sum([float(x.get('amount_due', 0)) for x in ledger])
        paid = sum([float(x.get('amount_paid', 0)) for x in ledger])
        summary.append({"الشقة": apt['name'], "المطلوب": f"{due:,.2f}", "المحصل": f"{paid:,.2f}", "الباقي": f"{due-paid:,.2f}"})
    if summary: st.table(pd.DataFrame(summary))

# ==========================================
# التبويب 2: إصدار مطالبة (إيجار/كهرباء/صيانة)
# ==========================================
with tabs[1]:
    if not s_data: st.info("يرجى إضافة شقة أولاً")
    else:
        apt_sel = st.selectbox("🏘️ اختر الشقة:", [s['name'] for s in s_data], key="sel_apt")
        target_apt = next(s for s in s_data if s['name'] == apt_sel)
        stds_in_apt = [std for std in t_data if std['sakan_id'] == target_apt['id']]
        
        with st.form("billing_form"):
            col1, col2 = st.columns(2)
            b_type = col1.selectbox("نوع العملية", ["إيجار", "كهرباء", "صيانة", "إنترنت", "أخرى"])
            total_v = col2.number_input("المبلغ الإجمالي", min_value=0.0)
            
            b_notes = st.text_area("الملاحظات")
            is_owner = st.checkbox("🚩 المصروف على حساب المالك (لا يوزع على الطالبات)")
            
            shares = {}
            if not is_owner and stds_in_apt:
                st.write("⚖️ توزيع الحصص:")
                def_v = round(total_v / len(stds_in_apt), 2) if total_v > 0 else 0.0
                c_s1, c_s2 = st.columns(2)
                for i, std in enumerate(stds_in_apt):
                    with (c_s1 if i % 2 == 0 else c_s2):
                        shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_v, key=f"s_{std['id']}")
            
            if st.form_submit_button("إصدار الفاتورة ✅"):
                try:
                    final_n = f"{b_notes} | {'(مالك)' if is_owner else '(طالبات)'}"
                    res = supabase.table("electricity_bills").insert({
                        "sakan_id": target_apt['id'], "total_amount": total_v, 
                        "bill_type": b_type, "bill_month": str(datetime.date.today().strftime("%Y-%m")),
                        "notes": final_n, "status": "نشطة"
                    }).execute()
                    
                    if not is_owner and shares:
                        b_id = res.data[0]['id']
                        l_recs = [{"student_id": sid, "bill_id": b_id, "type": b_type, "amount_due": amt} for sid, amt in shares.items()]
                        supabase.table("student_ledger").insert(l_recs).execute()
                    
                    log_action("إصدار", f"أصدر {st.session_state['user_name']} {b_type} لشقة {apt_sel} بمبلغ {total_v}")
                    st.success("تم الحفظ!")
                    st.rerun()
                except Exception as e: st.error(f"خطأ: {e}")

# ==========================================
# التبويب 3: العمليات النشطة (الإدارة والاستحقاق)
# ==========================================
with tabs[2]:
    active_bills = [b for b in b_data if not b.get('is_archived', False)]
    if not active_bills: st.info("لا توجد فواتير نشطة حالياً.")
    
    for bill in active_bills:
        is_owner_bill = "(مالك)" in (bill.get('notes') or "")
        status = bill.get('status', 'نشطة')
        card_style = "owner-card" if is_owner_bill else ""
        
        st.markdown(f"""
            <div class="bill-card {card_style}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{bill.get('bill_type')} - {bill.get('sakanat',{}).get('name')}</h3>
                    <span style="font-size:18px; font-weight:bold; color:#2e86de;">{bill['total_amount']:,.2f} د.أ</span>
                </div>
                <div style="margin-top:10px;">
                    <span class="status-badge bg-{'active' if status == 'نشطة' else 'settled'}">{status}</span>
                    <small style="color:#666;"> | {bill['bill_month']} | {bill.get('notes', '')}</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, _ = st.columns([1, 1, 1, 2])
        
        # خيار تم الاستحقاق (خاصة للمالك)
        if status == 'نشطة':
            if c1.button("✅ تم الاستحقاق", key=f"settle_{bill['id']}"):
                supabase.table("electricity_bills").update({"status": "مستحقة"}).eq("id", bill['id']).execute()
                log_action("استحقاق", f"تم تعليم فاتورة {bill['id']} كمستحقة من قبل {st.session_state['user_name']}")
                st.rerun()
        
        # خيار الأرشفة (إخفاء من القائمة النشطة)
        if c2.button("📦 أرشفة", key=f"arc_{bill['id']}"):
            supabase.table("electricity_bills").update({"is_archived": True}).eq("id", bill['id']).execute()
            log_action("أرشفة", f"أرشفة فاتورة {bill['id']}")
            st.rerun()
            
        # حذف نهائي
        if c3.button("🗑️ حذف", key=f"del_{bill['id']}", type="primary"):
            supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
            log_action("حذف", f"حذف فاتورة رقم {bill['id']}")
            st.rerun()

# ==========================================
# التبويب 4: التحصيل المفلتر
# ==========================================
with tabs[3]:
    f_apt = st.selectbox("🔍 فلترة حسب الشقة:", ["الكل"] + [s['name'] for s in s_data], key="filter_collection")
    p_list = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
    if f_apt != "الكل":
        s_id = next(s['id'] for s in s_data if s['name'] == f_apt)
        p_list = [l for l in p_list if l['students']['sakan_id'] == s_id]

    if not p_list: st.success("لا يوجد مطالبات مالية قائمة.")
    else:
        for p in p_list:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                rem = float(p['amount_due']) - float(p['amount_paid'])
                col1.write(f"👤 **{p['students']['name']}** | {p['type']}")
                col2.write(f"المتبقي: **{rem:,.2f}**")
                if col3.button("تم التحصيل ✅", key=f"pay_{p['id']}"):
                    supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                    supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": st.session_state['user_name']}).execute()
                    log_action("تحصيل", f"استلم {st.session_state['user_name']} مبلغ {rem} من {p['students']['name']}")
                    st.rerun()

# ==========================================
# التبويب 5: الأرشيف والسجل المالي
# ==========================================
with tabs[4]:
    sub1, sub2 = st.tabs(["📂 الأرشيف (الفواتير المؤرشفة)", "📜 سجل الحركات"])
    
    with sub1:
        archived = [b for b in b_data if b.get('is_archived', False)]
        for ab in archived:
            st.markdown(f"""<div class="bill-card archived-card">
                <b>{ab['bill_type']} - {ab.get('sakanat',{}).get('name')}</b> | {ab['total_amount']:,.2f} د.أ<br>
                <small>الحالة: {ab['status']} | مؤرشفة</small></div>""", unsafe_allow_html=True)
            if st.button("↩️ استعادة", key=f"unarc_{ab['id']}"):
                supabase.table("electricity_bills").update({"is_archived": False}).eq("id", ab['id']).execute()
                st.rerun()

    with sub2:
        logs = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(50).execute().data
        for g in logs:
            dt = pd.to_datetime(g['created_at']).strftime('%H:%M | %Y-%m-%d')
            st.write(f"🕒 `{dt}` | 👤 **{g.get('user_name', 'System')}** | {g['action']}: {g['details']}")