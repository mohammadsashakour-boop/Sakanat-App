import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات والأمان ---
VERSION = "2.0 Enterprise Strict"
ADMIN_PWD = "Shakur2026!"
SUPER_PWD = "ShakurMaster!"

st.set_page_config(
    page_title="النظام المالي  v2.0",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"⚠️ يرجى ضبط Secrets: {e}")
    st.stop()

# --- CSS لإبادة الشاشة الجانبية بالكامل على الهاتف ---
st.markdown("""
<style>
@media (max-width: 768px) {

    html, body {
        overflow-x: hidden !important;
    }

    .stApp {
        padding: 0 !important;
        margin: 0 !important;
    }

    div.block-container {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }

    /* منع التبويبات من التكسير */
    div[data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
    }

    /* إصلاح الجداول */
    .stDataFrame {
        font-size: 12px !important;
    }

}
</style>
""", unsafe_allow_html=True)


def log_action(action, details):
    try: supabase.table("audit_logs").insert({"action": action, "details": details}).execute()
    except: pass

# --- 2. الدخول ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 النظام المالي (وصول مقيد)</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        pwd_in = st.text_input("كلمة المرور", type="password")
        if st.button("دخول", use_container_width=True) or (pwd_in == ADMIN_PWD and pwd_in != ""):
            if pwd_in == ADMIN_PWD:
                st.session_state["logged_in"] = True
                log_action("دخول", "تسجيل دخول للنظام المالي")
                st.rerun()
            else: st.error("❌ وصول مرفوض")
    st.stop()

# --- 3. محرك البيانات ---
@st.cache_data(ttl=60)
def get_static_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    return s.data, t.data

def get_live_data():
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*").order('payment_date', desc=True).execute()
    return b.data, l.data, p.data

s_data, t_data = get_static_data()
b_data, l_data, p_data = get_live_data()

st.title("💰 الإدارة المالية والتدقيق")
tabs = st.tabs(["📊 التحليلات والتقارير", "⚡ إصدار الفواتير", "📅 إدارة الفواتير", "👤 الدفع (Ledger)"])

# ==========================================
# 1. التحليلات
# ==========================================
with tabs[0]:
    c_f1, c_f2 = st.columns(2)
    start_d = c_f1.date_input("من تاريخ", datetime.date(2026, 1, 1))
    end_d = c_f2.date_input("إلى تاريخ", datetime.date.today())
    
    filtered_l = [l for l in l_data if start_d <= pd.to_datetime(l['due_date']).date() <= end_d]
    total_due = sum([float(l.get('amount_due', 0)) for l in filtered_l])
    total_paid = sum([float(l.get('amount_paid', 0)) for l in filtered_l])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المطلوب (للفترة)", f"{total_due:,.2f} د.أ")
    c2.metric("المُحصّل (للفترة)", f"{total_paid:,.2f} د.أ")
    c3.metric("المتبقي للتحصيل", f"{(total_due - total_paid):,.2f} د.أ")

    st.subheader("🏢 تقرير الذمم حسب الشقة")
    apt_report = []
    for apt in s_data:
        apt_stds = [s['id'] for s in t_data if s['sakan_id'] == apt['id']]
        apt_ledger = [l for l in filtered_l if l['student_id'] in apt_stds]
        a_due = sum([float(l.get('amount_due', 0)) for l in apt_ledger])
        a_paid = sum([float(l.get('amount_paid', 0)) for l in apt_ledger])
        apt_report.append({"الشقة": apt['name'], "المطلوب": a_due, "المُحصل": a_paid, "الديون": a_due - a_paid})
    st.dataframe(pd.DataFrame(apt_report), use_container_width=True)

