import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import date

st.set_page_config(page_title="รายรับ-รายจ่าย & สุขภาพ", layout="wide")

# ---- Initial Session State ----
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["วันที่", "ประเภท", "กลุ่มรายจ่าย", "รายการ", "จำนวนเงิน", "เมนู", "แคลอรี่"])

# ---- ฟังก์ชันจัดการข้อมูล ----
def get_user_file(username):
    """ สร้างชื่อไฟล์ตามชื่อผู้ใช้ """
    return f"data_{username}.csv"

def load_user_data(username):
    """ โหลดข้อมูลจากไฟล์ CSV ของผู้ใช้ """
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=["วันที่"])
    else:
        return pd.DataFrame(columns=["วันที่", "ประเภท", "กลุ่มรายจ่าย", "รายการ", "จำนวนเงิน", "เมนู", "แคลอรี่"])

def save_user_data(username, df):
    """ บันทึกข้อมูลลงในไฟล์ CSV ของผู้ใช้ """
    file_path = get_user_file(username)
    df.to_csv(file_path, index=False)

# ---- Sidebar : เลือกผู้ใช้งาน ----
st.sidebar.title("👤 ผู้ใช้งาน")
user_list = [f.split("_")[1].replace(".csv", "") for f in os.listdir() if f.startswith("data_") and f.endswith(".csv")]
selected_user = st.sidebar.selectbox("เลือกผู้ใช้", user_list + ["➕ สร้างผู้ใช้ใหม่"])

if selected_user == "➕ สร้างผู้ใช้ใหม่":
    new_username = st.sidebar.text_input("กรอกชื่อผู้ใช้ใหม่")
    if st.sidebar.button("สร้าง"):
        if new_username.strip() != "":
            selected_user = new_username.strip()
            st.session_state.username = selected_user  # กำหนดชื่อผู้ใช้ใหม่ใน session_state
            st.session_state.data = pd.DataFrame(columns=["วันที่", "ประเภท", "กลุ่มรายจ่าย", "รายการ", "จำนวนเงิน", "เมนู", "แคลอรี่"])
            # รีเฟรชหน้าหลังจากเลือกชื่อใหม่ โดยไม่ใช้ `st.experimental_rerun()`
            st.session_state.selected_user_initialized = True  # ตั้งค่า session_state ว่าเลือกผู้ใช้แล้ว
        else:
            st.sidebar.error("⚠️ กรุณากรอกชื่อผู้ใช้!")

if selected_user and selected_user != "➕ สร้างผู้ใช้ใหม่":
    if "username" not in st.session_state or st.session_state.username != selected_user:
        st.session_state.username = selected_user
        st.session_state.data = load_user_data(selected_user)

# ---- Sidebar : ตั้งค่าเป้าหมาย ----
st.sidebar.title("🎯 เป้าหมายส่วนตัว")

target_calories = st.sidebar.number_input(
    "เป้าหมายแคลอรี่ต่อวัน (kcal)", min_value=100, max_value=5000,
    value=st.session_state.get("target_calories", 2000), step=50
)
target_expense = st.sidebar.number_input(
    "เป้าหมายรายจ่ายต่อวัน (บาท)", min_value=0, max_value=100000,
    value=st.session_state.get("target_expense", 500), step=50
)

st.session_state.target_calories = target_calories
st.session_state.target_expense = target_expense

# ---- Main Content ----
st.title("📒 บันทึกรายรับ-รายจ่าย และสุขภาพการกิน")

tab1, tab2, tab3 = st.tabs(["➕ บันทึกข้อมูล", "📋 ดูข้อมูลย้อนหลัง", "📊 Dashboard สุขภาพ"])

# ---- ตัวเลือกเมนูอาหาร/เครื่องดื่ม ----
menu_options = {
    "ข้าวต้มปลา": 325,
    "ข้าวซอยไก่": 390,
    "กาแฟ": 180,
    "ชาเขียว": 150,
    "ข้าวผัดหมู": 450,
    "ส้มตำไทย": 120,
    "น้ำเปล่า": 0,
}

expense_categories = [
    "ค่าอาหาร และเครื่องดื่ม",
    "ค่าเดินทาง (ค่ารถ/ค่าน้ำมัน)",
    "ของใช้ในบ้าน",
    "ค่าเสื้อผ้า/เครื่องสำอาง",
    "ค่ารักษาพยาบาล",
    "ค่าใช้จ่ายอื่นๆ (โปรดระบุ)",
]

