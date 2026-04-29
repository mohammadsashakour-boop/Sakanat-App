import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime
import urllib.parse
import uuid

# --- 1. الإعدادات والتحقق من الهوية (باسم المستخدم) ---
VERSION = "3.0 SaaS Edition"
st.set_page_config(page_title="نظام شكّور المالي Pro", layout="wide", initial_sidebar_state="collapsed")

# نظام الدخول السهل بالاسم
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

if not st.session_state["user_name"]:
    st.markdown("<h2 style='text-align: center; font-family: Cairo;'>👋 أهلاً بك في نظام شكّور</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        name_input = st.text_input("يرجى إدخال اسمك للمتابعة", placeholder="مثلاً: أحمد، محمد...")
        if st.button("دخول للنظام 🚀", use_container_width=True):
            if name_input:
                st.session_state["user_name"] = name_input
                st.rerun()
            else: st.warning("يرجى كتابة اسمك أولاً")
    st.stop()

# --- 2. الاتصال والتصميم ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
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
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .bill-card {
        background: white; padding: 20px; border-radius: 12px;
        border-right: 8px solid #2e86de; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .owner-card { border-right: 8px solid #10ac84; background: #f9fffb; }
    .user-tag { background: #eef2f7; padding: 2px 8px; border-radius: 15px; font-size: 12px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

def log_action(action, details):
    try:
        user = st.session_state.get("user_name", "Unknown")
        supabase.table("audit_logs").insert({
            "action": action, 
            "details": details,
            "user_name": user
        }).execute()
    except: pass

# --- 3. جلب البيانات ---
def fetch_data():
    # جلب الشقق
    s = supabase.table("sakanat").select("*").order('name').execute()
    # جلب الطالبات مع التأكد من عدم استثناء أي طالبة غير محذوفة
    t = supabase.table("students").select("*, sakanat(name)").neq("is_deleted", True).execute()
    b = supabase.table("electricity_bills").select("*, sakanat(name)").order('created_at', desc=True).execute()
    l = supabase.table("student_ledger").select("*, students(name, phone)").order('due_date', desc=True).execute()
    p = supabase.table("payments").select("*").order('payment_date', desc=True).execute()
    return s.data, t.data, b.data, l.data, p.data

s_data, t_data, b_data, l_data, p_data = fetch_data()

# --- 4. واجهة المستخدم ---
st.markdown(f"👤 المستخدم الحالي: **{st.session_state['user_name']}** | <a href='javascript:window.location.reload()' style='color:red; font-size:12px;'>تبديل المستخدم</a>", unsafe_allow_html=True)
st.title("💼 النظام المالي الذكي")

tabs = st.tabs(["📊 نظرة عامة", "➕ إصدار مطالبة", "🗓️ إدارة العمليات", "💰 التحصيل المالي", "📜 سجل التاريخ"])

# التبويب 1: نظرة عامة
with tabs[0]:
    due = sum([float(l.get('amount_due', 0)) for l in l_data])
    paid = sum([float(l.get('amount_paid', 0)) for l in l_data])
    c1, c2, c3 = st.columns(3)
    c1.metric("المتبقي في السوق", f"{due - paid:,.2f} د.أ")
    c2.metric("إجمالي المحصل", f"{paid:,.2f} د.أ")
    c3.metric("إجمالي الفواتير", len(b_data))

# التبويب 2: إصدار فاتورة (حل مشكلة ظهور الطالبات)
with tabs[1]:
    if not s_data:
        st.warning("يرجى إضافة شقق أولاً من الصفحة الرئيسية")
    else:
        with st.form("pro_billing"):
            col1, col2 = st.columns(2)
            apt_name = col1.selectbox("الشقة المستهدفة", [s['name'] for s in s_data])
            b_type = col2.selectbox("نوع المصروف", ["كهرباء", "إيجار", "صيانة", "إنترنت", "خدمات"])
            
            amt = st.number_input("المبلغ الإجمالي", min_value=0.0)
            is_owner = st.checkbox("🚩 المصروف بالكامل على المالك (صيانة عامة)")
            
            target_apt = next(s for s in s_data if s['name'] == apt_name)
            # فلترة الطالبات حسب الشقة المختارة
            apt_stds = [std for std in t_data if std['sakan_id'] == target_apt['id']]
            
            st.write(f"👥 الطالبات المسجلات في هذه الشقة: **{len(apt_stds)}**")
            
            shares = {}
            if not is_owner and apt_stds:
                def_share = round(amt / len(apt_stds), 2) if amt > 0 else 0.0
                st.info("سيتم توزيع المبلغ بالتساوي، يمكنك التعديل يدوياً:")
                c_s1, c_s2 = st.columns(2)
                for i, std in enumerate(apt_stds):
                    with (c_s1 if i % 2 == 0 else c_s2):
                        shares[std['id']] = st.number_input(f"حصة {std['name']}", value=def_share, key=f"std_{std['id']}")
            
            if st.form_submit_button("إصدار وتثبيت ✅"):
                try:
                    # 1. إدخال الفاتورة الأم
                    note = "بذمة المالك" if is_owner else "بذمة الطالبات"
                    b_res = supabase.table("electricity_bills").insert({
                        "sakan_id": target_apt['id'], "total_amount": amt, 
                        "bill_type": b_type, "bill_month": str(datetime.date.today().strftime("%Y-%m")),
                        "notes": note
                    }).execute()
                    
                    # 2. إدخال الذمم إذا لم تكن على المالك
                    if not is_owner and shares:
                        b_id = b_res.data[0]['id']
                        l_recs = [{
                            "student_id": sid, "bill_id": b_id, "type": b_type,
                            "amount_due": s_amt, "status": "pending"
                        } for sid, s_amt in shares.items()]
                        supabase.table("student_ledger").insert(l_recs).execute()
                    
                    log_action("إصدار فاتورة", f"أصدر {st.session_state['user_name']} فاتورة {b_type} لشقة {apt_name} بمبلغ {amt}")
                    st.success("تم التثبيت بنجاح")
                    st.rerun()
                except Exception as e: st.error(f"خطأ: {e}")

# التبويب 3: إدارة العمليات (التصميم الجديد)
with tabs[2]:
    for bill in b_data:
        is_owner_bill = "بذمة المالك" in (bill.get('notes') or "")
        style = "owner-card" if is_owner_bill else ""
        with st.container():
            st.markdown(f"""
                <div class="bill-card {style}">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:bold; font-size:18px;">{bill.get('bill_type')} - {bill.get('sakanat',{}).get('name')}</span>
                        <span style="color:#2e86de; font-weight:bold;">{bill['total_amount']} د.أ</span>
                    </div>
                    <div style="font-size:13px; color:#666; margin-top:5px;">
                        📅 {bill['bill_month']} | {bill.get('notes', '')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2, _ = st.columns([1,1,3])
            if c_btn1.button("🗑️ حذف نهائي", key=f"del_{bill['id']}", type="primary"):
                supabase.table("electricity_bills").delete().eq("id", bill['id']).execute()
                log_action("حذف فاتورة", f"قام {st.session_state['user_name']} بحذف فاتورة {bill['bill_type']} لشقة {bill.get('sakanat',{}).get('name')}")
                st.rerun()

# التبويب 4: التحصيل
with tabs[3]:
    pending = [l for l in l_data if float(l['amount_due']) > float(l['amount_paid'])]
    if not pending:
        st.success("لا يوجد ذمم قائمة حالياً! عمل رائع 👏")
    else:
        for p in pending:
            with st.container(border=True):
                c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
                c_p1.write(f"👤 **{p['students']['name']}** | {p['type']}")
                rem = float(p['amount_due']) - float(p['amount_paid'])
                c_p2.write(f"المتبقي: **{rem} د.أ**")
                if c_p3.button("تم الدفع ✅", key=f"p_{p['id']}"):
                    supabase.table("student_ledger").update({"amount_paid": p['amount_due'], "status": "paid"}).eq("id", p['id']).execute()
                    supabase.table("payments").insert({"ledger_id": p['id'], "amount_paid": rem, "recorded_by": st.session_state['user_name']}).execute()
                    log_action("تحصيل مبلغ", f"حصل {st.session_state['user_name']} مبلغ {rem} من الطالبة {p['students']['name']}")
                    st.rerun()

# التبويب 5: سجل التاريخ (The Real History)
with tabs[4]:
    st.subheader("📜 سجل الحركات التفصيلي")
    audits = supabase.table("audit_logs").select("*").order('created_at', desc=True).limit(100).execute().data
    if audits:
        for a in audits:
            t = pd.to_datetime(a['created_at']).strftime("%Y-%m-%d | %H:%M")
            st.markdown(f"""
                <div style="border-bottom:1px solid #eee; padding:10px 0;">
                    <span class="user-tag">👤 {a.get('user_name', 'System')}</span> 
                    <span style="font-weight:bold; color:#2e86de;">{a['action']}</span><br>
                    <small style="color:#888;">{t}</small> - {a['details']}
                </div>
            """, unsafe_allow_html=True)
    else: st.info("السجل فارغ حالياً.")