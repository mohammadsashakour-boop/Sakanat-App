import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات ---
VERSION = "2.2 Pro Management"
ADMIN_PWD = "Shakur2026!"
SUPER_PWD = "Shakur2026!"

st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بالخادم")
    st.stop()

# --- 2. التحسين البصري (Layout & Pro UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    
    /* إخفاء القائمة الجانبية تماماً وتنسيق الهيدر */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; height: 0 !important; }
    
    /* تنسيق التبويبات لتكون مريحة للنظر وغير متمركزة بشكل عشوائي */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: flex-start; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f1f3f6; border-radius: 8px 8px 0 0; 
        padding: 10px 20px; font-weight: bold; 
    }
    .stTabs [aria-selected="true"] { background-color: #2e86de !important; color: white !important; }

    /* نظام البطاقات الاحترافي بدل الـ Expander */
    .bill-card {
        background: #ffffff; border: 1px solid #e0e6ed; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border-right: 6px solid #2e86de;
    }
    .owner-bill { border-right: 6px solid #10ac84; background: #f0fdf4; }
    
    /* إصلاح الموبايل */
    @media (max-width: 768px) { .stApp { margin-top: -50px; } }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try: supabase.table("audit_logs").insert({"action": action, "details": details}).execute()
    except: pass

# --- 3. محرك البيانات ---
def fetch_all():
    s = supabase.table("sakanat").select("*").order('name').execute()
    t = supabase.table("students").select("*, sakanat(name)").eq("is_deleted", False).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = fetch_all()

# --- 4. واجهة المستخدم ---
st.title("💼 الإدارة المالية الاحترافية")

tabs = st.tabs(["📊 الملخص", "➕ إصدار فاتورة", "📅 إدارة العمليات", "👤 التحصيل المالي", "📜 سجل التاريخ (History)"])

# ==========================================
# التبويب 1: الملخص المالي
# ==========================================
with tabs[0]:
    total_due = sum([float(l.get('amount_due', 0)) for l in l_data])
    total_paid = sum([float(l.get('amount_paid', 0)) for l in l_data])
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الديون القائمة", f"{total_due - total_paid:,.2f} د.أ")
    c2.metric("المحصل الفعلي", f"{total_paid:,.2f} د.أ")
    c3.metric("عدد الفواتير النشطة", len(b_data))

# ==========================================
# التبويب 2: إصدار فاتورة (مع خيار المالك)
# ==========================================
with tabs[1]:
    if not s_data:
        st.info("يرجى إضافة شقة من الصفحة الرئيسية أولاً")
    else:
        with st.form("pro_bill_form"):
            col1, col2 = st.columns(2)
            apt_name = col1.selectbox("اختر الشقة", [s['name'] for s in s_data])
            b_type = col2.selectbox("نوع المصروف", ["كهرباء", "إيجار", "صيانة عامة", "إنترنت", "تصليحات"])
            
            total_amt = st.number_input("المبلغ الإجمالي (دينار)", min_value=0.0)
            
            # --- ميزة المالك (التي طلبتها) ---
            is_owner = st.checkbox("🚩 المصروف على المالك (لا يتم تحميله للطالبات)")
            
            col3, col4 = st.columns(2)
            b_month = col3.selectbox("الشهر المالي", [f"2026-{m:02d}" for m in range(1, 13)])
            due_d = col4.date_input("تاريخ الاستحقاق")
            
            st.markdown("---")
            target_apt = next(s for s in s_data if s['name'] == apt_name)
            apt_students = [std for std in t_data if std['sakan_id'] == target_apt['id']]
            
            shares = {}
            if not is_owner and apt_students:
                st.write("⚖️ توزيع الحصص على الطالبات:")
                def_s = round(total_amt / len(apt_students), 2) if total_amt > 0 else 0.0
                c_s1, c_s2 = st.columns(2)
                for i, std in enumerate(apt_students):
                    with (c_s1 if i % 2 == 0 else c_s2):
                        shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_s, key=f"s_{std['id']}")
            
            if st.form_submit_button("تثبيت العملية ✅"):
                try:
                    # تسجيل الفاتورة الأساسية
                    bill_res = supabase.table("electricity_bills").insert({
                        "sakan_id": target_apt['id'], "total_amount": total_amt, 
                        "bill_month": b_month, "bill_type": b_type,
                        "notes": "بذمة المالك" if is_owner else "بذمة الطالبات"
                    }).execute()
                    
                    # إذا لم تكن على المالك، نوزع على الطالبات
                    if not is_owner and shares:
                        bill_id = bill_res.data[0]['id']
                        l_entries = [{
                            "student_id": sid, "bill_id": bill_id, "type": b_type,
                            "amount_due": amt, "bill_month": b_month, "due_date": str(due_d)
                        } for sid, amt in shares.items()]
                        supabase.table("student_ledger").insert(l_entries).execute()
                    
                    log_action("إصدار فاتورة", f"{b_type} لـ {apt_name} - {'مالك' if is_owner else 'طالبات'}")
                    st.success("تم الحفظ بنجاح")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ: {e}")


# ==========================================
# التبويب 3: إدارة العمليات (النسخة المحسنة v2.3)
# ==========================================
with tabs[2]:
    st.subheader("🗓️ سجل العمليات المالية")
    
    if not b_data:
        st.info("لا توجد فواتير أو عمليات مسجلة حالياً.")
    else:
        for bill in b_data:
            # 1. جلب البيانات بأمان لمنع الـ KeyError للأبد
            b_type = bill.get('bill_type', 'كهرباء')
            b_total = bill.get('total_amount', 0)
            b_month = bill.get('bill_month', 'غير محدد')
            b_notes = bill.get('notes', "")
            sakan_info = bill.get('sakanat', {})
            sakan_name = sakan_info.get('name', 'شقة غير معروفة') if sakan_info else 'شقة غير معروفة'
            
            # 2. تحديد نوع الفاتورة (مالك أم طالبات)
            is_owner_bill = "بذمة المالك" in b_notes
            card_class = "owner-bill" if is_owner_bill else ""
            status_text = "✅ مغطاة من المالك" if is_owner_bill else "⚠️ موزعة على الطالبات"
            
            # 3. تصميم البطاقة (Card UI) المحاذية لليمين
            st.markdown(f"""
                <div class="bill-card {card_class}" style="
                    background: white; 
                    padding: 15px; 
                    border-radius: 10px; 
                    border-right: 8px solid {'#10ac84' if is_owner_bill else '#2e86de'};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    margin-bottom: 10px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1em; font-weight: bold;">{b_type} - {sakan_name}</span>
                        <span style="color: #2e86de; font-weight: bold; font-size: 1.2em;">{b_total:,.2f} د.أ</span>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #636e72;">
                        📅 الشهر المالي: {b_month} | 📌 الحالة: {status_text}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 4. أزرار التحكم (حذف ذكي + عرض)
            c_act1, c_act2, _ = st.columns([1, 1, 3])
            
            # زر الحذف الذكي (Smart Delete)
            if c_act1.button("🗑️ حذف نهائي", key=f"del_pro_{bill['id']}", type="primary", use_container_width=True):
                try:
                    # قبل الحذف: نسجل تفاصيل الفاتورة في الـ History (audit_logs)
                    history_details = f"حذف {b_type} لشقة {sakan_name} بمبلغ {b_total} لشهر {b_month}"
                    log_action("حذف وإلغاء", history_details)
                    
                    # تنفيذ الحذف (بسبب ON DELETE CASCADE سيتم حذف الذمم المرتبطة تلقائياً)
                    supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
                    
                    st.toast(f"تم حذف الفاتورة ونقلها للسجل التاريخي", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(f"فشل الحذف: {e}")
            
            if c_act2.button("👁️ تفاصيل", key=f"view_{bill['id']}", use_container_width=True):
                # عرض سريع للذمم المرتبطة بهذه الفاتورة
                relevant_ledger = [l for l in l_data if l.get('bill_id') == bill['id']]
                if relevant_ledger:
                    for entry in relevant_ledger:
                        st.caption(f"👤 {entry['students']['name']}: {entry['amount_due']} د.أ ({entry['status']})")
                else:
                    st.caption("لا توجد ذمم مرتبطة (فاتورة مالك)")
            
            st.markdown("<br>", unsafe_allow_html=True)
# ==========================================
# التبويب 4: التحصيل (جداول احترافية)
# ==========================================
with tabs[3]:
    st.subheader("💰 تحصيل الذمم القائمة")
    df_ledger = pd.DataFrame(l_data)
    if not df_ledger.empty:
        # عرض جدول مبسط للديون المتبقية فقط
        pending = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
        for p in pending:
            with st.container(border=True):
                col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                col_p1.write(f"👤 **{p['students']['name']}** - {p['type']} ({p['bill_month']})")
                rem = float(p['amount_due']) - float(p['amount_paid'])
                col_p2.write(f"المتبقي: **{rem} د.أ**")
                if col_p3.button("تسجيل دفع 💵", key=f"pay_{p['id']}"):
                    # تسجيل دفع سريع
                    supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                    supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": "Admin"}).execute()
                    st.rerun()

# ==========================================
# التبويب 5: التاريخ (History)
# ==========================================
with tabs[4]:
    st.subheader("📜 سجل الحركات التاريخية")
    # عرض سجل المراقبة (Audit Logs) بشكل مرتب
    audit_data = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(50).execute().data
    if audit_data:
        for a in audit_data:
            dt = pd.to_datetime(a['created_at']).strftime("%Y-%m-%d %H:%M")
            st.write(f"🕒 `{dt}` | **{a['action']}**: {a['details']}")
    else:
        st.write("لا يوجد سجلات حالياً.")