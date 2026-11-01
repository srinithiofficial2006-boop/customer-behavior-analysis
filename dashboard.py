from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Customer Intelligence | Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATHS = [
    BASE_DIR / "outputs" / "cleaned_data.csv",
    BASE_DIR / "outputs" / "cleaned_retail_data.csv",
    BASE_DIR / "cleaned_data.csv",
    BASE_DIR / "data" / "Online Retail.xlsx",
    BASE_DIR / "Online Retail.xlsx",
]

# ---------------------------------------------------------
# PROFESSIONAL DARK NAVY + ELECTRIC BLUE THEME
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #07111F 0%, #0B1730 55%, #101D3A 100%);
        color: #EAF2FF;
    }

    [data-testid="stSidebar"] {
        background: #081225;
        border-right: 1px solid #1E3154;
    }

    [data-testid="stSidebar"] * {
        color: #EAF2FF;
    }

    h1, h2, h3 {
        color: #F3F7FF !important;
        letter-spacing: -0.5px;
    }

    p, label, [data-testid="stCaptionContainer"] {
        color: #A9BAD6;
    }

    .hero {
        padding: 28px 30px;
        border: 1px solid #254A83;
        border-radius: 18px;
        background: linear-gradient(120deg, #10264A, #112B50 55%, #101D38);
        margin-bottom: 24px;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.20);
    }

    .hero-label {
        color: #5BB8FF;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .hero-title {
        color: #FFFFFF;
        font-size: 31px;
        font-weight: 800;
        margin: 8px 0;
    }

    .hero-subtitle {
        color: #B8C9E5;
        font-size: 14px;
        line-height: 1.7;
    }

    .metric-card {
        background: linear-gradient(145deg, #122644, #0D1B33);
        border: 1px solid #233E68;
        border-radius: 15px;
        padding: 19px 20px;
        min-height: 128px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.14);
    }

    .metric-label {
        color: #A8BBD8;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .metric-value {
        color: #FFFFFF;
        font-size: 27px;
        font-weight: 800;
        line-height: 1.2;
    }

    .metric-note {
        color: #57B7FF;
        font-size: 11px;
        margin-top: 9px;
    }

    .section-label {
        color: #57B7FF;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin: 24px 0 12px 0;
    }

    div[data-testid="stPlotlyChart"] {
        background: #0D1A30;
        border: 1px solid #203657;
        border-radius: 14px;
        padding: 8px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #203657;
        border-radius: 12px;
    }

    .insight {
        background: #102442;
        border-left: 4px solid #168BFF;
        padding: 14px 17px;
        border-radius: 8px;
        margin-bottom: 10px;
        color: #DCE9FF;
        font-size: 13px;
        line-height: 1.6;
    }

    .footer {
        border-top: 1px solid #203657;
        margin-top: 30px;
        padding-top: 18px;
        text-align: center;
        color: #7F93B4;
        font-size: 11px;
    }

    .stButton > button, .stDownloadButton > button {
        background: #1677F9;
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 700;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        background: #3694FF;
        color: white;
        border: none;
    }

    div[data-baseweb="select"] > div {
        background-color: #11223D;
        border-color: #2A4268;
    }

    hr {
        border-color: #233957;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------
@st.cache_data(show_spinner="Loading customer transaction data...")
def load_data(file_bytes=None, file_name=None):
    """Load a user-uploaded file or discover a local dataset."""
    if file_bytes is not None:
        name = (file_name or "").lower()
        from io import BytesIO
        source = BytesIO(file_bytes)

        if name.endswith(".csv"):
            df = pd.read_csv(source)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(source)
        else:
            raise ValueError("Upload a CSV or Excel file.")
    else:
        source_path = next(
            (path for path in DATA_PATHS if path.exists()),
            None
        )
        if source_path is None:
            return None

        if source_path.suffix.lower() == ".csv":
            df = pd.read_csv(source_path)
        else:
            df = pd.read_excel(source_path)

    df.columns = [
        str(col).strip().replace(" ", "").lower()
        for col in df.columns
    ]

    # Support common column-name variations.
    aliases = {
        "invoiceno": ["invoice", "invoice_no", "invoicenumber"],
        "stockcode": ["productcode", "itemcode", "stock_code"],
        "description": ["product", "productname", "itemname"],
        "quantity": ["qty", "units"],
        "invoicedate": ["date", "orderdate", "transactiondate"],
        "unitprice": ["price", "unit_price"],
        "customerid": ["customer_id", "customer", "clientid"],
        "country": ["location", "nation"],
    }

    for standard, alternatives in aliases.items():
        if standard not in df.columns:
            for alternative in alternatives:
                if alternative in df.columns:
                    df = df.rename(columns={alternative: standard})
                    break

    required = {"quantity", "unitprice", "invoicedate"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )

    for col in ["invoiceno", "stockcode", "description",
                "customerid", "country"]:
        if col not in df.columns:
            df[col] = "Unknown"

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unitprice"] = pd.to_numeric(df["unitprice"], errors="coerce")
    df["invoicedate"] = pd.to_datetime(
        df["invoicedate"], errors="coerce"
    )

    df = df.dropna(subset=["quantity", "unitprice", "invoicedate"])
    df = df[
        (df["quantity"] > 0) &
        (df["unitprice"] > 0)
    ].copy()

    df["revenue"] = df["quantity"] * df["unitprice"]
    df["country"] = df["country"].fillna("Unknown").astype(str)
    df["description"] = df["description"].fillna("Unknown").astype(str)
    df["invoiceno"] = df["invoiceno"].fillna("Unknown").astype(str)
    df["customerid"] = df["customerid"].fillna("Unknown").astype(str)

    # Cancelled invoices are excluded where identifiable.
    df = df[
        ~df["invoiceno"].str.upper().str.startswith("C")
    ].copy()

    return df


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def money(value):
    return f"£{value:,.2f}"


def metric_card(label, value, note):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


def style_chart(fig, height=350):
    fig.update_layout(
        height=height,
        paper_bgcolor="#0D1A30",
        plot_bgcolor="#0D1A30",
        font=dict(color="#DCE8FA", family="Inter"),
        margin=dict(l=20, r=20, t=45, b=20),
        title_font=dict(size=15, color="#F0F5FF"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#B9CBE5")
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor="#263C5B"
        ),
        yaxis=dict(
            gridcolor="#1C304C",
            zeroline=False
        ),
        hoverlabel=dict(
            bgcolor="#122644",
            font_color="#FFFFFF"
        )
    )
    return fig


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 CustomerIQ")
    st.caption("CUSTOMER INTELLIGENCE PLATFORM")
    st.divider()

    st.markdown("### Data source")
    uploaded_file = st.file_uploader(
        "Upload your retail dataset",
        type=["csv", "xlsx", "xls"],
        help="CSV or Excel file containing customer transactions."
    )

    st.divider()
    st.markdown("### Dashboard sections")
    st.markdown("""
    - Overview
    - Revenue Analytics
    - Product Performance
    - Customer Intelligence
    - Data Explorer
    """)

    st.divider()
    st.caption("PROJECT: CUSTOMER BEHAVIOR ANALYSIS")
    st.caption("Built with Python, Pandas, Plotly & Streamlit")


# ---------------------------------------------------------
# LOAD AND VALIDATE DATA
# ---------------------------------------------------------
try:
    if uploaded_file is not None:
        raw = load_data(
            uploaded_file.getvalue(),
            uploaded_file.name
        )
    else:
        raw = load_data()

except Exception as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.stop()

if raw is None or raw.empty:
    st.markdown("""
    <div class="hero">
        <div class="hero-label">CUSTOMER ANALYTICS</div>
        <div class="hero-title">Customer Intelligence Dashboard</div>
        <div class="hero-subtitle">
            Explore revenue, purchasing patterns, product performance
            and customer behavior in one interactive workspace.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "Dataset not found. Upload your Online Retail dataset using "
        "the sidebar, or place it in the data folder."
    )

    st.code(
        "Customer_Behavior_Analysis/\n"
        "├── dashboard.py\n"
        "└── data/\n"
        "    └── Online Retail.xlsx",
        language="text"
    )
    st.stop()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-label">DATA SCIENCE • BUSINESS INTELLIGENCE</div>
    <div class="hero-title">Customer Intelligence Dashboard</div>
    <div class="hero-subtitle">
        Understand customer purchasing behavior, monitor sales performance,
        discover high-performing products and identify valuable customers.
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔎 Filters")

    min_date = raw["invoicedate"].min().date()
    max_date = raw["invoicedate"].max().date()

    selected_dates = st.date_input(
        "Invoice date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    countries = sorted(raw["country"].dropna().unique().tolist())
    selected_countries = st.multiselect(
        "Country",
        countries,
        default=countries[:min(5, len(countries))]
        if len(countries) > 5 else countries
    )

    product_options = sorted(
        raw["description"].dropna().unique().tolist()
    )
    selected_products = st.multiselect(
        "Products",
        product_options,
        help="Leave empty to include every product."
    )

# Date input can temporarily contain one date while selecting a range.
if isinstance(selected_dates, (tuple, list)):
    start_date = selected_dates[0]
    end_date = selected_dates[-1]
else:
    start_date = selected_dates
    end_date = selected_dates

filtered = raw[
    (raw["invoicedate"].dt.date >= start_date) &
    (raw["invoicedate"].dt.date <= end_date)
].copy()

if selected_countries:
    filtered = filtered[
        filtered["country"].isin(selected_countries)
    ]
else:
    filtered = filtered.iloc[0:0]

if selected_products:
    filtered = filtered[
        filtered["description"].isin(selected_products)
    ]

if filtered.empty:
    st.warning("No transactions match these filters. Change the sidebar filters.")
    st.stop()


# ---------------------------------------------------------
# KEY PERFORMANCE INDICATORS
# ---------------------------------------------------------
total_revenue = filtered["revenue"].sum()
total_orders = filtered["invoiceno"].nunique()
known_customers = filtered.loc[
    filtered["customerid"] != "Unknown", "customerid"
].nunique()
avg_order_value = (
    total_revenue / total_orders if total_orders else 0
)
units_sold = filtered["quantity"].sum()

st.markdown('<div class="section-label">BUSINESS OVERVIEW</div>',
            unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    metric_card("TOTAL REVENUE", money(total_revenue), "Filtered sales value")
with c2:
    metric_card("TOTAL ORDERS", f"{total_orders:,}", "Unique invoices")
with c3:
    metric_card("KNOWN CUSTOMERS", f"{known_customers:,}", "Unique customer IDs")
with c4:
    metric_card("AVG. ORDER VALUE", money(avg_order_value), "Revenue ÷ orders")
with c5:
    metric_card("UNITS SOLD", f"{units_sold:,.0f}", "Positive quantities")

st.caption(
    f"Showing {len(filtered):,} transaction rows from "
    f"{start_date} to {end_date}."
)


# ---------------------------------------------------------
# REVENUE ANALYTICS
# ---------------------------------------------------------
st.markdown('<div class="section-label">01 / REVENUE ANALYTICS</div>',
            unsafe_allow_html=True)

left, right = st.columns([1.65, 1])

with left:
    daily = (
        filtered.set_index("invoicedate")
        .resample("D")["revenue"]
        .sum()
        .reset_index()
    )

    fig = px.area(
        daily,
        x="invoicedate",
        y="revenue",
        title="Revenue Trend Over Time",
        labels={
            "invoicedate": "Date",
            "revenue": "Revenue (£)"
        }
    )
    fig.update_traces(
        line=dict(color="#168BFF", width=2.5),
        fillcolor="rgba(22,139,255,0.18)"
    )
    st.plotly_chart(style_chart(fig, 390), use_container_width=True)

with right:
    weekday = filtered.copy()
    weekday["day"] = weekday["invoicedate"].dt.day_name()
    weekday["day_number"] = weekday["invoicedate"].dt.dayofweek

    weekday_sales = (
        weekday.groupby(["day", "day_number"], as_index=False)["revenue"]
        .sum()
        .sort_values("day_number")
    )

    fig = px.bar(
        weekday_sales,
        x="day",
        y="revenue",
        title="Sales by Day of Week",
        labels={"day": "Weekday", "revenue": "Revenue (£)"}
    )
    fig.update_traces(marker_color="#39B8FF")
    st.plotly_chart(style_chart(fig, 390), use_container_width=True)


# ---------------------------------------------------------
# PRODUCT PERFORMANCE
# ---------------------------------------------------------
st.markdown('<div class="section-label">02 / PRODUCT PERFORMANCE</div>',
            unsafe_allow_html=True)

p1, p2 = st.columns([1.4, 1])

with p1:
    top_products = (
        filtered.groupby("description", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            units=("quantity", "sum")
        )
        .nlargest(10, "revenue")
        .sort_values("revenue")
    )

    fig = px.bar(
        top_products,
        x="revenue",
        y="description",
        orientation="h",
        title="Top 10 Products by Revenue",
        labels={
            "revenue": "Revenue (£)",
            "description": "Product"
        },
        hover_data={"units": True}
    )
    fig.update_traces(marker_color="#1677F9")
    st.plotly_chart(style_chart(fig, 430), use_container_width=True)

with p2:
    country_sales = (
        filtered.groupby("country", as_index=False)["revenue"]
        .sum()
        .nlargest(10, "revenue")
        .sort_values("revenue", ascending=False)
    )

    fig = px.pie(
        country_sales,
        names="country",
        values="revenue",
        hole=0.60,
        title="Revenue Share by Country"
    )
    fig.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(style_chart(fig, 430), use_container_width=True)


# ---------------------------------------------------------
# CUSTOMER INTELLIGENCE & RFM SEGMENTATION
# ---------------------------------------------------------
st.markdown('<div class="section-label">03 / CUSTOMER INTELLIGENCE</div>',
            unsafe_allow_html=True)

customer_data = filtered[
    filtered["customerid"] != "Unknown"
].copy()

if customer_data.empty:
    st.info(
        "Customer IDs are unavailable in the filtered data. "
        "Customer-level RFM analysis cannot be calculated."
    )
else:
    snapshot_date = (
        customer_data["invoicedate"].max().normalize()
        + pd.Timedelta(days=1)
    )

    rfm = customer_data.groupby("customerid").agg(
        Recency=("invoicedate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("invoiceno", "nunique"),
        Monetary=("revenue", "sum")
    ).reset_index()

    col1, col2 = st.columns([1.2, 1])

    with col1:
        fig = px.scatter(
            rfm,
            x="Frequency",
            y="Monetary",
            size="Monetary",
            color="Recency",
            hover_name="customerid",
            title="Customer Purchase Behavior",
            labels={
                "Frequency": "Number of Orders",
                "Monetary": "Customer Revenue (£)",
                "Recency": "Days Since Last Purchase"
            },
            color_continuous_scale="Blues"
        )
        st.plotly_chart(style_chart(fig, 420), use_container_width=True)

    with col2:
        # Optional unsupervised ML: K-Means on RFM features.
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler

            if len(rfm) >= 4:
                features = rfm[["Recency", "Frequency", "Monetary"]].copy()
                features["Monetary"] = np.log1p(
                    features["Monetary"].clip(lower=0)
                )

                scaler = StandardScaler()
                scaled = scaler.fit_transform(features)

                n_clusters = min(4, len(rfm))
                model = KMeans(
                    n_clusters=n_clusters,
                    random_state=42,
                    n_init=10
                )
                rfm["Cluster"] = model.fit_predict(scaled).astype(str)

                fig = px.scatter(
                    rfm,
                    x="Frequency",
                    y="Monetary",
                    color="Cluster",
                    hover_name="customerid",
                    title="Machine Learning: Customer Clusters",
                    labels={
                        "Frequency": "Number of Orders",
                        "Monetary": "Customer Revenue (£)",
                        "Cluster": "ML Cluster"
                    },
                    color_discrete_sequence=[
                        "#168BFF", "#41D9FF", "#8B7CFF", "#FFB86B"
                    ]
                )
                st.plotly_chart(
                    style_chart(fig, 420),
                    use_container_width=True
                )
            else:
                st.info("At least four known customers are needed for clustering.")

        except ImportError:
            st.info(
                "Install scikit-learn to enable K-Means customer segmentation."
            )
        except Exception as exc:
            st.warning(f"Customer clustering could not run: {exc}")

    st.markdown("#### RFM Customer Summary")

    rfm_summary = rfm[["Recency", "Frequency", "Monetary"]].describe().T
    rfm_summary.index = ["Days Since Last Order", "Number of Orders", "Total Spend (£)"]
    st.dataframe(
        rfm_summary.round(2),
        use_container_width=True
    )

    st.caption(
        "RFM = Recency (how recently a customer purchased), "
        "Frequency (how often they purchased), and Monetary (how much they spent). "
        "K-Means is an unsupervised learning method; cluster numbers are not rankings."
    )


# ---------------------------------------------------------
# AUTOMATIC BUSINESS INSIGHTS
# ---------------------------------------------------------
st.markdown('<div class="section-label">04 / BUSINESS INSIGHTS</div>',
            unsafe_allow_html=True)

best_product = (
    filtered.groupby("description")["revenue"].sum().idxmax()
)
best_product_revenue = (
    filtered.groupby("description")["revenue"].sum().max()
)

best_country = (
    filtered.groupby("country")["revenue"].sum().idxmax()
)
best_country_revenue = (
    filtered.groupby("country")["revenue"].sum().max()
)

daily_totals = (
    filtered.groupby(filtered["invoicedate"].dt.date)["revenue"].sum()
)
best_day = daily_totals.idxmax() if not daily_totals.empty else None

i1, i2 = st.columns(2)

with i1:
    st.markdown(
        f'<div class="insight"><b>Top revenue product</b><br>'
        f'{best_product} generated {money(best_product_revenue)} '
        f'in revenue for the selected filters.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="insight"><b>Leading country</b><br>'
        f'{best_country} contributed {money(best_country_revenue)} '
        f'in revenue.</div>',
        unsafe_allow_html=True
    )

with i2:
    st.markdown(
        f'<div class="insight"><b>Average order value</b><br>'
        f'Each invoice generated an average of '
        f'{money(avg_order_value)}.</div>',
        unsafe_allow_html=True
    )

    if best_day is not None:
        st.markdown(
            f'<div class="insight"><b>Best sales day</b><br>'
            f'{best_day} recorded the highest daily revenue '
            f'within the selected period.</div>',
            unsafe_allow_html=True
        )


# ---------------------------------------------------------
# DATA EXPLORER & EXPORT
# ---------------------------------------------------------
st.markdown('<div class="section-label">05 / DATA EXPLORER</div>',
            unsafe_allow_html=True)

search_text = st.text_input(
    "Search product, customer, invoice or country",
    placeholder="Type a keyword..."
)

table_data = filtered.copy()
if search_text.strip():
    term = search_text.strip().lower()
    search_cols = [
        "description", "customerid", "invoiceno",
        "country", "stockcode"
    ]
    mask = pd.Series(False, index=table_data.index)
    for col in search_cols:
        if col in table_data.columns:
            mask |= table_data[col].astype(str).str.lower().str.contains(
                term, na=False, regex=False
            )
    table_data = table_data[mask]

display_cols = [
    col for col in [
        "invoiceno", "invoicedate", "customerid",
        "description", "quantity", "unitprice",
        "revenue", "country"
    ]
    if col in table_data.columns
]

st.dataframe(
    table_data[display_cols].sort_values(
        "invoicedate", ascending=False
    ),
    use_container_width=True,
    height=350,
    hide_index=True
)

csv_data = table_data[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download filtered data as CSV",
    data=csv_data,
    file_name="customer_behavior_analysis.csv",
    mime="text/csv"
)

st.markdown("""
<div class="footer">
    CUSTOMER INTELLIGENCE DASHBOARD · DATA SCIENCE INTERNSHIP PROJECT<br>
    Built with Python · Pandas · Plotly · Streamlit · Scikit-learn
</div>
""", unsafe_allow_html=True)