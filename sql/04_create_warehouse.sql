SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dw') EXEC('CREATE SCHEMA dw');
GO

DROP TABLE IF EXISTS dw.FactSales;
DROP TABLE IF EXISTS dw.DimDate;
DROP TABLE IF EXISTS dw.DimProduct;
DROP TABLE IF EXISTS dw.DimCustomer;
GO

CREATE TABLE dw.DimCustomer (
    CustomerKey     INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CustomerID      INT NOT NULL UNIQUE,
    CustomerName    NVARCHAR(120) NOT NULL,
    City            NVARCHAR(80) NOT NULL,
    StateName       NVARCHAR(80) NOT NULL,
    Segment         NVARCHAR(40) NOT NULL,
    SignupDate      DATE NOT NULL,
    LastUpdatedAt   DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dw.DimProduct (
    ProductKey      INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ProductID       INT NOT NULL UNIQUE,
    ProductName     NVARCHAR(120) NOT NULL,
    Category        NVARCHAR(60) NOT NULL,
    UnitPrice       DECIMAL(12,2) NOT NULL,
    ActiveFlag      BIT NOT NULL,
    LastUpdatedAt   DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dw.DimDate (
    DateKey         INT NOT NULL PRIMARY KEY,
    FullDate        DATE NOT NULL UNIQUE,
    CalendarYear    SMALLINT NOT NULL,
    CalendarQuarter TINYINT NOT NULL,
    MonthNumber     TINYINT NOT NULL,
    MonthName       NVARCHAR(20) NOT NULL,
    DayOfMonth      TINYINT NOT NULL,
    DayName         NVARCHAR(20) NOT NULL
);

CREATE TABLE dw.FactSales (
    SalesKey        BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    SaleID          INT NOT NULL UNIQUE,
    DateKey         INT NOT NULL REFERENCES dw.DimDate(DateKey),
    CustomerKey     INT NOT NULL REFERENCES dw.DimCustomer(CustomerKey),
    ProductKey      INT NOT NULL REFERENCES dw.DimProduct(ProductKey),
    Quantity        INT NOT NULL,
    UnitPrice       DECIMAL(12,2) NOT NULL,
    DiscountPct     DECIMAL(5,4) NOT NULL,
    GrossAmount     DECIMAL(14,2) NOT NULL,
    NetAmount       DECIMAL(14,2) NOT NULL,
    LoadedAt        DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX IX_FactSales_DateKey ON dw.FactSales(DateKey);
CREATE INDEX IX_FactSales_CustomerKey ON dw.FactSales(CustomerKey);
CREATE INDEX IX_FactSales_ProductKey ON dw.FactSales(ProductKey);
GO
