# Research Paper Outline

## Suggested title
Factory-to-Customer Shipping Route Efficiency Analysis for Nassau Candy Distributor

## Abstract
Describe the logistics problem, dataset, analytical approach, key findings (only after validating dates), and recommendations.

## 1. Introduction
- National distribution context
- Importance of delivery reliability
- Project objectives and research questions

## 2. Dataset Description
- 10,194 source rows and 18 columns
- 8,549 distinct Order IDs
- Product, customer, geography, sales and shipment fields
- Factory-to-product mapping supplied separately

## 3. Data Preparation
- Explicit DD-MM-YYYY date parsing
- Duplicate and missing-value checks
- Distinguish order-product rows from unique orders
- Infer factory from product mapping
- Validate shipment lead time and document anomalies

## 4. Feature Engineering
- Shipping Lead Time
- Factory-to-State Route
- Factory-to-Region Route
- Order month
- Delay indicator using a clearly stated threshold

## 5. Exploratory Data Analysis
- Order volume over time
- Ship-mode mix
- Regional and state-level order distribution
- Factory and product distribution
- Sales and gross-profit summaries

## 6. Route Efficiency Analysis
- Distinct order count per route
- Mean, median and standard deviation of validated lead time
- Delay frequency
- Route efficiency score
- Top and bottom routes, only where enough valid records exist

## 7. Geographic Bottleneck Analysis
- High-volume / high-delay states
- Regional comparisons
- Map-based interpretation and limitations

## 8. Ship Mode Comparison
- Lead-time distribution by mode
- Volume by mode
- Descriptive sales and profit comparisons
- Explain that freight costs are unavailable, so true shipping cost-time trade-offs cannot be established

## 9. Recommendations
- Prioritize high-volume routes with verified delays
- Investigate factory assignment and fulfilment processes
- Review ship-mode allocation
- Improve shipment event data quality
- Establish route-level monitoring

## 10. Limitations and Future Scope
- Date anomalies
- No carrier, tracking scan, freight charge, road distance or traffic fields
- Add validated geospatial data and delay prediction in future work

## 11. Conclusion
Summarize validated findings and operational implications.

## Suggested figures
1. Data processing workflow
2. Order volume by month
3. Ship mode distribution
4. Orders by region
5. Route leaderboard
6. US state-level lead-time map
7. Lead-time distribution by ship mode
8. High-volume / high-delay state matrix
