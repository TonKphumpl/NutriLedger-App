import streamlit as st
import pandas as pd
import altair as alt
import awswrangler as wr
import os
from datetime import date

st.set_page_config(page_title="Income-Expense & Healthy", layout="wide")

# ---- Initial Session State ----
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["date_", "type_", "expense_category", "lists", "amount", "menu", "calories"])

# ---- Data Management Functions ----
def get_user_file(username):
    """ Generate file path based on username """
    return f's3://income-expense-tracker-webapp/user_data/{username}'

def load_user_data(username):
    """ Load user data from CSV """
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=["Date"]) 
    else:
        return pd.DataFrame(columns=["date_", "type_", "expense_category", "lists", "amount", "menu", "calories"])

def save_user_data(username, df):
    """ Save user data to CSV file """
    file_path = f's3://income-expense-tracker-webapp/user_data/data_{username}.csv'
    wr.s3.to_csv(df=df, path=file_path, index=False)

# ---- Sidebar: User Selection ----
s3_prefix = "s3://income-expense-tracker-webapp/user_data/"
file_list = wr.s3.list_objects(s3_prefix)
user_list = [
    os.path.basename(f).split("_")[1].replace(".csv", "")
    for f in file_list
    if f.endswith(".csv") and os.path.basename(f).startswith("data_")
]
selected_user = st.sidebar.selectbox("Select User", user_list + ["➕ Create New User"])

if selected_user == "➕ Create New User":
    new_username = st.sidebar.text_input("Enter new username")
    if st.sidebar.button("Create"):
        if new_username.strip() != "":
            selected_user = new_username.strip()
            st.session_state.username = selected_user
            st.session_state.data = pd.DataFrame(columns=["date_", "type_", "expense_category", "lists", "amount", "menu", "calories"])
            st.session_state.selected_user_initialized = True
        else:
            st.sidebar.error("⚠️ Please enter a valid username!")

if selected_user and selected_user != "➕ Create New User":
    if "username" not in st.session_state or st.session_state.username != selected_user:
        st.session_state.username = selected_user
        st.session_state.data = load_user_data(selected_user)

# ---- Sidebar: Goal Settings ----
st.sidebar.title("🎯 Personal Goals")

target_calories = st.sidebar.number_input(
    "Daily Calorie Target (kcal)", min_value=100, max_value=5000,
    value=st.session_state.get("target_calories", 2000), step=50
)
target_expense = st.sidebar.number_input(
    "Daily Expense Target (THB)", min_value=0, max_value=100000,
    value=st.session_state.get("target_expense", 500), step=50
)

st.session_state.target_calories = target_calories
st.session_state.target_expense = target_expense

# ---- Main Content ----
st.title("📒 Income-Expense and Healthy Eating Tracker")

tab1, tab2, tab3 = st.tabs(["➕ Record Entry", "📋 History", "📊 Health Dashboard"])

# ---- Menu Options ----
menu_options = {
    "Rice Soup with Fish": 325,
    "Khao Soi Chicken": 390,
    "Coffee": 180,
    "Green Tea": 150,
    "Fried Rice with Pork": 450,
    "Papaya Salad (Thai Style)": 120,
    "Water": 0,
}

expense_categories = [
    "Food and Drinks",
    "Transportation (Fare/Fuel)",
    "Household Items",
    "Clothing/Cosmetics",
    "Medical Expenses",
    "Other Expenses (please specify)",
]

