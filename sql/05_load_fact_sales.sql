CREATE OR ALTER PROCEDURE etl.usp_LoadFactSales
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS
    (
        SELECT 1
        FROM stg.Sale AS Sale
        LEFT JOIN dw.DimCustomer AS Customer
            ON Customer.CustomerID = Sale.CustomerID
        LEFT JOIN dw.DimProduct AS Product
            ON Product.ProductID = Sale.ProductID
        LEFT JOIN dw.DimDate AS CalendarDate
            ON CalendarDate.FullDate = Sale.SaleDate
        WHERE Customer.CustomerKey IS NULL
           OR Product.ProductKey IS NULL
           OR CalendarDate.DateKey IS NULL
    )
    BEGIN
        THROW 51001, 'Fact load stopped because a dimension key could not be resolved.', 1;
    END;

    INSERT INTO dw.FactSales
    (
        SaleID,
        DateKey,
        CustomerKey,
        ProductKey,
        Quantity,
        UnitPrice,
        DiscountRate,
        SalesAmount
    )
    SELECT
        Sale.SaleID,
        CalendarDate.DateKey,
        Customer.CustomerKey,
        Product.ProductKey,
        Sale.Quantity,
        Sale.UnitPrice,
        Sale.DiscountRate,
        Sale.SalesAmount
    FROM stg.Sale AS Sale
    INNER JOIN dw.DimCustomer AS Customer
        ON Customer.CustomerID = Sale.CustomerID
    INNER JOIN dw.DimProduct AS Product
        ON Product.ProductID = Sale.ProductID
    INNER JOIN dw.DimDate AS CalendarDate
        ON CalendarDate.FullDate = Sale.SaleDate
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dw.FactSales AS ExistingSale
        WHERE ExistingSale.SaleID = Sale.SaleID
    );

    SELECT @@ROWCOUNT AS FactRowsInserted;
END;
GO
