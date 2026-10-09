CREATE OR ALTER VIEW dw.vw_MonthlyRevenue
AS
SELECT
    CalendarDate.YearNumber,
    CalendarDate.MonthNumber,
    CalendarDate.MonthName,
    SUM(Sale.SalesAmount) AS TotalRevenue,
    COUNT_BIG(*) AS OrderCount
FROM dw.FactSales AS Sale
INNER JOIN dw.DimDate AS CalendarDate
    ON CalendarDate.DateKey = Sale.DateKey
GROUP BY
    CalendarDate.YearNumber,
    CalendarDate.MonthNumber,
    CalendarDate.MonthName;
GO

CREATE OR ALTER VIEW dw.vw_CustomerRevenueRank
AS
WITH CustomerRevenue AS
(
    SELECT
        Customer.CustomerID,
        Customer.CustomerName,
        SUM(Sale.SalesAmount) AS TotalRevenue
    FROM dw.FactSales AS Sale
    INNER JOIN dw.DimCustomer AS Customer
        ON Customer.CustomerKey = Sale.CustomerKey
    GROUP BY Customer.CustomerID, Customer.CustomerName
)
SELECT
    CustomerID,
    CustomerName,
    TotalRevenue,
    ROW_NUMBER() OVER (ORDER BY TotalRevenue DESC, CustomerID) AS RevenueRank
FROM CustomerRevenue;
GO

CREATE OR ALTER VIEW dw.vw_ProductRevenueRank
AS
WITH ProductRevenue AS
(
    SELECT
        Product.ProductID,
        Product.ProductName,
        Product.Category,
        SUM(Sale.SalesAmount) AS TotalRevenue
    FROM dw.FactSales AS Sale
    INNER JOIN dw.DimProduct AS Product
        ON Product.ProductKey = Sale.ProductKey
    GROUP BY Product.ProductID, Product.ProductName, Product.Category
)
SELECT
    ProductID,
    ProductName,
    Category,
    TotalRevenue,
    ROW_NUMBER() OVER (ORDER BY TotalRevenue DESC, ProductID) AS RevenueRank
FROM ProductRevenue;
GO

CREATE OR ALTER VIEW dw.vw_MonthOverMonthRevenue
AS
WITH Monthly_Revenue AS
(
    SELECT
        YearNumber,
        MonthNumber,
        MonthName,
        TotalRevenue,
        OrderCount
    FROM dw.vw_MonthlyRevenue
)
SELECT
    YearNumber,
    MonthNumber,
    MonthName,
    TotalRevenue,
    OrderCount,
    LAG(TotalRevenue) OVER (ORDER BY YearNumber, MonthNumber) AS PreviousMonthRevenue
FROM Monthly_Revenue;
GO

CREATE OR ALTER VIEW dw.vw_RepeatCustomerRevenue
AS
SELECT
    Customer.CustomerID,
    Customer.CustomerName,
    COUNT_BIG(*) AS OrderCount,
    SUM(Sale.SalesAmount) AS TotalRevenue
FROM dw.FactSales AS Sale
INNER JOIN dw.DimCustomer AS Customer
    ON Customer.CustomerKey = Sale.CustomerKey
GROUP BY Customer.CustomerID, Customer.CustomerName
HAVING COUNT_BIG(*) > 1;
GO
