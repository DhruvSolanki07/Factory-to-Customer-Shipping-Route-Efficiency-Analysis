import streamlit as st
import pandas as pd
import plotly.express as px
from src.data import load_data, build_analytics, FACTORY_COORDS, STATE_ABBR

st.set_page_config(page_title="NassauLogix | Shipping Intelligence", page_icon="🚚", layout="wide")
st.title("🚚 NassauLogix")
st.caption("Factory-to-Customer Shipping Route Efficiency & Logistics Intelligence")

@st.cache_data
def get_data():
    return load_data("data/Nassau Candy Distributor.csv")

df, quality = get_data()
if df.empty:
    st.error("No data could be loaded. Check the CSV path and column names.")
    st.stop()

st.sidebar.header("Dashboard Filters")
min_date, max_date = df["Order Date"].min(), df["Order Date"].max()
date_range = st.sidebar.date_input("Order date range", value=(min_date.date(), max_date.date()))
regions = st.sidebar.multiselect("Region", sorted(df["Region"].dropna().unique()), default=sorted(df["Region"].dropna().unique()))
states = st.sidebar.multiselect("State", sorted(df["State/Province"].dropna().unique()))
modes = st.sidebar.multiselect("Ship mode", sorted(df["Ship Mode"].dropna().unique()), default=sorted(df["Ship Mode"].dropna().unique()))
threshold = st.sidebar.slider("Delay threshold (days)", 1, 30, 7)
valid_only = st.sidebar.checkbox("Exclude invalid / unverified lead times", value=False)

st.sidebar.divider()
st.sidebar.subheader("Research Documentation")
try:
    with open("reports/research_paper.pdf", "rb") as _f_pdf:
        _pdf_bytes = _f_pdf.read()
    st.sidebar.download_button(
        "📥 Download Research Paper (PDF)",
        data=_pdf_bytes,
        file_name="NassauLogix_Research_Paper.pdf",
        mime="application/pdf",
        use_container_width=True
    )
except Exception:
    pass

try:
    with open("reports/research_paper.html", "r", encoding="utf-8") as _f_html:
        _paper_html = _f_html.read()
    st.sidebar.download_button(
        "🌐 Download Research Paper (HTML)",
        data=_paper_html,
        file_name="NassauLogix_Research_Paper.html",
        mime="text/html",
        use_container_width=True
    )
except Exception:
    pass

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    filtered = df[df["Order Date"].between(start, end)]
else:
    filtered = df.copy()
if regions:
    filtered = filtered[filtered["Region"].isin(regions)]
if states:
    filtered = filtered[filtered["State/Province"].isin(states)]
if modes:
    filtered = filtered[filtered["Ship Mode"].isin(modes)]
if valid_only:
    filtered = filtered[filtered["Lead Time Validated"]]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

analytics = build_analytics(filtered, threshold)
valid = filtered[filtered["Lead Time Validated"]]
invalid_count = int((~filtered["Lead Time Validated"]).sum())

if quality["date_warning"]:
    st.warning(
        f"DATA QUALITY WARNING: {quality['date_warning']} "
        "The supplied dates currently imply unusually long shipping durations. "
        "Do not interpret lead-time KPIs as operational truth until the source dates are verified."
    )

c1,c2,c3,c4 = st.columns(4)
c1.metric("Order lines", f"{len(filtered):,}")
c2.metric("Unique orders", f"{filtered['Order ID'].nunique():,}")
c3.metric("Unique customers", f"{filtered['Customer ID'].nunique():,}")
c4.metric("Unverified lead-time rows", f"{invalid_count:,}")

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "Executive Overview","Route Efficiency","Geographic Analysis",
    "Ship Mode Analysis","Shipment Drill-Down","Data Quality"
])

