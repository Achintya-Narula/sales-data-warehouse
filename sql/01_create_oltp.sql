SET NOCOUNT ON;

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'oltp') EXEC('CREATE SCHEMA oltp');
GO

DROP TABLE IF EXISTS oltp.Sales;
DROP TABLE IF EXISTS oltp.Products;
DROP TABLE IF EXISTS oltp.Customers;
GO

CREATE TABLE oltp.Customers (
    CustomerID      INT            NOT NULL PRIMARY KEY,
    CustomerName    NVARCHAR(120)  NOT NULL,
    City            NVARCHAR(80)   NOT NULL,
    StateName       NVARCHAR(80)   NOT NULL,
    Segment         NVARCHAR(40)   NOT NULL,
    SignupDate      DATE           NOT NULL
);

CREATE TABLE oltp.Products (
    ProductID       INT            NOT NULL PRIMARY KEY,
    ProductName     NVARCHAR(120)  NOT NULL,
    Category        NVARCHAR(60)   NOT NULL,
    UnitPrice       DECIMAL(12,2)  NOT NULL CHECK (UnitPrice > 0),
    ActiveFlag      BIT            NOT NULL
);

CREATE TABLE oltp.Sales (
    SaleID          INT            NOT NULL PRIMARY KEY,
    SaleDate        DATE           NOT NULL,
    CustomerID      INT            NOT NULL REFERENCES oltp.Customers(CustomerID),
    ProductID       INT            NOT NULL REFERENCES oltp.Products(ProductID),
    Quantity        INT            NOT NULL CHECK (Quantity > 0),
    UnitPrice       DECIMAL(12,2)  NOT NULL CHECK (UnitPrice > 0),
    DiscountPct     DECIMAL(5,4)   NOT NULL CHECK (DiscountPct BETWEEN 0 AND 0.5),
    NetAmount       DECIMAL(14,2)  NOT NULL CHECK (NetAmount >= 0)
);
GO
