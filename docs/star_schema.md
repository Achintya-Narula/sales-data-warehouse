# Star Schema

The warehouse uses a classic star schema centered on `dw.FactSales`. The fact table grain is **one source sales line (`SaleID`)**.

```text
                    +-------------------+
                    |    dw.DimDate     |
                    |-------------------|
                    | DateKey (PK)      |
                    | FullDate          |
                    | CalendarYear      |
                    | CalendarQuarter   |
                    | MonthNumber       |
                    | MonthName         |
                    | DayOfMonth        |
                    | DayName           |
                    +---------+---------+
                              |
                              |
+-------------------+         |         +-------------------+
|  dw.DimCustomer   |         |         |   dw.DimProduct   |
|-------------------|         |         |-------------------|
| CustomerKey (PK)  |         |         | ProductKey (PK)   |
| CustomerID (NK)   |         |         | ProductID (NK)    |
| CustomerName      |         |         | ProductName       |
| City              |         |         | Category          |
| StateName         |         |         | UnitPrice         |
| Segment           |         |         | ActiveFlag        |
| SignupDate        |         |         +---------+---------+
+---------+---------+         |                   |
          |                   |                   |
          +-------------------+-------------------+
                              |
                    +---------v---------+
                    |   dw.FactSales    |
                    |-------------------|
                    | SalesKey (PK)     |
                    | SaleID (NK)       |
                    | DateKey (FK)      |
                    | CustomerKey (FK)  |
                    | ProductKey (FK)   |
                    | Quantity          |
                    | UnitPrice         |
                    | DiscountPct       |
                    | GrossAmount       |
                    | NetAmount         |
                    +-------------------+
```

## Keys and grain

- `SalesKey`, `CustomerKey`, and `ProductKey` are warehouse-generated surrogate keys.
- `SaleID`, `CustomerID`, and `ProductID` retain the source-system natural identifiers for traceability.
- `DateKey` is an integer in `YYYYMMDD` form and joins each sale to `dw.DimDate`.
- `dw.FactSales` stores one row per source `SaleID`, so rerunning the fact load can match existing business events instead of duplicating them.

## Slowly changing dimensions

`dw.DimCustomer` and `dw.DimProduct` use SCD Type 1 logic. When a matching natural key already exists, the current descriptive attributes are overwritten. This keeps the model compact and appropriate for current-state analysis, while deliberately not preserving historical attribute versions.

## Measures

The fact table exposes the additive or semi-additive fields used in analysis:

- `Quantity`
- `GrossAmount`
- `NetAmount`
- `DiscountPct`
- `UnitPrice`

`GrossAmount` is calculated as `Quantity * UnitPrice`, while `NetAmount` reflects the applied discount.
