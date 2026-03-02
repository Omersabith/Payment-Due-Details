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
        # 1. Use 'utf-8-sig' to remove BOM hidden characters
        # 2. sep=None with engine='python' tells pandas to guess the delimiter (tab or comma)
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
    except FileNotFoundError:
        st.error(f"Error: '{file_path}' not found. Please ensure it is in your GitHub repository.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading the file: {e}")
        return pd.DataFrame()

    # Clean column names: Remove spaces and convert to UPPERCASE for consistency
    df.columns = df.columns.str.strip().str.upper()

    # Diagnostic check: If 'DATE' is missing, show the user what columns WERE found
    expected_cols = ["DATE", "BALANCE", "DAYS", "SALESMAN NAME", "CUSTOMER NAME"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing columns in CSV: {', '.join(missing_cols)}")
        st.write("Found columns:", list(df.columns))
        st.stop()

    # Convert Date column
    df["DATE"] = pd.to_datetime(df["DATE"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["DATE"])

    # Ensure numeric types
    df["BALANCE"] = pd.to_numeric(df["BALANCE"], errors="coerce").fillna(0)
    df["DAYS"] = pd.to_numeric(df["DAYS"], errors="coerce").fillna(0)

    # Aging Categorization
    def categorize_aging(days):
        if days <= 30: return "0-30 Days"
        elif days <= 60: return "31-60 Days"
        elif days <= 90: return "61-90 Days"
        else: return "90+ Days"
    
    df["AGING CATEGORY"] = df["DAYS"].apply(categorize_aging)
    
    return df

df = load_data()

if df.empty:
    st.stop()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔍 Filters")

# Salesman Filter
salesman_options = sorted(df["SALESMAN NAME"].unique().tolist())
selected_salesman = st.sidebar.multiselect("Select Salesman", salesman_options, default=salesman_options)

# Customer Filter
customer_options = sorted(df[df["SALESMAN NAME"].isin(selected_salesman)]["CUSTOMER NAME"].unique().tolist())
selected_customer = st.sidebar.multiselect("Select Customer", customer_options, default=customer_options)

# Apply Filters
mask = (df["SALESMAN NAME"].isin(selected_salesman)) & (df["CUSTOMER NAME"].isin(selected_customer))
filtered_df = df[mask]

# =========================
# KPI METRICS
# =========================
st.title("💰 Payment Due Details Dashboard")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Outstanding", f"{filtered_df['BALANCE'].sum():,.2f} OMR")
with m2:
    st.metric("Pending Invoices", len(filtered_df))
with m3:
    st.metric("Avg. Days Overdue", f"{filtered_df['DAYS'].mean():.0f} Days")

st.markdown("---")

# =========================
# VISUALIZATIONS
# =========================
col1, col2 = st.columns(2)

with col1:
    # Donut Chart for Aging
    aging_summary = filtered_df.groupby("AGING CATEGORY")["BALANCE"].sum().reset_index()
    fig_donut = px.pie(
        aging_summary, 
        values="BALANCE", 
        names="AGING CATEGORY", 
        hole=0.5,
        title="Due Amount by Aging Category",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col2:
    # Bar Chart for Salesman
    sales_summary = filtered_df.groupby("SALESMAN NAME")["BALANCE"].sum().reset_index().sort_values("BALANCE", ascending=False)
    fig_bar = px.bar(
        sales_summary,
        x="SALESMAN NAME",
        y="BALANCE",
        title="Balance per Salesman",
        color="BALANCE",
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Trend Line
st.markdown("---")
st.subheader("📅 Payment Due Trend")
trend_data = filtered_df.sort_values("DATE").groupby("DATE")["BALANCE"].sum().reset_index()
fig_trend = px.line(trend_data, x="DATE", y="BALANCE", markers=True)
st.plotly_chart(fig_trend, use_container_width=True)

# Detailed Table
st.markdown("---")
st.subheader("📋 Invoice Details")
st.dataframe(
    filtered_df[["DATE", "INVOICE NO", "CUSTOMER NAME", "BALANCE", "DAYS", "SALESMAN NAME"]], 
    use_container_width=True,
    hide_index=True
)