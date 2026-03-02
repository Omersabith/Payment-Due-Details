import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(layout="wide", page_title="Payment Due Dashboard", page_icon="💰")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    file_path = "MasterData.csv"
    try:
        # Using 'utf-8-sig' to handle Byte Order Mark (BOM)
        # sep=None allows pandas to automatically detect delimiter
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
    except FileNotFoundError:
        st.error(f"Error: '{file_path}' not found in the repository.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()

    # Clean column names
    df.columns = df.columns.str.strip().str.upper()

    # Data Type Conversion
    df["DATE"] = pd.to_datetime(df["DATE"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["DATE"])
    df["BALANCE"] = pd.to_numeric(df["BALANCE"], errors="coerce").fillna(0)
    df["DAYS"] = pd.to_numeric(df["DAYS"], errors="coerce").fillna(0)

    # Define Aging Categories
    def categorize_aging(days):
        if days <= 60: 
            return "Below 60"
        elif days <= 90: 
            return "61-90"
        elif days <= 120: 
            return "91-120"
        elif days <= 180: 
            return "121-180"
        else: 
            return "Above 180"
    
    df["AGING CATEGORY"] = df["DAYS"].apply(categorize_aging)
    
    # Define logical order for categories
    category_order = ["Below 60", "61-90", "91-120", "121-180", "Above 180"]
    df["AGING CATEGORY"] = pd.Categorical(df["AGING CATEGORY"], categories=category_order, ordered=True)
    
    return df

df = load_data()

if df.empty:
    st.stop()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔍 Quick Analysis Filters")

# 1. Aging Category Filter (Added for quick analysis)
aging_list = ["Below 60", "61-90", "91-120", "121-180", "Above 180"]
selected_aging = st.sidebar.multiselect("Select Aging Category", aging_list, default=aging_list)

# 2. Salesman Filter
salesman_list = sorted(df["SALESMAN NAME"].unique().tolist())
selected_salesman = st.sidebar.multiselect("Select Salesman", salesman_list, default=salesman_list)

# 3. Customer Filter
customer_list = sorted(df[df["SALESMAN NAME"].isin(selected_salesman)]["CUSTOMER NAME"].unique().tolist())
selected_customer = st.sidebar.multiselect("Select Customer", customer_list, default=customer_list)

# Apply All Filters
mask = (
    (df["AGING CATEGORY"].isin(selected_aging)) & 
    (df["SALESMAN NAME"].isin(selected_salesman)) & 
    (df["CUSTOMER NAME"].isin(selected_customer))
)
filtered_df = df[mask]

# =========================
# MAIN DASHBOARD
# =========================
st.title("💰 Payment Due Details Dashboard")

# Top Level Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Total Outstanding", f"{filtered_df['BALANCE'].sum():,.2f} OMR")
m2.metric("Total Invoices", len(filtered_df))
m3.metric("Avg Days Overdue", f"{filtered_df['DAYS'].mean():.0f} Days" if not filtered_df.empty else "0 Days")

st.markdown("---")

# Visualizations Row
c1, c2 = st.columns(2)

with c1:
    # Donut Chart for Aging Categories
    aging_summary = filtered_df.groupby("AGING CATEGORY", observed=False)["BALANCE"].sum().reset_index()
    fig_donut = px.pie(
        aging_summary, 
        values="BALANCE", 
        names="AGING CATEGORY", 
        hole=0.5,
        title="Due Amount Distribution",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)

with c2:
    # Bar Chart for Outstanding Balance by Salesman
    sales_summary = filtered_df.groupby("SALESMAN NAME")["BALANCE"].sum().reset_index().sort_values("BALANCE", ascending=False)
    fig_bar = px.bar(
        sales_summary,
        x="SALESMAN NAME",
        y="BALANCE",
        title="Outstanding Balance by Salesman",
        color="BALANCE",
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Trend Line
st.markdown("---")
st.subheader("📅 Payment Due Trend")
if not filtered_df.empty:
    trend_df = filtered_df.sort_values("DATE").groupby("DATE")["BALANCE"].sum().reset_index()
    fig_trend = px.line(trend_df, x="DATE", y="BALANCE", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# Data Table
st.markdown("---")
st.subheader("📋 Detailed Invoice Records")
st.dataframe(
    filtered_df[["DATE", "INVOICE NO", "CUSTOMER NAME", "BALANCE", "DAYS", "SALESMAN NAME", "AGING CATEGORY"]], 
    use_container_width=True,
    hide_index=True
)