# ==========================================
# 2. إصدار الفواتير 
# ==========================================
with tabs[1]:
    apt_sel = st.selectbox("🏘️ الشقة المستهدفة:", [s['name'] for s in s_data], key="new_bill_apt")
    target_s = next(s for s in s_data if s['name'] == apt_sel)
    stds_in = [s for s in t_data if s.get('sakan_id') == target_s['id']]
    
    if stds_in:
        with st.form("new_bill_form"):
            col_b1, col_b2, col_b3 = st.columns(3)
            total_v = col_b1.number_input("قيمة الفاتورة (دينار)", min_value=0.0, step=1.0)
            month_v = col_b2.selectbox("شهر مالي:", [f"2026-{m:02d}" for m in range(1, 13)])
            due_v = col_b3.date_input("تاريخ الاستحقاق", datetime.date.today())
            bill_file = st.file_uploader("صورة الفاتورة", type=['jpg', 'png', 'pdf'])
            
            st.markdown("---")
            st.write("⚖️ **توزيع الحصص:**")
            def_share = round(total_v / len(stds_in), 2) if total_v > 0 else 0.0
            
            shares = {}
            c_s1, c_s2 = st.columns(2)
            for i, std in enumerate(stds_in):
                with (c_s1 if i % 2 == 0 else c_s2):
                    shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_share, key=f"n_shr_{std['id']}", step=0.5)
            
            total_dist = sum(shares.values())
            st.write(f"الموزع: **{total_dist:,.2f}** | الفاتورة: **{total_v:,.2f}**")
            
            if st.form_submit_button("إصدار الفاتورة ✅"):
                if abs(total_dist - total_v) > 0.01:
                    st.error("⚠️ إجمالي الحصص لا يطابق قيمة الفاتورة!")
                elif any(b['sakan_id'] == target_s['id'] and b['bill_month'] == month_v for b in b_data):
                    st.error("⚠️ توجد فاتورة لهذه الشقة في نفس الشهر المالي!")
                else:
                    try:
                        f_path = None
                        if bill_file:
                            f_path = f"bill_{target_s['id']}_{month_v}_{uuid.uuid4().hex[:8]}.{bill_file.name.split('.')[-1]}"
                            supabase.storage.from_("student_files").upload(f_path, bill_file.read())
                        
                        # --- صائد الأخطاء الحقيقي ---
                        bill_res = supabase.table("electricity_bills").insert({
                            "sakan_id": target_s['id'], "total_amount": total_v, "bill_month": month_v, "file_path": f_path
                        }).execute()
                        bill_id = bill_res.data[0]['id']
                        
                        l_entries = [{"student_id": sid, "bill_id": bill_id, "type": "كهرباء", "amount_due": amt, "bill_month": month_v, "due_date": str(due_v), "status": "pending"} for sid, amt in shares.items()]
                        supabase.table("student_ledger").insert(l_entries).execute()
                        
                        log_action("إصدار فاتورة", f"شقة {apt_sel} - شهر {month_v}")
                        st.success("تم الإصدار بنجاح!")
                        st.rerun()
                    except Exception as db_err:
                        st.error(f"🛑 تم إيقاف الكراش! تفاصيل خطأ الداتا بيس: {db_err}")

# ==========================================
# 3. إدارة الفواتير
# ==========================================
with tabs[2]:
    st.subheader("📅 الفواتير المصدرة")
    for bill in b_data:
        with st.expander(f"فاتورة {bill['bill_month']} | {bill.get('sakanat',{}).get('name')} | {bill['total_amount']} د.أ"):
            if bill['file_path']:
                st.link_button("👁️ عرض الفاتورة", supabase.storage.from_("student_files").get_public_url(bill['file_path']))
            
            bill_ledger = [l for l in l_data if l['bill_id'] == bill['id']]
            with st.form(f"edit_bill_{bill['id']}"):
                new_tot = st.number_input("قيمة الفاتورة الكلية", value=float(bill['total_amount']), min_value=0.0)
                new_shares = {}
                for bl in bill_ledger:
                    paid_amt = float(bl.get('amount_paid', 0))
                    disabled = paid_amt > 0
                    std_name = bl.get('students', {}).get('name', 'N/A')
                    new_shares[bl['id']] = st.number_input(f"حصة {std_name} (دُفع: {paid_amt})", value=float(bl['amount_due']), disabled=disabled)
                
                sum_new_shares = sum(new_shares.values())
                st.caption(f"مجموع الحصص المعدلة: {sum_new_shares:,.2f}")
                
                if st.form_submit_button("حفظ التعديلات 💾"):
                    if abs(sum_new_shares - new_tot) > 0.01:
                        st.error("المجموع لا يطابق!")
                    else:
                        try:
                            supabase.table("electricity_bills").update({"total_amount": new_tot}).eq("id", bill['id']).execute()
                            for bl_id, n_amt in new_shares.items():
                                supabase.table("student_ledger").update({"amount_due": n_amt}).eq("id", bl_id).execute()
                            log_action("تعديل فاتورة", f"تعديل فاتورة {bill['id']}")
                            st.success("تم التعديل!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")

            st.markdown("---")
            del_c1, del_c2 = st.columns(2)
            check_del = del_c1.checkbox("أقر برغبتي بحذف الفاتورة", key=f"chk_{bill['id']}")
            if check_del:
                if del_c2.button("🗑️ حذف نهائي", key=f"del_{bill['id']}", type="primary"):
                    pwd_verify = st.text_input("أدخل كلمة المرور:", type="password", key=f"pwd_{bill['id']}")
                    if pwd_verify == SUPER_PWD or pwd_verify == ADMIN_PWD:
                        try:
                            supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
                            log_action("حذف فاتورة", f"رقم {bill['id']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ في الحذف: {e}")

