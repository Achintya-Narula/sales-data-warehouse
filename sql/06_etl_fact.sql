SET NOCOUNT ON;

MERGE dw.FactSales AS target
USING (
    SELECT
        s.SaleID,
        d.DateKey,
        c.CustomerKey,
        p.ProductKey,
        s.Quantity,
        s.UnitPrice,
        s.DiscountPct,
        CAST(s.Quantity * s.UnitPrice AS DECIMAL(14,2)) AS GrossAmount,
        s.NetAmount
    FROM stg.Sales s
    INNER JOIN dw.DimDate d ON d.FullDate = s.SaleDate
    INNER JOIN dw.DimCustomer c ON c.CustomerID = s.CustomerID
    INNER JOIN dw.DimProduct p ON p.ProductID = s.ProductID
) AS source
ON target.SaleID = source.SaleID
WHEN MATCHED THEN
    UPDATE SET
        DateKey = source.DateKey,
        CustomerKey = source.CustomerKey,
        ProductKey = source.ProductKey,
        Quantity = source.Quantity,
        UnitPrice = source.UnitPrice,
        DiscountPct = source.DiscountPct,
        GrossAmount = source.GrossAmount,
        NetAmount = source.NetAmount,
        LoadedAt = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
    INSERT (SaleID, DateKey, CustomerKey, ProductKey, Quantity, UnitPrice, DiscountPct, GrossAmount, NetAmount)
    VALUES (source.SaleID, source.DateKey, source.CustomerKey, source.ProductKey, source.Quantity, source.UnitPrice, source.DiscountPct, source.GrossAmount, source.NetAmount);
GO
