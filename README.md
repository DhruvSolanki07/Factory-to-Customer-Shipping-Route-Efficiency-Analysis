# NassauLogix — Factory-to-Customer Shipping Route Analytics

A Streamlit analytics application for understanding factory-to-customer shipping patterns for Nassau Candy Distributor.

## Features
- Executive KPI overview
- Factory-to-state route leaderboard
- State and regional shipping analysis
- Ship-mode comparison
- Order-level shipment drill-down
- Data-quality validation and filtered CSV export
- Product-to-factory mapping based on the supplied project specification

## Dataset
Place `Nassau Candy Distributor.csv` inside `data/`. The supplied copy is already included.

## Important data caveat
The source data currently contains Order Dates from 2024–2025 and Ship Dates from 2026–2030. The calculated durations are 904–1,642 days. The app flags durations outside 0–365 days as unverified and excludes them from operational lead-time summaries by default. This is a conservative validation rule, not proof that those dates are wrong. Confirm source date semantics with the dataset owner before changing dates or publishing delivery-performance claims.

The dataset contains order-product rows, not necessarily one row per shipment. Shipment volume therefore uses distinct Order IDs. The supplied factory-to-product relationship is used to infer factory location; validate that relationship before operational deployment.

## Setup (Windows PowerShell)
```powershell
cd NassauLogix
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the EDA script
```powershell
python run_eda.py
```

## Project structure
```text
NassauLogix/
├── app.py
├── run_eda.py
├── requirements.txt
├── README.md
├── data/
│   └── Nassau Candy Distributor.csv
├── src/
│   ├── __init__.py
│   └── data.py
└── reports/
    └── research_paper_outline.md
```

## KPI definitions
- Shipping Lead Time = Ship Date − Order Date (calendar days)
- Route Volume = distinct Order IDs per factory-to-state route
- Delay Frequency = percentage of validated distinct orders whose lead time exceeds the selected threshold
- Efficiency Score = min-max normalized route lead-time score; higher is faster within the selected filtered dataset

## Limitations
- No actual freight charge or transport distance is supplied.
- Sales, Cost and Gross Profit are not shipping costs.
- The factory coordinates are supplied project inputs; they should be verified.
- The current app does not claim to optimize a real carrier route or calculate road-network travel distance.
- The optional predictive model should only be trained after the target date/label has been validated and sufficient examples exist.

## Recommended extensions
1. Add SQL database storage and queries.
2. Add US factory-to-state route lines with verified state centroids.
3. Add a delay prediction model after fixing/validating source dates.
4. Add PDF executive reporting.
5. Add role-based access and deployment.