# ==========================================
# 4. التحصيل والدفعات
# ==========================================
with tabs[3]:
    f_c1, f_c2 = st.columns(2)
    s_fin = f_c1.selectbox("بحث عن طالبة:", ["الكل"] + [s['name'] for s in t_data])
    
    view_l = l_data
    if s_fin != "الكل": view_l = [l for l in view_l if l.get('students') and l['students']['name'] == s_fin]
    today = datetime.date.today()
    
    for entry in view_l:
        due_d = pd.to_datetime(entry['due_date']).date()
        amt_due = float(entry.get('amount_due', 0))
        amt_paid = float(entry.get('amount_paid', 0))
        rem = round(amt_due - amt_paid, 2)
        sts = entry['status']
        
        is_overdue = due_d < today and sts != 'paid'
        box_class = "overdue" if is_overdue else ""
        c_class = "paid" if sts == 'paid' else "partial" if sts == 'partial' else "pending"
        
        with st.container():
            st.markdown(f"""
                <div class="{box_class}" style="background:white; padding:15px; border-radius:10px; border-right:5px solid {'#E74C3C' if is_overdue else '#3498DB'}; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <b>👤 {entry['students']['name'] if entry['students'] else 'مجهول'}</b>
                        <span class="{c_class}">{sts.upper()}</span>
                    </div>
                    <p style="margin:5px 0 0 0; font-size:14px;">البند: {entry['type']} | استحقاق: {due_d} {'(متأخر ⚠️)' if is_overdue else ''}<br>
                    المطلوب: {amt_due} | المدفوع: {amt_paid} | <b>المتبقي: {rem}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            act_c1, act_c2, act_c3 = st.columns([1,1,1])
            
            with act_c1.popover("💸 دفع"):
                if rem > 0:
                    p_amt = st.number_input("المبلغ", min_value=0.01, max_value=float(rem), value=float(rem), step=1.0, key=f"pin_{entry['id']}")
                    if st.button("سداد", key=f"pbtn_{entry['id']}"):
                        try:
                            new_paid = min(amt_paid + p_amt, amt_due)
                            new_sts = "paid" if new_paid >= amt_due else "partial"
                            supabase.table("student_ledger").update({"amount_paid": new_paid, "status": new_sts}).eq("id", entry['id']).execute()
                            supabase.table("payments").insert({"ledger_id": entry['id'], "amount_paid": p_amt, "recorded_by": "Admin"}).execute()
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")
                else: st.success("مسدد.")
            
            with act_c2.popover("📜 السجل"):
                entry_payments = [p for p in p_data if p['ledger_id'] == entry['id']]
                if entry_payments:
                    for p in entry_payments:
                        st.caption(f"دُفع {p['amount_paid']} د.أ ({pd.to_datetime(p['payment_date']).strftime('%m-%d %H:%M')})")
                        if st.button("🗑️ إلغاء", key=f"undo_p_{p['id']}"):
                            try:
                                revert_paid = max(amt_paid - float(p['amount_paid']), 0)
                                revert_sts = "paid" if revert_paid >= amt_due else "partial" if revert_paid > 0 else "pending"
                                supabase.table("student_ledger").update({"amount_paid": revert_paid, "status": revert_sts}).eq("id", entry['id']).execute()
                                supabase.table("payments").delete().eq("id", p['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ: {e}")
                else: st.info("لا حركات.")

            if rem > 0 and entry.get('students'):
                msg = f"مرحباً {entry['students']['name']}، تذكير بقسط ({entry['type']}) بقيمة {rem} د.أ المستحق بتاريخ {due_d}."
                wa_url = f"https://wa.me/962{str(entry['students']['phone'])[1:]}?text={urllib.parse.quote(msg)}"
                act_c3.link_button("📱 تذكير", wa_url)