IF NOT EXISTS (SELECT 1 FROM dw.DimDate)
BEGIN
    ;WITH DateSeries AS
    (
        SELECT CONVERT(date, '2024-01-01') AS FullDate
        UNION ALL
        SELECT DATEADD(day, 1, FullDate)
        FROM DateSeries
        WHERE FullDate < CONVERT(date, '2025-12-31')
    )
    INSERT INTO dw.DimDate
    (
        DateKey,
        FullDate,
        DayNumber,
        MonthNumber,
        MonthName,
        QuarterNumber,
        YearNumber
    )
    SELECT
        CONVERT(int, CONVERT(char(8), FullDate, 112)),
        FullDate,
        DATEPART(day, FullDate),
        DATEPART(month, FullDate),
        DATENAME(month, FullDate),
        DATEPART(quarter, FullDate),
        DATEPART(year, FullDate)
    FROM DateSeries
    OPTION (MAXRECURSION 1000);
END;
GO

CREATE OR ALTER PROCEDURE etl.usp_LoadDimensions
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @CustomerActions table (ActionName nvarchar(10) NOT NULL);
    DECLARE @ProductActions table (ActionName nvarchar(10) NOT NULL);

    ;WITH CustomerSource AS
    (
        SELECT CustomerID, CustomerName, City, StateName, Segment, SignupDate
        FROM
        (
            SELECT
                CustomerID,
                CustomerName,
                City,
                StateName,
                Segment,
                SignupDate,
                ROW_NUMBER() OVER
                (
                    PARTITION BY CustomerID
                    ORDER BY CustomerName, City, StateName, Segment, SignupDate
                ) AS SourceRow
            FROM stg.Customer
        ) AS RankedCustomers
        WHERE SourceRow = 1
    )
    MERGE dw.DimCustomer AS Target
    USING CustomerSource AS Source
        ON Target.CustomerID = Source.CustomerID
    WHEN MATCHED AND
    (
           Target.CustomerName <> Source.CustomerName
        OR Target.City <> Source.City
        OR Target.StateName <> Source.StateName
        OR Target.Segment <> Source.Segment
        OR Target.SignupDate <> Source.SignupDate
    )
        THEN UPDATE SET
            CustomerName = Source.CustomerName,
            City = Source.City,
            StateName = Source.StateName,
            Segment = Source.Segment,
            SignupDate = Source.SignupDate,
            UpdatedAt = SYSUTCDATETIME()
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (CustomerID, CustomerName, City, StateName, Segment, SignupDate)
        VALUES
        (
            Source.CustomerID,
            Source.CustomerName,
            Source.City,
            Source.StateName,
            Source.Segment,
            Source.SignupDate
        )
    OUTPUT $action INTO @CustomerActions (ActionName);

    ;WITH ProductSource AS
    (
        SELECT ProductID, ProductName, Category, UnitPrice
        FROM
        (
            SELECT
                ProductID,
                ProductName,
                Category,
                UnitPrice,
                ROW_NUMBER() OVER
                (
                    PARTITION BY ProductID
                    ORDER BY ProductName, Category, UnitPrice
                ) AS SourceRow
            FROM stg.Product
        ) AS RankedProducts
        WHERE SourceRow = 1
    )
    MERGE dw.DimProduct AS Target
    USING ProductSource AS Source
        ON Target.ProductID = Source.ProductID
    WHEN MATCHED AND
    (
           Target.ProductName <> Source.ProductName
        OR Target.Category <> Source.Category
        OR Target.UnitPrice <> Source.UnitPrice
    )
        THEN UPDATE SET
            ProductName = Source.ProductName,
            Category = Source.Category,
            UnitPrice = Source.UnitPrice,
            UpdatedAt = SYSUTCDATETIME()
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (ProductID, ProductName, Category, UnitPrice)
        VALUES (Source.ProductID, Source.ProductName, Source.Category, Source.UnitPrice)
    OUTPUT $action INTO @ProductActions (ActionName);

    SELECT
        (SELECT COUNT(*) FROM @CustomerActions WHERE ActionName = N'INSERT')
            AS CustomerInserts,
        (SELECT COUNT(*) FROM @CustomerActions WHERE ActionName = N'UPDATE')
            AS CustomerUpdates,
        (SELECT COUNT(*) FROM @ProductActions WHERE ActionName = N'INSERT')
            AS ProductInserts,
        (SELECT COUNT(*) FROM @ProductActions WHERE ActionName = N'UPDATE')
            AS ProductUpdates;
END;
GO
