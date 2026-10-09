IF OBJECT_ID(N'dw.DimCustomer', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimCustomer
    (
        CustomerKey int IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DimCustomer PRIMARY KEY,
        CustomerID varchar(5) NOT NULL
            CONSTRAINT UQ_DimCustomer_CustomerID UNIQUE (CustomerID),
        CustomerName nvarchar(100) NOT NULL,
        City nvarchar(80) NOT NULL,
        StateName nvarchar(80) NOT NULL,
        Segment nvarchar(40) NOT NULL,
        SignupDate date NOT NULL,
        UpdatedAt datetime2(0) NOT NULL
            CONSTRAINT DF_DimCustomer_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_DimCustomer_Segment
            CHECK (Segment IN (N'Consumer', N'Corporate', N'Small Business'))
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dw.DimCustomer')
      AND name = N'IX_DimCustomer_SegmentCity'
)
    CREATE INDEX IX_DimCustomer_SegmentCity
        ON dw.DimCustomer (Segment, City);
GO

IF OBJECT_ID(N'dw.DimProduct', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimProduct
    (
        ProductKey int IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DimProduct PRIMARY KEY,
        ProductID varchar(4) NOT NULL
            CONSTRAINT UQ_DimProduct_ProductID UNIQUE (ProductID),
        ProductName nvarchar(120) NOT NULL,
        Category nvarchar(60) NOT NULL,
        UnitPrice decimal(18,2) NOT NULL,
        UpdatedAt datetime2(0) NOT NULL
            CONSTRAINT DF_DimProduct_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_DimProduct_UnitPrice CHECK (UnitPrice >= 0)
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dw.DimProduct')
      AND name = N'IX_DimProduct_Category'
)
    CREATE INDEX IX_DimProduct_Category
        ON dw.DimProduct (Category);
GO

IF OBJECT_ID(N'dw.DimDate', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimDate
    (
        DateKey int NOT NULL
            CONSTRAINT PK_DimDate PRIMARY KEY,
        FullDate date NOT NULL
            CONSTRAINT UQ_DimDate_FullDate UNIQUE (FullDate),
        DayNumber tinyint NOT NULL,
        MonthNumber tinyint NOT NULL,
        MonthName nvarchar(20) NOT NULL,
        QuarterNumber tinyint NOT NULL,
        YearNumber smallint NOT NULL
    );
END;
GO
