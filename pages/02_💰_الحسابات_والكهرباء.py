import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# --- 1. الإعدادات وهوية النظام ---
VERSION = "4.5 SaaS Fortress Edition"
st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

# نظام الدخول بالاسم لضبط المسؤولية والرقابة
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if not st.session_state["user_name"]:
    st.markdown("<h2 style='text-align: center; font-family: Cairo;'>🔐 بوابة الإدارة المالية المحصنة</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        name_input = st.text_input("اسم المستخدم للرقابة", placeholder="من يقوم بالعملية حالياً؟")
        if st.button("دخول آمن 🚀", use_container_width=True):
            if name_input:
                st.session_state["user_name"] = name_input
                st.rerun()
    st.stop()

# الاتصال المحمي بقاعدة البيانات
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("⚠️ فشل في الاتصال بقاعدة البيانات. تأكد من الإعدادات.")
    st.stop()

# --- 2. التصميم البصري الاحترافي (SaaS UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; height: 0 !important; }
    
    .bill-card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-right: 8px solid #2e86de; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .owner-card { border-right-color: #10ac84; background: #f0fdf4; }
    .kpi-box { background: #ffffff; padding: 20px; border-radius: 10px; border-bottom: 5px solid #2e86de; text-align: center; }
    .money { color: #2e86de; font-weight: bold; font-size: 1.4em; }
    .date-tag { background: #f1f2f6; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #555; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try: supabase.table("audit_logs").insert({"action": action, "details": details, "user_name": st.session_state["user_name"]}).execute()
    except: pass

# --- 3. محرك البيانات المصفح ---
@st.cache_data(ttl=2)
def get_clean_data():
    try:
        s = supabase.table("sakanat").select("*").order('name').execute()
        t = supabase.table("students").select("*, sakanat(name)").neq("is_deleted", True).execute()
        b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
        l = supabase.table("student_ledger").select("*, students(name, phone, sakan_id)").order('due_date', desc=True).execute()
        p = supabase.table("payments").select("*, student_ledger(student_id, type, bill_month, students(name))").order('payment_date', desc=True).execute()
        return s.data, t.data, b.data, l.data, p.data
    except: return [], [], [], [], []

s_data, t_data, b_data, l_data, p_data = get_clean_data()

# --- 4. واجهة النظام الرئيسية ---
st.title("💼 المركز المالي الشامل")
st.caption(f"المسؤول الحالي: {st.session_state['user_name']} | النسخة {VERSION}")

tabs = st.tabs(["📊 لوحة التحكم", "🧾 إصدار مطالبة", "🗓️ إدارة الفواتير", "💸 تحصيل الذمم", "📜 السجل والأرشيف"])

# ==========================================
# 1. لوحة التحكم (Financial Analytics)
# ==========================================
with tabs[0]:
    due_total = sum([float(x.get('amount_due', 0)) for x in l_data])
    paid_total = sum([float(x.get('amount_paid', 0)) for x in l_data])
    
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.markdown(f"<div class='kpi-box'><small>الديون المعلقة في السوق</small><br><span class='money'>{due_total - paid_total:,.2f} د.أ</span></div>", unsafe_allow_html=True)
    col_k2.markdown(f"<div class='kpi-box' style='border-color:#10ac84'><small>إجمالي التحصيل الفعلي</small><br><span class='money' style='color:#10ac84'>{paid_total:,.2f} د.أ</span></div>", unsafe_allow_html=True)
    col_k3.markdown(f"<div class='kpi-box' style='border-color:#e67e22'><small>الفواتير النشطة</small><br><span class='money' style='color:#e67e22'>{len([x for x in b_data if not x.get('is_archived')])}</span></div>", unsafe_allow_html=True)

    st.subheader("🏢 الموقف المالي لكل شقة")
    apt_analysis = []
    for apt in s_data:
        std_ids = [st['id'] for st in t_data if st['sakan_id'] == apt['id']]
        recs = [x for x in l_data if x['student_id'] in std_ids]
        d = sum([float(x.get('amount_due', 0)) for x in recs])
        p = sum([float(x.get('amount_paid', 0)) for x in recs])
        apt_analysis.append({"الشقة": apt['name'], "المطلوب": f"{d:,.2f}", "المحصل": f"{p:,.2f}", "المتبقي": f"{d-p:,.2f}", "الحالة": "✅" if d-p <= 0 else "⏳"})
    st.table(pd.DataFrame(apt_analysis))

# ==========================================
# 2. إصدار مطالبة (الحماية من البيانات غير المكتملة)
# ==========================================
with tabs[1]:
    if not s_data: st.warning("أضف شقة أولاً من الصفحة الرئيسية")
    else:
        apt_sel = st.selectbox("🏘️ اختر الشقة المستهدفة:", [s['name'] for s in s_data], key="issue_apt")
        sel_obj = next(s for s in s_data if s['name'] == apt_sel)
        stds = [st for st in t_data if st['sakan_id'] == sel_obj['id']]
        
        st.info(f"👥 عدد الطالبات في {apt_sel}: {len(stds)}")

        with st.form("billing_form"):
            c1, c2, c3 = st.columns(3)
            b_type = c1.selectbox("نوع المطالبة", ["إيجار", "كهرباء", "صيانة", "إنترنت", "أخرى"])
            b_val = c2.number_input("المبلغ الإجمالي (د.أ)", min_value=0.0)
            b_mo = c3.selectbox("شهر الاستحقاق", [f"{m:02d}-2026" for m in range(1, 13)], index=datetime.date.today().month-1)
            
            b_due_date = st.date_input("تاريخ استحقاق الدفع")
            b_notes = st.text_area("وصف تفصيلي للفاتورة (يظهر في السجل)")
            is_owner = st.checkbox("🚩 مصروف على المالك (لا يوزع على الطالبات)")
            
            shares = {}
            if not is_owner and stds:
                st.write("⚖️ التوزيع التلقائي للمبالغ:")
                def_v = round(b_val / len(stds), 2) if b_val > 0 else 0.0
                sc1, sc2 = st.columns(2)
                for i, std in enumerate(stds):
                    with (sc1 if i % 2 == 0 else sc2):
                        shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_v, key=f"std_v_{std['id']}")
            
            if st.form_submit_button("إصدار وتوثيق العملية ✅"):
                try:
                    final_n = f"{b_notes} | {'(مالك)' if is_owner else '(طالبات)'}"
                    res = supabase.table("electricity_bills").insert({
                        "sakan_id": sel_obj['id'], "total_amount": b_val, "bill_type": b_type, 
                        "bill_month": b_mo, "due_date": str(b_due_date), "notes": final_n
                    }).execute()
                    
                    if not is_owner and shares:
                        b_id = res.data[0]['id']
                        recs = [{"student_id": sid, "bill_id": b_id, "type": b_type, "amount_due": amt, "bill_month": b_mo, "due_date": str(b_due_date)} for sid, amt in shares.items()]
                        supabase.table("student_ledger").insert(recs).execute()
                    
                    log_action("إصدار فاتورة", f"أصدر {st.session_state['user_name']} {b_type} لشقة {apt_sel} بمبلغ {b_val:,.2f}")
                    st.success("تم التثبيت بنجاح!")
                    st.rerun()
                except Exception as e: st.error(f"خطأ: {e}")

# ==========================================
# 3. إدارة الفواتير (نظام الدفاع الرباعي ضد البيانات اليتيمة)
# ==========================================
with tabs[2]:
    active = [b for b in b_data if not b.get('is_archived')]
    if not active: st.info("لا يوجد فواتير نشطة حالياً.")
    for bill in active:
        is_owner = "(مالك)" in (bill.get('notes') or "")
        st.markdown(f"""
            <div class="bill-card {'owner-card' if is_owner else ''}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b>{bill.get('bill_type')} - {bill.get('sakanat', {}).get('name')}</b>
                    <span class="money">{bill['total_amount']:,.2f} د.أ</span>
                </div>
                <div style="margin-top:8px;">
                    <span class="date-tag">🗓️ شهر: {bill.get('bill_month')}</span>
                    <span class="date-tag">⌛ استحقاق: {bill.get('due_date')}</span>
                </div>
                <div style="font-size:13px; color:#666; margin-top:8px;">📝 {bill.get('notes')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        ca1, ca2, ca3, _ = st.columns([1.5, 1, 1, 2.5])
        
        # --- الحذف الذكي والمحمي (Smart & Defensive Delete) ---
        with ca1.popover("🗑️ حذف وإدارة", use_container_width=True):
            st.warning("⚠️ هل أنت متأكد؟")
            ledger_items = [l for l in l_data if l.get('bill_id') == bill['id']]
            if ledger_items:
                st.error(f"هذه الفاتورة مربوطة بـ ({len(ledger_items)}) ذمة طالبة.")
                st.info("سيقوم النظام بحذف الذمم التابعة لها لضمان نظافة البيانات.")
            
            if st.button("تأكيد الحذف النهائي 🔥", key=f"force_del_{bill['id']}", type="primary", use_container_width=True):
                # برمجياً: نقوم بمسح الذمم يدوياً أولاً كطبقة حماية إضافية
                supabase.table("student_ledger").delete().eq("bill_id", bill['id']).execute()
                # ثم نحذف الفاتورة الأب
                supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
                log_action("حذف شامل", f"حذف فاتورة {bill.get('bill_type')} وجميع ذممها بواسطة {st.session_state['user_name']}")
                st.rerun()

        if ca2.button("📦 أرشفة", key=f"arc_{bill['id']}", use_container_width=True):
            supabase.table("electricity_bills").update({"is_archived": True}).eq("id", bill['id']).execute()
            log_action("أرشفة", f"أرشفة فاتورة {bill.get('bill_type')}")
            st.rerun()
            
        if ca3.button("👁️ تفاصيل", key=f"det_{bill['id']}", use_container_width=True):
            rel = [l for l in l_data if l.get('bill_id') == bill['id']]
            if rel:
                for r in rel: st.caption(f"👤 {r['students']['name']}: {float(r['amount_due']):,.2f} د.أ ({r['status']})")
            else: st.caption("هذا المصروف مسجل على المالك.")

# ==========================================
# 4. تحصيل الذمم (حماية الأرقام + توثيق الأثر المالي)
# ==========================================
with tabs[3]:
    st.subheader("💰 تحصيل المبالغ من الطالبات")
    f_apt = st.selectbox("🔍 فلترة الشقة:", ["الكل"] + [s['name'] for s in s_data])
    
    pending = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
    if f_apt != "الكل":
        sid = next(s['id'] for s in s_data if s['name'] == f_apt)
        pending = [l for l in pending if l['students']['sakan_id'] == sid]

    if not pending: st.success("لا توجد مبالغ معلقة لهذه الشقة! 🎉")
    for p in pending:
        with st.container(border=True):
            cp1, cp2, cp3 = st.columns([2, 1, 1])
            full_desc = f"{p['type']} - شهر {p.get('bill_month')}"
            cp1.markdown(f"👤 **{p['students']['name']}**<br><small>{full_desc} | استحقاق: {p.get('due_date')}</small>", unsafe_allow_html=True)
            rem = float(p['amount_due']) - float(p['amount_paid'])
            cp2.markdown(f"<br><span class='money'>{rem:,.2f} د.أ</span>", unsafe_allow_html=True)
            
            if cp3.button("تم التحصيل ✅", key=f"pay_led_{p['id']}", use_container_width=True):
                # تسجيل الدفعة مع تجميد الوصف (للحماية من "البيانات اليتيمة" مستقبلاً)
                fixed_desc = f"تحصيل {p['type']} شهر {p.get('bill_month')} من {p['students']['name']}"
                supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": st.session_state['user_name'], "notes": fixed_desc}).execute()
                log_action("تحصيل مالي", fixed_desc)
                st.rerun()

# ==========================================
# 5. السجلات والتحقيق المالي (Audit & Finance Journal)
# ==========================================
with tabs[4]:
    st.subheader("📜 سجل الحركات التاريخية المحصن")
    sub1, sub2, sub3 = st.tabs(["💵 سجل المقبوضات (الخزنة)", "📂 الأرشيف", "🛠️ سجل النظام الكامل"])
    
    with sub1:
        st.write("### 💰 كشف حساب المقبوضات (غير قابل للتلاعب)")
        if not p_data: st.info("لا توجد دفعات مسجلة حالياً.")
        for pay in p_data:
            dt = pd.to_datetime(pay['payment_date']).strftime('%Y-%m-%d | %H:%M')
            # حماية: لو انحذفت الفاتورة والليدجر، نعتمد على الوصف المجمد (notes)
            info = pay.get('notes') or f"دفعة من {pay.get('student_ledger', {}).get('students', {}).get('name', 'طالبة')}"
            st.markdown(f"""
                <div style="background:#f9fffb; border-right:5px solid #10ac84; padding:12px; border-radius:8px; margin-bottom:8px; font-size:14px;">
                    📅 <b>{dt}</b> | المسؤول: <span style='color:#2e86de;'>{pay['recorded_by']}</span> <br>
                    تم استلام مبلغ <span class='money' style='color:#10ac84; font-size:1.1em;'>{pay['amount_paid']:,.2f} د.أ</span> | {info}
                </div>
            """, unsafe_allow_html=True)

    with sub2:
        st.write("### 📂 الفواتير والمصاريف المؤرشفة")
        archived = [b for b in b_data if b.get('is_archived')]
        for ab in archived:
            st.markdown(f"<div class='bill-card' style='border-right-color:#95a5a6; opacity:0.8;'><b>{ab['bill_type']} - {ab.get('sakanat',{}).get('name')}</b> | {ab['total_amount']:,.2f} د.أ</div>", unsafe_allow_html=True)
            if st.button("↩️ استعادة للنشط", key=f"unarc_{ab['id']}", use_container_width=True):
                supabase.table("electricity_bills").update({"is_archived": False}).eq("id", ab['id']).execute()
                st.rerun()

    with sub3:
        st.write("### 🛠️ تتبع حركات المستخدمين (Audit Trail)")
        logs = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(100).execute().data
        if logs:
            for g in logs:
                g_dt = pd.to_datetime(g['created_at']).strftime('%H:%M | %Y-%m-%d')
                st.markdown(f"🕒 `{g_dt}` | 👤 **{g.get('user_name', 'النظام')}** | **{g['action']}**: {g['details']}")
        else: st.info("السجل فارغ.")