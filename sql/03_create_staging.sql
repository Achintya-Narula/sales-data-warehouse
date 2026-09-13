SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'stg') EXEC('CREATE SCHEMA stg');
GO

DROP TABLE IF EXISTS stg.Sales;
DROP TABLE IF EXISTS stg.Products;
DROP TABLE IF EXISTS stg.Customers;
GO

CREATE TABLE stg.Customers (
    CustomerID INT NOT NULL,
    CustomerName NVARCHAR(120) NOT NULL,
    City NVARCHAR(80) NOT NULL,
    StateName NVARCHAR(80) NOT NULL,
    Segment NVARCHAR(40) NOT NULL,
    SignupDate DATE NOT NULL
);

CREATE TABLE stg.Products (
    ProductID INT NOT NULL,
    ProductName NVARCHAR(120) NOT NULL,
    Category NVARCHAR(60) NOT NULL,
    UnitPrice DECIMAL(12,2) NOT NULL,
    ActiveFlag BIT NOT NULL
);

CREATE TABLE stg.Sales (
    SaleID INT NOT NULL,
    SaleDate DATE NOT NULL,
    CustomerID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(12,2) NOT NULL,
    DiscountPct DECIMAL(5,4) NOT NULL,
    NetAmount DECIMAL(14,2) NOT NULL
);
GO

TRUNCATE TABLE stg.Customers;
TRUNCATE TABLE stg.Products;
TRUNCATE TABLE stg.Sales;

INSERT INTO stg.Customers SELECT CustomerID, CustomerName, City, StateName, Segment, SignupDate FROM oltp.Customers;
INSERT INTO stg.Products SELECT ProductID, ProductName, Category, UnitPrice, ActiveFlag FROM oltp.Products;
INSERT INTO stg.Sales SELECT SaleID, SaleDate, CustomerID, ProductID, Quantity, UnitPrice, DiscountPct, NetAmount FROM oltp.Sales;
GO
