IF OBJECT_ID(N'stg.Customer', N'U') IS NULL
BEGIN
    CREATE TABLE stg.Customer
    (
        CustomerID varchar(5) NOT NULL,
        CustomerName nvarchar(100) NOT NULL,
        City nvarchar(80) NOT NULL,
        StateName nvarchar(80) NOT NULL,
        Segment nvarchar(40) NOT NULL,
        SignupDate date NOT NULL
    );
END;
GO

IF OBJECT_ID(N'stg.Product', N'U') IS NULL
BEGIN
    CREATE TABLE stg.Product
    (
        ProductID varchar(4) NOT NULL,
        ProductName nvarchar(120) NOT NULL,
        Category nvarchar(60) NOT NULL,
        UnitPrice decimal(18,2) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'stg.Sale', N'U') IS NULL
BEGIN
    CREATE TABLE stg.Sale
    (
        SaleID varchar(6) NOT NULL,
        SaleDate date NOT NULL,
        CustomerID varchar(5) NOT NULL,
        ProductID varchar(4) NOT NULL,
        Quantity smallint NOT NULL,
        UnitPrice decimal(18,2) NOT NULL,
        DiscountRate decimal(5,4) NOT NULL,
        SalesAmount decimal(18,2) NOT NULL
    );
END;
GO
