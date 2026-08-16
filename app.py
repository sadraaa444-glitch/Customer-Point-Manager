import streamlit as st
import pandas as pd
from PIL import Image
from sqlalchemy.exc import IntegrityError
from streamlit.runtime.scriptrunner import RerunException
from datetime import datetime, timedelta

from database import init_db, get_db
import crud
from models import TransactionType
from utils import date_to_jalali, jalali_to_date

try:
    logo_image = Image.open("logo.png")
    st.set_page_config(
        page_title="سیستم مدیریت امتیازات",
        page_icon=logo_image,
        layout="wide"
    )
except FileNotFoundError:
    st.set_page_config(
        page_title="سیستم مدیریت امتیازات",
        page_icon="🌟",
        layout="wide"
    )

st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        direction: ltr !important;
    }
    
    .stApp { direction: rtl; font-family: Tahoma, sans-serif; }
    h1, h2, h3, h4, h5, h6, p, label { text-align: right !important; }
    table { width: 100% !important; margin-left: auto; margin-right: auto; }
    th, td { text-align: center !important; vertical-align: middle !important; }
    .stTextInput input, .stSelectbox select, .stNumberInput input { direction: rtl; }
    [data-baseweb="select"], [data-baseweb="select"] > div, [data-baseweb="popover"], [role="option"] {
        direction: rtl !important; text-align: right !important;
    }
    button[kind="primary"] { background-color: #007bff !important; border-color: #007bff !important; color: white !important; }
    button[kind="primary"]:hover { background-color: #0056b3 !important; border-color: #0056b3 !important; }
    button[kind="secondary"]:hover, button[kind="secondary"]:active, button[kind="secondary"]:focus {
        border-color: #007bff !important; color: #007bff !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #007bff !important; box-shadow: 0 0 0 1px #007bff !important;
    }
    [data-testid="stDownloadButton"] button {
        background-color: #ffffff !important; color: #217346 !important; border: 2px solid #217346 !important; font-weight: bold;
    }
    [data-testid="stDownloadButton"] button:hover { background-color: #217346 !important; color: #ffffff !important; }
    [data-testid="stPopoverBody"] button:not([data-testid="stDownloadButton"] button) {
        background-color: #ffffff !important; color: #007bff !important; border: 2px solid #007bff !important; font-weight: bold;
    }
    [data-testid="stPopoverBody"] button:not([data-testid="stDownloadButton"] button):hover {
        background-color: #007bff !important; color: #ffffff !important;
    }
    [data-testid="stMetric"] { display: flex; flex-direction: column; align-items: center; text-align: center !important; }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { text-align: center !important; justify-content: center !important; width: 100%; }
    [data-testid="stMetricValue"] { direction: ltr !important; text-align: center !important; justify-content: center !important; width: 100%; }
    
    button[kind="tertiary"] {
        background-color: transparent !important;
        border: none !important;
        color: #007bff !important;
        font-weight: bold;
        padding: 0 !important;
    }
    
    button[kind="tertiary"]:hover {
        color: #0056b3 !important;
        text-decoration: underline;
    }

    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def setup_db():
    init_db()
    db = next(get_db())
    crud.create_admin_if_not_exists(db)

setup_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

def set_flash_message(msg: str, msg_type: str = "success"):
    st.session_state["flash"] = {"msg": msg, "type": msg_type}

def show_flash_messages():
    if "flash" in st.session_state:
        flash = st.session_state["flash"]
        if flash["type"] == "success":
            st.success(flash["msg"])
        elif flash["type"] == "error":
            st.error(flash["msg"])
        elif flash["type"] == "warning":
            st.warning(flash["msg"])
        del st.session_state["flash"]

def login_page():
    st.title("ورود به سیستم مدیریت امتیازات")
    with st.form("login_form"):
        username_input = st.text_input("نام کاربری")
        password_input = st.text_input("رمز عبور", type="password")
        submit_button = st.form_submit_button("ورود به سیستم")

        if submit_button:
            if not username_input or not password_input:
                st.warning("لطفا تمام فیلدها را پر کنید.")
                return

            db = next(get_db())
            user = crud.get_user_by_username(db, username_input)

            if user and crud.verify_password(password_input, user.hashed_password):
                st.session_state.authenticated = True
                st.session_state.username = user.username
                st.success("ورود موفقیت‌آمیز بود!")
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور نادرست است.")

@st.dialog("📈 گزارش جامع")
def show_general_report_dialog(customers_data):
    if not customers_data:
        st.warning("هنوز داده‌ای برای گزارش‌گیری وجود ندارد.")
        return

    total_customers = len(customers_data)
    total_points = sum(pts for _, pts in customers_data)
    avg_points = int(total_points / total_customers) if total_customers > 0 else 0
    pos_customers = sum(1 for _, pts in customers_data if pts > 0)
    neg_customers = sum(1 for _, pts in customers_data if pts < 0)
    zero_customers = sum(1 for _, pts in customers_data if pts == 0)
    total_pos_points = sum(pts for _, pts in customers_data if pts > 0)
    total_neg_points = sum(pts for _, pts in customers_data if pts < 0)
    best_customer = max(customers_data, key=lambda x: x[1]) if customers_data else (None, 0)

    def render_stat_card(label, value, color="#333333"):
        html = f'''<div style="background-color:#f8f9fa;border:1px solid #e2e8f0;border-radius:8px;padding:12px 8px;text-align:center;margin-bottom:10px;">
    <div style="font-size:13px;color:#64748b;margin-bottom:6px;font-weight:500;">{label}</div>
    <div style="font-size:20px;font-weight:bold;color:{color};direction:ltr;unicode-bidi:isolate;">{value}</div>
    </div>'''
        st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: render_stat_card("تعداد کل مشتریان", total_customers)
    with c2: render_stat_card("تراز کل (مجموع امتیازات)", total_points)
    with c3: render_stat_card("میانگین امتیاز هر نفر", avg_points)

    c4, c5, c6 = st.columns(3)
    with c4: render_stat_card("تعداد بستانکاران (+)", pos_customers, color="#27ae60")
    with c5: render_stat_card("تعداد بدهکاران (-)", neg_customers, color="#c0392b")
    with c6: render_stat_card("مشتریان بی‌حساب (۰)", zero_customers)

    c7, c8, c9 = st.columns(3)
    with c7: render_stat_card("کل امتیازات بستانکار", total_pos_points, color="#27ae60")
    with c8: render_stat_card("کل امتیازات بدهکار", total_neg_points, color="#c0392b")
    with c9:
        best_str = f"{best_customer[0].name} ({best_customer[1]})" if best_customer[0] else "-"
        render_stat_card("برترین مشتری", best_str, color="#007bff")

    st.divider()

    report_data = [
        {"ردیف": 1, "شاخص آماری": "تعداد کل مشتریان", "مقدار": total_customers},
        {"ردیف": 2, "شاخص آماری": "مجموع کل امتیازات (تراز سیستم)", "مقدار": total_points},
        {"ردیف": 3, "شاخص آماری": "میانگین امتیاز هر مشتری", "مقدار": avg_points},
        {"ردیف": 4, "شاخص آماری": "تعداد مشتریان با امتیاز مثبت", "مقدار": pos_customers},
        {"ردیف": 5, "شاخص آماری": "تعداد مشتریان با امتیاز منفی", "مقدار": neg_customers},
        {"ردیف": 6, "شاخص آماری": "تعداد مشتریان بی‌حساب (صفر)", "مقدار": zero_customers},
        {"ردیف": 7, "شاخص آماری": "مجموع کل امتیازات بستانکار (+)", "مقدار": total_pos_points},
        {"ردیف": 8, "شاخص آماری": "مجموع کل امتیازات بدهکار (-)", "مقدار": total_neg_points},
    ]

    if best_customer[0]:
        report_data.append({
            "ردیف": 9,
            "شاخص آماری": "برترین مشتری (بیشترین امتیاز)",
            "مقدار": f"{best_customer[0].name} با {best_customer[1]} امتیاز"
        })

    df_report = pd.DataFrame(report_data)
    csv_data = df_report.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 دانلود فایل اکسل گزارش کلی",
        data=csv_data,
        file_name="system_general_report.csv",
        mime="text/csv",
        use_container_width=True
    )

def show_main_dashboard():
    st.title("📊 داشبورد کل مشتریان و امتیازات")
    show_flash_messages()

    with st.expander("➕ ثبت مشتری جدید", expanded=False):
        with st.form("new_customer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            new_name = col1.text_input("نام و نام خانوادگی مشتری *")
            new_phone = col2.text_input("شماره تماس (اختیاری)")
            submitted = st.form_submit_button("ثبت در سیستم")

            if submitted:
                if new_name.strip():
                    db = next(get_db())
                    try:
                        crud.create_customer(
                            db,
                            name=new_name.strip(),
                            phone=new_phone.strip() or None
                        )
                        db.commit()
                        set_flash_message(f"مشتری {new_name} با موفقیت ثبت شد.")
                        st.rerun()
                    except IntegrityError:
                        db.rollback()
                        st.error("خطا! مشتری با این مشخصات قبلاً ثبت شده است.")
                    except RerunException:
                        raise
                    except Exception as e:
                        db.rollback()
                        st.error(f"خطای سیستمی: {e}")
                else:
                    st.warning("وارد کردن نام مشتری الزامی است.")

    st.divider()
    st.subheader("جستجو، ورود به پرونده یا حذف مشتری")

    db = next(get_db())
    customers_data = crud.get_customers_with_balance(db)

    if customers_data:
        customer_options = {"- انتخاب کنید -": None}
        for customer, total_points in customers_data:
            points_text = f"\u200e{total_points}\u200e"
            customer_options[f"{customer.name} | امتیاز: {points_text}"] = customer.id

        selected_label = st.selectbox("انتخاب از لیست مشتریان:", list(customer_options.keys()))
        selected_id = customer_options[selected_label]

        if selected_id is not None:
            col_enter, col_del = st.columns([8, 2])
            with col_enter:
                if st.button("ورود به پرونده و ثبت تراکنش", type="primary", use_container_width=True):
                    st.session_state["active_customer_id"] = selected_id
                    st.rerun()

            with col_del:
                if st.button("حذف مشتری", type="secondary", use_container_width=True):
                    try:
                        customer_to_del = crud.get_customer_by_id(db, selected_id)
                        if customer_to_del:
                            db.delete(customer_to_del)
                            db.commit()
                            set_flash_message("مشتری با موفقیت حذف شد.")
                            st.rerun()
                    except RerunException:
                        raise
                    except Exception as e:
                        db.rollback()
                        st.error(f"خطا در حذف مشتری: {e}")
    else:
        st.info("هنوز مشتری‌ای ثبت نشده است.")

    st.divider()

    if "sort_desc" not in st.session_state:
        st.session_state.sort_desc = True

    if customers_data:
        customers_data.sort(key=lambda x: x[0].id, reverse=st.session_state.sort_desc)

        col_title, col_menu = st.columns([15, 1.5])
        with col_title:
            st.markdown("""<h3 style="margin: 0; padding-top: 5px; padding-bottom: 10px;">لیست و وضعیت امتیازات کل مشتریان</h3>""", unsafe_allow_html=True)

        with col_menu:
            with st.popover(" ", use_container_width=True):
                sort_icon = "نزولی" if st.session_state.sort_desc else "صعودی"
                if st.button(f"مرتب‌سازی: {sort_icon}", use_container_width=True):
                    st.session_state.sort_desc = not st.session_state.sort_desc
                    st.rerun()

                if st.button("📈 گزارش", use_container_width=True):
                    show_general_report_dialog(customers_data)

                df_data = [{"شناسه": c.id, "نام مشتری": c.name, "امتیاز کل": pts, "تاریخ ثبت": date_to_jalali(c.created_at)} for c, pts in customers_data]
                csv_data = pd.DataFrame(df_data).to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 خروجی اکسل",
                    data=csv_data,
                    file_name="customers_list.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.markdown(
            """
            <div style="display:flex; font-weight:bold; background-color:#f8f9fa; padding:12px; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:10px;">
                <div style="flex:1; text-align:center;">شناسه</div>
                <div style="flex:3; text-align:center;">نام مشتری (ورود به پرونده)</div>
                <div style="flex:2; text-align:center;">امتیاز کل</div>
                <div style="flex:3; text-align:center;">تاریخ ثبت</div>
            </div>
            """, unsafe_allow_html=True
        )

        for c, pts in customers_data:
            cc1, cc2, cc3, cc4 = st.columns([1, 3, 2, 3])
            
            cc1.markdown(f"<div style='text-align:center; padding-top:8px;'>{c.id}</div>", unsafe_allow_html=True)
            
            if cc2.button(c.name, key=f"go_{c.id}", use_container_width=True, type="tertiary"):
                st.session_state["active_customer_id"] = c.id
                st.rerun()
            
            pts_color = "#27ae60" if pts > 0 else "#c0392b" if pts < 0 else "inherit"
            cc3.markdown(f"<div style='direction:ltr; text-align:center; padding-top:8px; font-weight:bold; color:{pts_color};'>{pts}</div>", unsafe_allow_html=True)
            
            cc4.markdown(f"<div style='text-align:center; padding-top:8px;'>{date_to_jalali(c.created_at)}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 0; opacity: 0.2;'>", unsafe_allow_html=True)
    else:
        st.subheader("لیست و وضعیت امتیازات کل مشتریان")
        st.info("هنوز مشتری‌ای ثبت نشده است.")

def get_weighted_average(transactions, days):
    if not transactions:
        return 0
        
    sorted_tx = sorted(transactions, key=lambda x: x.transaction_date)
    history = []
    running_bal = 0
    
    for tx in sorted_tx:
        t_date = tx.transaction_date
        if isinstance(t_date, datetime):
            t_date = t_date.date()
        
        running_bal += tx.points
        if running_bal <= 0:
            history = [(t_date, 0)]
        else:
            history.append((t_date, running_bal))
            
    if not history:
        return 0
        
    today = datetime.now().date()
    start_window = today - timedelta(days=days - 1)
    
    total_weight = 0
    for day_offset in range(days):
        current_date = start_window + timedelta(days=day_offset)
        daily_bal = 0
        for t_date, t_bal in history:
            if t_date <= current_date:
                daily_bal = max(0, t_bal)
            else:
                break
        total_weight += daily_bal
        
    return int(total_weight / days) if days > 0 else 0

@st.dialog("گزارش میانگین حساب مشتری")
def show_loan_report_dialog(customer, transactions):
    st.write(f"مشتری: **{customer.name}**")
    
    avg_3 = get_weighted_average(transactions, 90)
    avg_6 = get_weighted_average(transactions, 180)
    avg_12 = get_weighted_average(transactions, 365)
    
    col1, col2, col3 = st.columns(3)
    
    def render_avg_card(label, value):
        html = f'''<div style="background-color:#f8f9fa;border:1px solid #e2e8f0;border-radius:8px;padding:12px 8px;text-align:center;margin-bottom:10px;">
    <div style="font-size:13px;color:#64748b;margin-bottom:6px;font-weight:500;">{label}</div>
    <div style="font-size:20px;font-weight:bold;color:#007bff;direction:ltr;">{value}</div>
    </div>'''
        st.markdown(html, unsafe_allow_html=True)

    with col1:
        render_avg_card("۳ ماهه", avg_3)
    with col2:
        render_avg_card("۶ ماهه", avg_6)
    with col3:
        render_avg_card("۱۲ ماهه", avg_12)
        
    st.divider()
    today_jalali = date_to_jalali(datetime.now().date())
    st.caption(f"تاریخ تهیه گزارش: {today_jalali}")
    
    with st.expander("راهنمای محاسبه میانگین"):
        st.caption("این اعداد نشان‌دهنده میانگین وزن‌دار (رسوب) امتیازات در بازه‌های زمانی هستند. هرچه امتیاز مثبت مدت طولانی‌تری در حساب بماند، میانگین بالاتر می‌رود")

def show_customer_profile(customer_id: int):
    if "tx_sort_desc" not in st.session_state:
        st.session_state.tx_sort_desc = True

    db = next(get_db())
    customer = crud.get_customer_by_id(db, customer_id)

    if not customer:
        st.error("مشتری یافت نشد.")
        if "active_customer_id" in st.session_state:
            del st.session_state["active_customer_id"]
        return

    transactions = crud.get_customer_transactions(db, customer_id)
    total_points = sum(tx.points for tx in transactions)

    col_title, col_back = st.columns([8, 2])
    with col_title:
        st.title(f"پرونده مشتری: {customer.name}")
        st.caption(f"شماره تماس: {customer.phone or 'ثبت نشده'} | تاریخ عضویت: {date_to_jalali(customer.created_at)}")

    with col_back:
        st.write("")
        if st.button("بازگشت به داشبورد", use_container_width=True):
            if "active_customer_id" in st.session_state:
                del st.session_state["active_customer_id"]
            st.rerun()

    show_flash_messages()

    col1, col2 = st.columns(2)
    col1.metric("امتیاز کل فعلی", total_points)
    col2.metric("تعداد کل تراکنش‌ها", len(transactions))

    st.divider()
    
    col_sub, col_rep = st.columns([15, 2])
    with col_sub:
        st.markdown("""<h3 style="margin: 0; padding-top: 5px; padding-bottom: 10px;">ثبت تراکنش جدید</h3>""", unsafe_allow_html=True)
    with col_rep:
        if st.button("گزارش", use_container_width=True):
            show_loan_report_dialog(customer, transactions)

    with st.form(key=f"transaction_form_{customer_id}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        tx_type_str = c1.selectbox("نوع تراکنش", ["کسب امتیاز (خرید)", "خرج امتیاز (کالا)", "وام"])
        points_val = c2.number_input("مقدار امتیاز", min_value=1, step=1, value=10)
        ref_num = c3.text_input("شماره فاکتور / ارجاع (اختیاری)")
        
        c4, c5 = st.columns([1, 2])
        jalali_date_str = c4.text_input("تاریخ (مثال: 1403/05/25 - پیش‌فرض: امروز)")
        desc = c5.text_input("توضیحات تکمیلی (مثلاً تحویل آب‌سردکن)")

        submit_tx = st.form_submit_button("ثبت در دفتر حساب")

        if submit_tx:
            tx_date = None
            if jalali_date_str.strip():
                try:
                    parts = jalali_date_str.strip().split('/')
                    tx_date = jalali_to_date(int(parts[0]), int(parts[1]), int(parts[2]))
                except Exception:
                    st.error("فرمت تاریخ نامعتبر است. از فرمت سال/ماه/روز استفاده کنید.")
                    st.stop()

            if "کسب" in tx_type_str:
                tx_enum = TransactionType.EARN
            elif "خرج" in tx_type_str:
                tx_enum = TransactionType.REDEEM
            else:
                tx_enum = TransactionType.LOAN

            try:
                crud.add_transaction(
                    db,
                    customer.id,
                    tx_enum,
                    int(points_val),
                    ref_num or None,
                    desc or None
                )
                db.commit()
                
                if tx_date:
                    all_tx = crud.get_customer_transactions(db, customer.id)
                    if all_tx:
                        latest_tx = max(all_tx, key=lambda x: x.id)
                        latest_tx.transaction_date = tx_date
                        db.commit()

                set_flash_message("تراکنش با موفقیت ثبت شد.")
                st.rerun()
            except RerunException:
                raise
            except Exception as e:
                db.rollback()
                set_flash_message(f"خطا در ثبت تراکنش: {e}", "error")
                st.rerun()

    st.divider()

    col_hist_title, col_hist_menu = st.columns([15, 2])
    with col_hist_title:
        st.markdown("""<h3 style="margin: 0; padding-top: 5px; padding-bottom: 10px;">تاریخچه تراکنش‌ها</h3>""", unsafe_allow_html=True)
    with col_hist_menu:
        with st.popover(" ", use_container_width=True):
            sort_icon = "بر اساس تاریخ (جدیدترین)" if st.session_state.tx_sort_desc else "بر اساس تاریخ (قدیمی‌ترین)"
            if st.button(f"مرتب‌سازی: {sort_icon}", key="sort_tx_btn", use_container_width=True):
                st.session_state.tx_sort_desc = not st.session_state.tx_sort_desc
                st.rerun()

    if transactions:
        st.markdown(
            """
            <div style="display:flex; font-weight:bold; background-color:#f8f9fa; padding:12px; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:10px;">
                <div style="flex:1; text-align:center;">ردیف</div>
                <div style="flex:1.5; text-align:center;">نوع</div>
                <div style="flex:1.5; text-align:center;">مقدار</div>
                <div style="flex:1.5; text-align:center;">فاکتور</div>
                <div style="flex:2.5; text-align:center;">تاریخ</div>
                <div style="flex:3; text-align:center;">توضیحات</div>
                <div style="flex:1; text-align:center;">حذف</div>
            </div>
            """, unsafe_allow_html=True
        )

        chrono_tx = sorted(transactions, key=lambda x: (x.transaction_date, x.id), reverse=st.session_state.tx_sort_desc)

        for idx, tx in enumerate(chrono_tx):
            row_num = idx + 1
            t1, t2, t3, t4, t5, t6, t7 = st.columns([1, 1.5, 1.5, 1.5, 2.5, 3, 1])
            
            t1.markdown(f"<div style='text-align:center; padding-top:8px;'>{row_num}</div>", unsafe_allow_html=True)

            tx_str = "خرید" if tx.transaction_type == TransactionType.EARN else "کالا" if tx.transaction_type == TransactionType.REDEEM else "وام"
            t2.markdown(f"<div style='text-align:center; padding-top:8px;'>{tx_str}</div>", unsafe_allow_html=True)

            tx_color = "#27ae60" if tx.points > 0 else "#c0392b" if tx.points < 0 else "inherit"
            t3.markdown(f"<div style='direction:ltr; text-align:center; font-weight:bold; padding-top:8px; color:{tx_color};'>{tx.points}</div>", unsafe_allow_html=True)

            t4.markdown(f"<div style='text-align:center; padding-top:8px;'>{tx.reference_number or '-'}</div>", unsafe_allow_html=True)
            t5.markdown(f"<div style='text-align:center; padding-top:8px;'>{date_to_jalali(tx.transaction_date)}</div>", unsafe_allow_html=True)
            t6.markdown(f"<div style='text-align:center; padding-top:8px;'>{tx.description or '-'}</div>", unsafe_allow_html=True)

            if t7.button("🗑️", key=f"del_tx_{tx.id}", help="حذف این تراکنش", type="tertiary"):
                try:
                    db.delete(tx)
                    db.commit()
                    set_flash_message("تراکنش با موفقیت حذف شد.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    set_flash_message(f"خطا در حذف تراکنش: {e}", "error")
                    st.rerun()
            
            st.markdown("<hr style='margin: 0; opacity: 0.1;'>", unsafe_allow_html=True)
    else:
        st.info("هنوز تراکنشی برای این مشتری ثبت نشده است.")

if not st.session_state.authenticated:
    login_page()
else:
    if "active_customer_id" in st.session_state:
        show_customer_profile(st.session_state["active_customer_id"])
    else:
        show_main_dashboard()