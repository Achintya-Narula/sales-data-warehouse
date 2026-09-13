SET NOCOUNT ON;

-- Type 1: overwrite current descriptive attributes for an existing natural key.
MERGE dw.DimCustomer AS target
USING stg.Customers AS source
ON target.CustomerID = source.CustomerID
WHEN MATCHED THEN
    UPDATE SET
        CustomerName = source.CustomerName,
        City = source.City,
        StateName = source.StateName,
        Segment = source.Segment,
        SignupDate = source.SignupDate,
        LastUpdatedAt = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
    INSERT (CustomerID, CustomerName, City, StateName, Segment, SignupDate)
    VALUES (source.CustomerID, source.CustomerName, source.City, source.StateName, source.Segment, source.SignupDate);

MERGE dw.DimProduct AS target
USING stg.Products AS source
ON target.ProductID = source.ProductID
WHEN MATCHED THEN
    UPDATE SET
        ProductName = source.ProductName,
        Category = source.Category,
        UnitPrice = source.UnitPrice,
        ActiveFlag = source.ActiveFlag,
        LastUpdatedAt = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
    INSERT (ProductID, ProductName, Category, UnitPrice, ActiveFlag)
    VALUES (source.ProductID, source.ProductName, source.Category, source.UnitPrice, source.ActiveFlag);
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimDate WHERE FullDate = '2024-01-01')
BEGIN
    ;WITH DateSeries AS (
        SELECT CAST('2024-01-01' AS DATE) AS FullDate
        UNION ALL
        SELECT DATEADD(DAY, 1, FullDate)
        FROM DateSeries
        WHERE FullDate < '2027-12-31'
    )
    INSERT INTO dw.DimDate (DateKey, FullDate, CalendarYear, CalendarQuarter, MonthNumber, MonthName, DayOfMonth, DayName)
    SELECT
        CONVERT(INT, CONVERT(CHAR(8), FullDate, 112)),
        FullDate,
        YEAR(FullDate),
        DATEPART(QUARTER, FullDate),
        MONTH(FullDate),
        DATENAME(MONTH, FullDate),
        DAY(FullDate),
        DATENAME(WEEKDAY, FullDate)
    FROM DateSeries
    OPTION (MAXRECURSION 0);
END;
GO
