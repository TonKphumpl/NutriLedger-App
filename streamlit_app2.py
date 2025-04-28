import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Dashboard", layout="wide")

# Title
st.title("Dashboard")

# Tabs for Day, Week, Month, Year
timeframe = st.selectbox("Select Timeframe", ["Day", "Week", "Month", "Year"], index=2)

# Financial Summary
st.subheader("Financial Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Income", value="$18,033", delta="↑")

with col2:
    st.metric(label="Expenses", value="$4,412", delta="↓")

with col3:
    st.metric(label="Net Savings", value="$13,621", delta="↑", delta_color="normal")

# Nutrition Summary
st.subheader("Nutrition Summary")
col4, col5, col6, col7 = st.columns(4)

with col4:
    st.metric(label="Calories", value="34,883")

with col5:
    st.metric(label="Protein", value="2908g")

with col6:
    st.metric(label="Carbs", value="3214g")

with col7:
    st.metric(label="Fat", value="1136g")

# Expenses by Category
st.subheader("Expenses by Category")

# Dummy data for expenses
expense_data = {
    "Category": ["Health", "Education", "Other", "Utilities", "Transportation",
                 "Food & Dining", "Entertainment", "Shopping", "Housing"],
    "Amount": [500, 800, 300, 400, 600, 700, 350, 500, 550]
}
df_expenses = pd.DataFrame(expense_data)

# Pie chart using Plotly
fig = px.pie(df_expenses, names='Category', values='Amount',
             color_discrete_sequence=px.colors.qualitative.Set3,
             hole=0.3)

st.plotly_chart(fig, use_container_width=True)
