import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration with a standard emoji icon instead of a local file
st.set_page_config(layout="wide", page_title="Payment Due Dashboard", page_icon="💰")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    try:
        # Loading MasterData.csv with tab delimiter as identified in the source
        df = pd.read_csv("MasterData.csv", sep='\t')
    except FileNotFoundError:
        st.error("MasterData.csv not found. Please ensure it is in the same folder as this script.")
        return pd.DataFrame()

    # Clean column names and whitespace
    df.columns = df.columns.str.strip()

    # Convert Date column to datetime format
    df["DATE"] = pd.to_datetime(df["DATE"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["DATE"])

    # Ensure numeric types for calculations
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce").fillna(0)
    df["DAYS"] = pd.to_numeric(df["DAYS"], errors="coerce").fillna(0)

    # Aging Categorization based on the 'DAYS' column
    def categorize_aging(days):
        if days <= 30: return "0-30 Days"
        elif days <= 60: return "31-60 Days"
        elif days <= 90: return "61-90 Days"
        else: return "90+ Days"
    
    df["Aging Category"] = df["DAYS"].apply(categorize_aging)
    
    return df

df = load_data()

if df.empty:
    st.warning("No data available to display.")
    st.stop()

# =========================
# SIDEBAR FILTERS
# =========================
# Restricting filters only to Salesman and Customer Name as requested
st.sidebar.header("🔍 Filters")

# Salesman Filter
salesman_options = sorted(df["Salesman Name"].unique().tolist())
selected_salesman = st.sidebar.multiselect("Select Salesman", salesman_options, default=salesman_options)

# Customer Filter (dynamically updates based on selected salesmen)
customer_options = sorted(df[df["Salesman Name"].isin(selected_salesman)]["Customer Name"].unique().tolist())
selected_customer = st.sidebar.multiselect("Select Customer", customer_options, default=customer_options)

# Apply Filters
mask = (df["Salesman Name"].isin(selected_salesman)) & (df["Customer Name"].isin(selected_customer))
filtered_df = df[mask]

# =========================
# KPI METRICS
# =========================
st.title("💰 Payment Due Details Dashboard")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Outstanding Balance", f"{filtered_df['Balance'].sum():,.2f} OMR")
with m2:
    st.metric("Total Pending Invoices", len(filtered_df))
with m3:
    st.metric("Average Days Overdue", f"{filtered_df['DAYS'].mean():.0f} Days")

st.markdown("---")

# =========================
# VISUALIZATIONS
# =========================
col1, col2 = st.columns(2)

with col1:
    # Donut Chart for Payment Aging
    aging_summary = filtered_df.groupby("Aging Category")["Balance"].sum().reset_index()
    fig_donut = px.pie(
        aging_summary, 
        values="Balance", 
        names="Aging Category", 
        hole=0.5,
        title="Due Amount by Aging Category",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)

with col2:
    # Bar Chart for Outstanding Balance by Salesman
    sales_summary = filtered_df.groupby("Salesman Name")["Balance"].sum().reset_index().sort_values("Balance", ascending=False)