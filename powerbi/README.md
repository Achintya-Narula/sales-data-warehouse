# Power BI Layer

Connect Power BI to `rpt.vwSalesDetail` or the `dw` star schema. Prefer the star schema for a semantic model and use single-direction relationships from dimensions to `FactSales`.

## Suggested measures

```DAX
Total Revenue = SUM(FactSales[NetAmount])

Total Units = SUM(FactSales[Quantity])

Sales Lines = DISTINCTCOUNT(FactSales[SaleID])

Average Line Value = DIVIDE([Total Revenue], [Sales Lines])

Previous Month Revenue =
CALCULATE(
    [Total Revenue],
    DATEADD(DimDate[FullDate], -1, MONTH)
)

MoM Growth % =
DIVIDE(
    [Total Revenue] - [Previous Month Revenue],
    [Previous Month Revenue]
)
```

## Suggested report pages
1. Executive overview: revenue, units, sales lines, average line value, monthly trend.
2. Product analysis: category revenue, top products, discount behavior.
3. Customer analysis: segment/state revenue, top customers, contribution share.

These are design suggestions; no `.pbix` binary is included in the repository.