# ---- Tab 1: Record Entry ----
with tab1:
    st.subheader("➕ New Entry")
    with st.form("form_record", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("date_", value=date.today())
            transaction_type = st.radio("type_", ["Income", "Expense"])
            if transaction_type == "Expense":
                category = st.selectbox("Expense Category", expense_categories)
            else:
                category = "-"
            description = st.text_input("Description")
        with col2:
            amount = st.number_input("Amount (THB)", min_value=0.0, step=1.0)
            menu = st.selectbox("Food/Drink Menu", ["-"] + list(menu_options.keys()))
            calories = menu_options.get(menu, 0) if menu != "-" else 0

        submitted = st.form_submit_button("Submit")

        if submitted:
            new_data = pd.DataFrame({
                "date_": [pd.to_datetime(date_input)],
                "type_": [transaction_type],
                "expense_category": [category],
                "lists": [description],
                "amount": [amount],
                "menu": [menu],
                "calories": [calories],
            })

            st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
            save_user_data(st.session_state.username, st.session_state.data)
            st.success("✅ Entry saved successfully!")

# ---- Tab 2: History ----
with tab2:
    st.subheader("📋 Entry History")
    if not st.session_state.data.empty:
        df = st.session_state.data
        df_display = df.sort_values(by="date_", ascending=False)
        st.dataframe(df_display, use_container_width=True)

        total_income = df[df["type_"] == "Income"]["amount"].sum()
        total_expense = df[df["type_"] == "Expense"]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("💰 Total Income", f"{total_income:,.2f} THB")
        col2.metric("💸 Total Expense", f"{total_expense:,.2f} THB")
    else:
        st.info("No entries recorded yet.")

# ---- Tab 3: Health Dashboard ----
with tab3:
    st.subheader("📊 Consumption Dashboard")
    if not st.session_state.data.empty:
        df = st.session_state.data

        today = pd.to_datetime(date.today())
        df_today = df[df["date_"] == today]

        # --- Today Summary ---
        st.markdown("### 📅 Today's Summary")
        today_calories = df_today["calories"].sum()
        today_expenses = df_today[df_today["type_"] == "Expense"]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("🔥 Calories Today", f"{today_calories:,.0f} kcal")
        col2.metric("💸 Expenses Today", f"{today_expenses:,.2f} THB")

        # --- Progress Bar ---
        percent = min(today_calories / target_calories, 1.0)
        st.progress(percent, text=f"{today_calories:.0f} / {target_calories} kcal")
        if today_calories > target_calories:
            st.error("⚠️ You exceeded your calorie goal today!")
        else:
            st.success("✅ You're within your target range. Great job!")

        st.divider()

        # --- This Month Summary ---
        st.markdown("### 📅 Monthly Summary")
        df['Month'] = df['date_'].dt.to_period('M')
        this_month = today.to_period('M')
        df_month = df[df['Month'] == this_month]

        month_calories = df_month["calories"].sum()
        month_expenses = df_month[df_month["type_"] == "Expense"]["amount"].sum()
        month_income = df_month[df_month["type_"] == "Income"]["amount"].sum()

        col3, col4, col5 = st.columns(3)
        col3.metric("🔥 Monthly Calories", f"{month_calories:,.0f} kcal")
        col4.metric("💸 Monthly Expenses", f"{month_expenses:,.2f} THB")
        col5.metric("💰 Monthly Income", f"{month_income:,.2f} THB")

        # --- Income/Expense Graphs ---
        daily_expenses = df_month[df_month["type_"] == "Expense"].groupby("date_").agg({"amount": "sum"}).reset_index()
        daily_income = df_month[df_month["type_"] == "Income"].groupby("date_").agg({"amount": "sum"}).reset_index()

        st.markdown("### 📈 Daily Expenses")
        expense_chart = alt.Chart(daily_expenses).mark_bar(color="skyblue").encode(
            x="Date:T",
            y="Amount:Q",
            tooltip=["Date:T", "Amount:Q"]
        ).properties(width=700, height=400)

        st.altair_chart(expense_chart, use_container_width=True)

        st.markdown("### 📈 Daily Income")
        income_chart = alt.Chart(daily_income).mark_bar(color="orange").encode(
            x="Date:T",
            y="Amount:Q",
            tooltip=["Date:T", "Amount:Q"]
        ).properties(width=700, height=400)

        st.altair_chart(income_chart, use_container_width=True)