# ---- Tab 1 : บันทึกข้อมูล ----
with tab1:
    st.subheader("➕ บันทึกข้อมูลใหม่")
    with st.form("form_record", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("วันที่", value=date.today())
            transaction_type = st.radio("ประเภท", ["รายรับ", "รายจ่าย"])
            if transaction_type == "รายจ่าย":
                category = st.selectbox("กลุ่มรายจ่าย", expense_categories)
            else:
                category = "-"
            description = st.text_input("รายการ (ระบุได้เอง)")
        with col2:
            amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=1.0)
            menu = st.selectbox("เมนูอาหาร/เครื่องดื่ม", ["-"] + list(menu_options.keys()))
            calories = menu_options.get(menu, 0) if menu != "-" else 0

        submitted = st.form_submit_button("บันทึกข้อมูล")

        if submitted:
            new_data = pd.DataFrame({
                "วันที่": [pd.to_datetime(date_input)],
                "ประเภท": [transaction_type],
                "กลุ่มรายจ่าย": [category],
                "รายการ": [description],
                "จำนวนเงิน": [amount],
                "เมนู": [menu],
                "แคลอรี่": [calories],
            })

            st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
            save_user_data(st.session_state.username, st.session_state.data)
            st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว!")

# ---- Tab 2 : ดูข้อมูลย้อนหลัง ----
with tab2:
    st.subheader("📋 ดูข้อมูลย้อนหลัง")
    if not st.session_state.data.empty:
        df = st.session_state.data
        df_display = df.sort_values(by="วันที่", ascending=False)
        st.dataframe(df_display, use_container_width=True)

        total_income = df[df["ประเภท"] == "รายรับ"]["จำนวนเงิน"].sum()
        total_expense = df[df["ประเภท"] == "รายจ่าย"]["จำนวนเงิน"].sum()

        col1, col2 = st.columns(2)
        col1.metric("💰 รายรับรวม", f"{total_income:,.2f} บาท")
        col2.metric("💸 รายจ่ายรวม", f"{total_expense:,.2f} บาท")
    else:
        st.info("ยังไม่มีข้อมูลที่บันทึกไว้")

# ---- Tab 3 : Dashboard สุขภาพ ----
with tab3:
    st.subheader("📊 Dashboard สุขภาพการบริโภค")
    if not st.session_state.data.empty:
        df = st.session_state.data

        today = pd.to_datetime(date.today())
        df_today = df[df["วันที่"] == today]

        # --- สรุปวันนี้ ---
        st.markdown("### 📅 สรุปข้อมูลวันนี้")
        today_calories = df_today["แคลอรี่"].sum()
        today_expenses = df_today[df_today["ประเภท"] == "รายจ่าย"]["จำนวนเงิน"].sum()

        col1, col2 = st.columns(2)
        col1.metric("🔥 แคลอรี่ที่ได้รับวันนี้", f"{today_calories:,.0f} kcal")
        col2.metric("💸 รายจ่ายวันนี้", f"{today_expenses:,.2f} บาท")

        # --- Progress Bar ---
        percent = min(today_calories / target_calories, 1.0)
        st.progress(percent, text=f"{today_calories:.0f} / {target_calories} kcal")
        if today_calories > target_calories:
            st.error("⚠️ คุณได้รับพลังงานเกินเป้าหมายวันนี้!")
        else:
            st.success("✅ อยู่ในเกณฑ์ที่กำหนด ดีมากเลยครับ!")

        st.divider()

        # --- สรุปเดือนนี้ ---
        st.markdown("### 📅 สรุปข้อมูลเดือนนี้")
        df['เดือน'] = df['วันที่'].dt.to_period('M')
        this_month = today.to_period('M')
        df_month = df[df['เดือน'] == this_month]

        month_calories = df_month["แคลอรี่"].sum()
        month_expenses = df_month[df_month["ประเภท"] == "รายจ่าย"]["จำนวนเงิน"].sum()
        month_income = df_month[df_month["ประเภท"] == "รายรับ"]["จำนวนเงิน"].sum()

        col3, col4, col5 = st.columns(3)
        col3.metric("🔥 แคลอรี่เดือนนี้", f"{month_calories:,.0f} kcal")
        col4.metric("💸 รายจ่ายเดือนนี้", f"{month_expenses:,.2f} บาท")
        col5.metric("💰 รายรับเดือนนี้", f"{month_income:,.2f} บาท")

        # --- กราฟรายจ่าย-รายรับ ---
        daily_expenses = df_month[df_month["ประเภท"] == "รายจ่าย"].groupby("วันที่").agg({"จำนวนเงิน": "sum"}).reset_index()
        daily_income = df_month[df_month["ประเภท"] == "รายรับ"].groupby("วันที่").agg({"จำนวนเงิน": "sum"}).reset_index()

        st.markdown("### 📈 กราฟรายจ่ายในเดือนนี้")
        expense_chart = alt.Chart(daily_expenses).mark_bar(color="skyblue").encode(
            x="วันที่:T",
            y="จำนวนเงิน:Q",
            tooltip=["วันที่:T", "จำนวนเงิน:Q"]
        ).properties(width=700, height=400)

        st.altair_chart(expense_chart, use_container_width=True)

        st.markdown("### 📈 กราฟรายรับในเดือนนี้")
        income_chart = alt.Chart(daily_income).mark_bar(color="orange").encode(
            x="วันที่:T",
            y="จำนวนเงิน:Q",
            tooltip=["วันที่:T", "จำนวนเงิน:Q"]
        ).properties(width=700, height=400)

        st.altair_chart(income_chart, use_container_width=True)
