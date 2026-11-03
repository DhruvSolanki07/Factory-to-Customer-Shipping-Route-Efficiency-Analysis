import pandas as pd

FACTORY_BY_PRODUCT = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory",
}

FACTORY_COORDS = {
    "Lot's O' Nuts": (32.881893, -111.768036),
    "Wicked Choccy's": (32.076176, -81.088371),
    "Sugar Shack": (48.119140, -96.181150),
    "Secret Factory": (41.446333, -90.565487),
    "The Other Factory": (35.117500, -89.971107),
}

STATE_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC",
    "Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL",
    "Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
    "Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN",
    "Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR",
    "Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA",
    "Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY",
    "Ontario":"ON","Quebec":"QC","British Columbia":"BC","Alberta":"AB"
}

def load_data(path):
    df = pd.read_csv(path)
    required = ["Order ID","Order Date","Ship Date","Ship Mode","Customer ID",
                "City","State/Province","Region","Product Name","Sales","Units","Gross Profit","Cost"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # The source appears to use DD-MM-YYYY. Explicit parsing avoids locale ambiguity.
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y", errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y", errors="coerce")
    df["Shipping Lead Time"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Factory"] = df["Product Name"].map(FACTORY_BY_PRODUCT)
    df["Factory Latitude"] = df["Factory"].map(lambda x: FACTORY_COORDS.get(x, (None,None))[0])
    df["Factory Longitude"] = df["Factory"].map(lambda x: FACTORY_COORDS.get(x, (None,None))[1])
    df["Lead Time Validated"] = (
        df["Shipping Lead Time"].notna()
        & df["Shipping Lead Time"].between(0, 365)
        & df["Order Date"].notna()
        & df["Ship Date"].notna()
    )
    df["Route"] = df["Factory"].fillna("Unknown Factory") + " → " + df["State/Province"].fillna("Unknown State")
    df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)

    lead = df["Shipping Lead Time"].dropna()
    warning = None
    if len(lead) and (lead > 365).mean() > 0.5:
        warning = f"{(lead > 365).sum():,} of {len(lead):,} rows have lead times over 365 days."
    elif len(lead) and (lead < 0).any():
        warning = f"{(lead < 0).sum():,} rows have negative lead times."
    quality = {
        "rows": int(len(df)),
        "unique_orders": int(df["Order ID"].nunique()),
        "order_date_min": str(df["Order Date"].min()),
        "order_date_max": str(df["Order Date"].max()),
        "ship_date_min": str(df["Ship Date"].min()),
        "ship_date_max": str(df["Ship Date"].max()),
        "lead_time_min_days": None if lead.empty else int(lead.min()),
        "lead_time_median_days": None if lead.empty else float(lead.median()),
        "lead_time_max_days": None if lead.empty else int(lead.max()),
        "unmapped_products": sorted(df.loc[df["Factory"].isna(),"Product Name"].dropna().unique().tolist()),
        "date_warning": warning
    }
    return df, quality

def build_analytics(df, delay_threshold=7):
    valid = df[df["Lead Time Validated"]].copy()

    def summarize(group_col):
        cols = [group_col, "Orders", "Delay Frequency (%)", "Average Lead Time", "Median Lead Time", "Lead Time Std Dev"]
        if valid.empty:
            return pd.DataFrame(columns=cols)
        out = valid.groupby(group_col).agg(
            Orders=("Order ID","nunique"),
            Average_Lead_Time=("Shipping Lead Time","mean"),
            Median_Lead_Time=("Shipping Lead Time","median"),
            Lead_Time_Std_Dev=("Shipping Lead Time","std"),
            Delayed_Orders=("Order ID", lambda s: s[valid.loc[s.index,"Shipping Lead Time"] > delay_threshold].nunique())
        ).reset_index()
        out["Delay Frequency (%)"] = (out["Delayed_Orders"] / out["Orders"] * 100).round(2)
        out["Average Lead Time"] = out.pop("Average_Lead_Time").round(2)
        out["Median Lead Time"] = out.pop("Median_Lead_Time").round(2)
        out["Lead Time Std Dev"] = out.pop("Lead_Time_Std_Dev").round(2)
        out = out.drop(columns=["Delayed_Orders"])
        return out

    routes = summarize("Route")
    if not routes.empty:
        routes["Factory"] = routes["Route"].str.split(" → ").str[0]
        routes["Efficiency Score"] = (
            100 * (routes["Average Lead Time"].max() - routes["Average Lead Time"])
            / max(routes["Average Lead Time"].max() - routes["Average Lead Time"].min(), 1e-9)
        ).round(1)
        routes = routes.sort_values(["Average Lead Time","Orders"])
    states = summarize("State/Province").rename(columns={"State/Province":"State"})
    regions = summarize("Region").rename(columns={"Region":"Region"})
    modes = summarize("Ship Mode").rename(columns={"Ship Mode":"Ship Mode"})
    return {"routes": routes, "states": states, "regions": regions, "modes": modes}
