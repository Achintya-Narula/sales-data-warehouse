-- 1. Month-over-month revenue growth using a CTE and LAG window function.
WITH Monthly_Sales AS (
    SELECT
        d.CalendarYear,
        d.MonthNumber,
        SUM(f.NetAmount) AS Revenue
    FROM dw.FactSales f
    JOIN dw.DimDate d ON d.DateKey = f.DateKey
    GROUP BY d.CalendarYear, d.MonthNumber
), With_Previous AS (
    SELECT
        CalendarYear,
        MonthNumber,
        Revenue,
        LAG(Revenue) OVER (ORDER BY CalendarYear, MonthNumber) AS PreviousRevenue
    FROM Monthly_Sales
)
SELECT *,
    CAST(100.0 * (Revenue - PreviousRevenue) / NULLIF(PreviousRevenue, 0) AS DECIMAL(10,2)) AS MoMGrowthPct
FROM With_Previous
ORDER BY CalendarYear, MonthNumber;
GO

-- 2. Top three products by revenue inside each category.
WITH Product_Revenue AS (
    SELECT
        p.Category,
        p.ProductName,
        SUM(f.NetAmount) AS Revenue
    FROM dw.FactSales f
    JOIN dw.DimProduct p ON p.ProductKey = f.ProductKey
    GROUP BY p.Category, p.ProductName
), Ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY Category ORDER BY Revenue DESC) AS RevenueRank
    FROM Product_Revenue
)
SELECT Category, ProductName, Revenue, RevenueRank
FROM Ranked
WHERE RevenueRank <= 3
ORDER BY Category, RevenueRank;
GO

-- 3. Customer segment contribution.
SELECT
    c.Segment,
    COUNT(DISTINCT c.CustomerID) AS Customers,
    SUM(f.NetAmount) AS Revenue,
    CAST(100.0 * SUM(f.NetAmount) / SUM(SUM(f.NetAmount)) OVER () AS DECIMAL(10,2)) AS RevenueSharePct
FROM dw.FactSales f
JOIN dw.DimCustomer c ON c.CustomerKey = f.CustomerKey
GROUP BY c.Segment
ORDER BY Revenue DESC;
GO
