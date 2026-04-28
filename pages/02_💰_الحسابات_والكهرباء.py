import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# ==========================================
# 1. الإعدادات ونظام الصلاحيات (Roles)
# ==========================================
VERSION = "3.0 SaaS Edition"
# نظام تعدد المستخدمين (Multi-user System)
ROLES = {
    "ShakurMaster!": "SuperAdmin", # يحق له الحذف النهائي
    "Shakur2026!": "Admin",        # يحق له الإضافة والتعديل
    "ShakurView": "Viewer"         # للقراءة والتقارير فقط
}

st.set_page_config(page_title="النظام المالي | v3.0", layout="wide")

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ يرجى التحقق من إعدادات Secrets")
    st.stop()

# ==========================================
# 2. التصميم (عودة الشاشة الجانبية الأصلية)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .metric-box { background: #f8f9fa; padding: 20px; border-radius: 10px; border-top: 4px solid #2980B9; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .status-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; }
    .bg-paid { background: #E9F7EF; color: #27AE60; border: 1px solid #27AE60; }
    .bg-partial { background: #FEF5E7; color: #F39C12; border: 1px solid #F39C12; }
    .bg-pending { background: #FDEDEC; color: #E74C3C; border: 1px solid #E74C3C; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try: supabase.table("audit_logs").insert({"action": action, "details": f"[{st.session_state.get('role', 'System')}] {details}"}).execute()
    except: pass

# ==========================================
# 3. شاشة الدخول الموجهة بالصلاحيات
# ==========================================
if "role" not in st.session_state:
    st.session_state["role"] = None

if not st.session_state["role"]:
    st.markdown("<h2 style='text-align: center;'>🔐 بوابة الدخول المالية</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        pwd_in = st.text_input("رمز الوصول", type="password")
        if st.button("تسجيل الدخول", use_container_width=True) or pwd_in != "":
            if pwd_in in ROLES:
                st.session_state["role"] = ROLES[pwd_in]
                log_action("تسجيل دخول", f"دخول بصلاحية {ROLES[pwd_in]}")
                st.rerun()
            elif pwd_in != "": st.error("❌ الرمز غير صحيح")
    st.stop()

# ==========================================
# 4. محرك البيانات الدقيق
# ==========================================
def get_data():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = get_data()

st.title(f"💰 النظام المالي ({st.session_state['role']})")
tabs = st.tabs(["📊 التحليلات والرسوم", "⚡ إصدار وتعديل", "👤 التحصيل والدفعات", "📜 سجل النظام"])

# ==========================================
# TAB 1: التحليلات والرسوم (Charts)
# ==========================================
with tabs[0]:
    total_due = sum([float(l.get('amount_due', 0)) for l in l_data])
    total_paid = sum([float(l.get('amount_paid', 0)) for l in l_data])
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'>المطلوب الكلي<br><h2>{total_due:,.2f} د.أ</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'>المحصل الكلي<br><h2 style='color:#27AE60;'>{total_paid:,.2f} د.أ</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'>المتبقي بالسوق<br><h2 style='color:#E74C3C;'>{(total_due - total_paid):,.2f} د.أ</h2></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📈 الأداء المالي لكل شقة")
    # تجهيز بيانات الرسم البياني
    chart_data = []
    for apt in s_data:
        apt_stds = [s['id'] for s in t_data if s['sakan_id'] == apt['id']]
        a_due = sum([float(l.get('amount_due', 0)) for l in l_data if l['student_id'] in apt_stds])
        a_paid = sum([float(l.get('amount_paid', 0)) for l in l_data if l['student_id'] in apt_stds])
        if a_due > 0: chart_data.append({"الشقة": apt['name'], "المطلوب": a_due, "المحصل": a_paid})
    
    if chart_data:
        df_chart = pd.DataFrame(chart_data).set_index("الشقة")
        st.bar_chart(df_chart, color=["#E74C3C", "#27AE60"])

# ==========================================
# TAB 2: إصدار وتعديل الفواتير
# ==========================================
with tabs[1]:
    if st.session_state["role"] == "Viewer":
        st.warning("صلاحية القراءة فقط. لا يمكنك إصدار فواتير.")
    else:
        with st.expander("➕ إصدار فاتورة جديدة", expanded=False):
            apt_sel = st.selectbox("الشقة:", [s['name'] for s in s_data])
            target_s = next(s for s in s_data if s['name'] == apt_sel)
            stds_in = [s for s in t_data if s.get('sakan_id') == target_s['id']]
            
            if stds_in:
                with st.form("new_bill_form"):
                    c_f1, c_f2 = st.columns(2)
                    total_v = c_f1.number_input("إجمالي الفاتورة", min_value=0.0)
                    month_v = c_f2.selectbox("الشهر", [f"2026-{m:02d}" for m in range(1,13)])
                    
                    st.write("⚖️ توزيع الحصص:")
                    def_share = round(total_v / len(stds_in), 2) if total_v > 0 else 0.0
                    shares = {std['id']: st.number_input(f"{std['name']}", value=def_share, key=f"s_{std['id']}", step=0.5) for std in stds_in}
                    
                    if st.form_submit_button("إصدار الفاتورة"):
                        if abs(sum(shares.values()) - total_v) > 0.01: st.error("❌ المجموع لا يطابق!")
                        else:
                            bill_res = supabase.table("electricity_bills").insert({"sakan_id": target_s['id'], "total_amount": total_v, "bill_month": month_v}).execute()
                            bill_id = bill_res.data[0]['id']
                            l_entries = [{"student_id": sid, "bill_id": bill_id, "type": "كهرباء", "amount_due": amt, "bill_month": month_v} for sid, amt in shares.items()]
                            supabase.table("student_ledger").insert(l_entries).execute()
                            log_action("إصدار فاتورة", f"فاتورة لـ {apt_sel} بـ {total_v}")
                            st.rerun()

        st.subheader("📅 الفواتير المصدرة")
        for b in b_data:
            with st.expander(f"{b['bill_month']} - {b.get('sakanat',{}).get('name')} | {b['total_amount']} د.أ"):
                b_ledger = [l for l in l_data if l['bill_id'] == b['id']]
                
                # تعديل الفاتورة مع التوزيع التلقائي (Smart Edit)
                with st.form(f"edit_{b['id']}"):
                    new_tot = st.number_input("تعديل الإجمالي", value=float(b['total_amount']))
                    new_shares = {}
                    for bl in b_ledger:
                        paid_amt = float(bl.get('amount_paid', 0))
                        # لا نسمح بالتعديل إذا تم الدفع لتجنب تضارب البيانات
                        new_shares[bl['id']] = st.number_input(f"{bl.get('students',{}).get('name', 'N/A')} (مدفوع: {paid_amt})", value=float(bl['amount_due']), disabled=(paid_amt > 0))
                    
                    if st.form_submit_button("تحديث الفاتورة والحصص 💾"):
                        if abs(sum(new_shares.values()) - new_tot) > 0.01: st.error("❌ الحصص لا تطابق الإجمالي الجديد.")
                        else:
                            supabase.table("electricity_bills").update({"total_amount": new_tot}).eq("id", b['id']).execute()
                            for bl_id, n_amt in new_shares.items():
                                supabase.table("student_ledger").update({"amount_due": n_amt}).eq("id", bl_id).execute()
                            st.success("تم التحديث")
                            st.rerun()

                # الحذف الصارم (Cascade) للمدير الأعلى فقط
                if st.session_state["role"] == "SuperAdmin":
                    if st.button("🗑️ حذف الفاتورة نهائياً", key=f"del_{b['id']}", type="primary"):
                        supabase.table("electricity_bills").delete().eq("id", b['id']).execute()
                        log_action("حذف فاتورة", f"تم حذف الفاتورة رقم {b['id']}")
                        st.rerun()

# ==========================================
# TAB 3: التحصيل وإدارة الدفعات (Undo Fixed)
# ==========================================
with tabs[2]:
    search_std = st.selectbox("تصفية حسب الطالبة:", ["الكل"] + [s['name'] for s in t_data])
    view_l = [l for l in l_data if l.get('students') and l['students']['name'] == search_std] if search_std != "الكل" else l_data
    
    for l in view_l:
        amt_due = float(l.get('amount_due', 0))
        amt_paid = float(l.get('amount_paid', 0))
        rem = round(amt_due - amt_paid, 2)
        sts = l.get('status', 'pending')
        badge = f"<span class='status-badge bg-{sts}'>{sts.upper()}</span>"
        
        with st.container(border=True):
            st.markdown(f"<b>{l.get('students',{}).get('name', 'N/A')}</b> | {l['type']} ({l['bill_month']}) {badge}", unsafe_allow_html=True)
            st.write(f"المطلوب: {amt_due} | المدفوع: {amt_paid} | **المتبقي: {rem}**")
            
            if st.session_state["role"] != "Viewer":
                c_p1, c_p2, c_p3 = st.columns(3)
                
                # 1. تسجيل دفعة
                with c_p1.popover("💸 دفع"):
                    if rem > 0:
                        p_amt = st.number_input("المبلغ", min_value=0.01, max_value=rem, value=rem, key=f"p_{l['id']}")
                        if st.button("سداد"):
                            new_paid = min(amt_paid + p_amt, amt_due)
                            new_sts = "paid" if new_paid >= amt_due else "partial"
                            supabase.table("student_ledger").update({"amount_paid": new_paid, "status": new_sts}).eq("id", l['id']).execute()
                            supabase.table("payments").insert({"ledger_id": l['id'], "amount_paid": p_amt, "recorded_by": st.session_state["role"]}).execute()
                            st.rerun()
                
                # 2. سجل الدفعات (Undo Logic Fix)
                with c_p2.popover("📜 سجل الدفعات"):
                    entry_p = [p for p in p_data if p['ledger_id'] == l['id']]
                    for p in entry_p:
                        st.write(f"💰 {p['amount_paid']} د.أ ({pd.to_datetime(p['payment_date']).strftime('%Y-%m-%d')})")
                        if st.button("إلغاء الدفعة ↩️", key=f"undo_{p['id']}"):
                            # نسترجع القيمة المحدثة لليدجر لضمان دقة العمليات الحسابية
                            live_ledger = supabase.table("student_ledger").select("amount_due, amount_paid").eq("id", l['id']).single().execute().data
                            revert_paid = max(float(live_ledger['amount_paid']) - float(p['amount_paid']), 0)
                            revert_sts = "paid" if revert_paid >= float(live_ledger['amount_due']) else "partial" if revert_paid > 0 else "pending"
                            
                            supabase.table("student_ledger").update({"amount_paid": revert_paid, "status": revert_sts}).eq("id", l['id']).execute()
                            supabase.table("payments").delete().eq("id", p['id']).execute()
                            log_action("إلغاء دفعة", f"إلغاء {p['amount_paid']} للطالبة {l.get('students',{}).get('name')}")
                            st.rerun()
                
                # 3. واتساب
                if rem > 0 and l.get('students'):
                    msg = urllib.parse.quote(f"تذكير بخصوص ذمة ({l['type']}) بقيمة {rem} د.أ.")
                    c_p3.link_button("📱 واتساب", f"https://wa.me/962{str(l['students']['phone'])[1:]}?text={msg}")

# ==========================================
# TAB 4: سجل النظام 
# ==========================================
with tabs[3]:
    a_data = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(50).execute().data
    if a_data:
        df_a = pd.DataFrame(a_data)[['created_at', 'action', 'details']]
        df_a['created_at'] = pd.to_datetime(df_a['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df_a, use_container_width=True)

if st.button("تسجيل الخروج"):
    st.session_state["role"] = None
    st.rerun()