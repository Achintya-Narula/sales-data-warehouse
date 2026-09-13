IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'rpt') EXEC('CREATE SCHEMA rpt');
GO

CREATE OR ALTER VIEW rpt.vwSalesDetail AS
SELECT
    f.SaleID,
    d.FullDate,
    d.CalendarYear,
    d.CalendarQuarter,
    d.MonthNumber,
    d.MonthName,
    c.CustomerID,
    c.CustomerName,
    c.City,
    c.StateName,
    c.Segment,
    p.ProductID,
    p.ProductName,
    p.Category,
    f.Quantity,
    f.UnitPrice,
    f.DiscountPct,
    f.GrossAmount,
    f.NetAmount
FROM dw.FactSales f
JOIN dw.DimDate d ON d.DateKey = f.DateKey
JOIN dw.DimCustomer c ON c.CustomerKey = f.CustomerKey
JOIN dw.DimProduct p ON p.ProductKey = f.ProductKey;
GO

CREATE OR ALTER VIEW rpt.vwMonthlySales AS
SELECT
    CalendarYear,
    MonthNumber,
    MonthName,
    COUNT(DISTINCT SaleID) AS Orders,
    SUM(Quantity) AS Units,
    SUM(NetAmount) AS Revenue,
    AVG(NetAmount) AS AverageOrderLineValue
FROM rpt.vwSalesDetail
GROUP BY CalendarYear, MonthNumber, MonthName;
GO