with tab1:
    st.subheader("Executive overview")
    if len(valid):
        a,b,c = st.columns(3)
        a.metric("Average lead time (validated)", f"{valid['Shipping Lead Time'].mean():.1f} days")
        b.metric("Median lead time (validated)", f"{valid['Shipping Lead Time'].median():.1f} days")
        c.metric("Delay rate (validated)", f"{(valid['Shipping Lead Time'] > threshold).mean()*100:.1f}%")
    else:
        st.info("No validated lead-time rows are available. Verify the date source before interpreting delivery KPIs.")
    left,right = st.columns(2)
    with left:
        volume = filtered.groupby("Ship Mode")["Order ID"].nunique().reset_index(name="Orders")
        fig = px.bar(volume, x="Ship Mode", y="Orders", title="Unique orders by shipping mode", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        reg = filtered.groupby("Region")["Order ID"].nunique().reset_index(name="Orders")
        fig = px.pie(reg, names="Region", values="Orders", title="Order mix by customer region", hole=.45)
        st.plotly_chart(fig, use_container_width=True)
    monthly = filtered.assign(OrderMonth=filtered["Order Date"].dt.to_period("M").astype(str)).groupby("OrderMonth")["Order ID"].nunique().reset_index(name="Orders")
    st.plotly_chart(px.line(monthly, x="OrderMonth", y="Orders", markers=True, title="Monthly order volume"), use_container_width=True)

with tab2:
    st.subheader("Factory-to-customer route leaderboard")
    route = analytics["routes"]
    if route.empty:
        st.info("No route records available.")
    else:
        st.caption("Route volume counts distinct Order IDs, not product rows. Lead-time measures use validated records only.")
        st.dataframe(route, use_container_width=True, hide_index=True)
        if len(route):
            chart = route.sort_values("Average Lead Time")
            st.plotly_chart(px.bar(chart.head(15), x="Route", y="Average Lead Time", color="Factory",
                                   hover_data=["Orders","Lead Time Std Dev","Delay Frequency (%)"],
                                   title="Fastest 15 routes (validated records)"), use_container_width=True)
            slow = route.sort_values("Average Lead Time", ascending=False).head(10)
            st.plotly_chart(px.bar(slow, x="Route", y="Average Lead Time", color="Factory",
                                   title="Slowest 10 routes (validated records)"), use_container_width=True)

with tab3:
    st.subheader("Geographic shipping analysis")
    state = analytics["states"]
    if not state.empty:
        st.dataframe(state, use_container_width=True, hide_index=True)
        map_df = state.copy()
        map_df["State Code"] = map_df["State"].map(STATE_ABBR)
        map_df = map_df.dropna(subset=["State Code"])
        if not map_df.empty:
            fig = px.choropleth(map_df, locations="State Code", locationmode="USA-states",
                                color="Average Lead Time", scope="usa",
                                hover_name="State", hover_data=["Orders","Delay Frequency (%)"],
                                color_continuous_scale="Reds", title="Average validated lead time by state")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("State map unavailable for the state names in this file; use the state table above.")
    else:
        st.info("No validated geographic lead-time data to map.")
    region = analytics["regions"]
    if not region.empty:
        st.plotly_chart(px.bar(region, x="Region", y="Orders", color="Average Lead Time",
                               title="Regional order volume and average lead time"), use_container_width=True)
    else:
        st.info("No validated regional lead-time data to display.")

with tab4:
    st.subheader("Shipping mode comparison")
    mode = analytics["modes"]
    st.dataframe(mode, use_container_width=True, hide_index=True)
    if not mode.empty and mode["Average Lead Time"].notna().any():
        st.plotly_chart(px.bar(mode, x="Ship Mode", y="Average Lead Time", color="Ship Mode",
                               title="Average validated lead time by ship mode"), use_container_width=True)
    cost_mode = filtered.groupby("Ship Mode").agg(
        Orders=("Order ID","nunique"), Sales=("Sales","sum"),
        Gross_Profit=("Gross Profit","sum"), Cost=("Cost","sum")
    ).reset_index()
    st.dataframe(cost_mode, use_container_width=True, hide_index=True)
    st.caption("Sales, cost and gross profit are descriptive financial measures, not necessarily freight/shipping charges.")

with tab5:
    st.subheader("Order-level shipment drill-down")
    order_ids = sorted(filtered["Order ID"].dropna().unique())
    selected = st.selectbox("Select an order", order_ids)
    detail = filtered[filtered["Order ID"] == selected].copy()
    cols = ["Order ID","Order Date","Ship Date","Shipping Lead Time","Lead Time Validated",
            "Ship Mode","Customer ID","City","State/Province","Region","Factory","Product Name","Units","Sales"]
    st.dataframe(detail[cols], use_container_width=True, hide_index=True)
    first = detail.iloc[0]
    st.write(f"**Customer location:** {first['City']}, {first['State/Province']} · **Factory:** {first['Factory']}")
    st.write(f"**Order date:** {first['Order Date'].date()} · **Ship date:** {first['Ship Date'].date()}")

with tab6:
    st.subheader("Data quality and validation")
    q1,q2,q3 = st.columns(3)
    q1.metric("Missing values", f"{int(df.isna().sum().sum()):,}")
    q2.metric("Negative lead times", f"{int((df['Shipping Lead Time'] < 0).sum()):,}")
    q3.metric("Unverified lead times", f"{int((~df['Lead Time Validated']).sum()):,}")
    st.write("**Date range and lead-time profile**")
    st.json(quality)
    st.write("**Rows requiring source-date review**")
    st.dataframe(filtered.loc[~filtered["Lead Time Validated"],
        ["Order ID","Order Date","Ship Date","Shipping Lead Time","Ship Mode","State/Province"]].head(100),
        use_container_width=True, hide_index=True)
    st.download_button("Download filtered data as CSV", filtered.to_csv(index=False).encode("utf-8"),
                       "nassaulogix_filtered_data.csv", "text/csv")

st.caption("NassauLogix · Analytics prototype. Confirm source date semantics and factory mapping before operational use.")
