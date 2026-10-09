IF OBJECT_ID(N'dw.FactSales', N'U') IS NULL
BEGIN
    CREATE TABLE dw.FactSales
    (
        SalesKey bigint IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_FactSales PRIMARY KEY,
        SaleID varchar(6) NOT NULL
            CONSTRAINT UQ_FactSales_SaleID UNIQUE (SaleID),
        DateKey int NOT NULL,
        CustomerKey int NOT NULL,
        ProductKey int NOT NULL,
        Quantity smallint NOT NULL,
        UnitPrice decimal(18,2) NOT NULL,
        DiscountRate decimal(5,4) NOT NULL,
        SalesAmount decimal(18,2) NOT NULL,
        LoadedAt datetime2(0) NOT NULL
            CONSTRAINT DF_FactSales_LoadedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_FactSales_DimDate
            FOREIGN KEY (DateKey) REFERENCES dw.DimDate(DateKey),
        CONSTRAINT FK_FactSales_DimCustomer
            FOREIGN KEY (CustomerKey) REFERENCES dw.DimCustomer(CustomerKey),
        CONSTRAINT FK_FactSales_DimProduct
            FOREIGN KEY (ProductKey) REFERENCES dw.DimProduct(ProductKey),
        CONSTRAINT CK_FactSales_Quantity CHECK (Quantity > 0),
        CONSTRAINT CK_FactSales_UnitPrice CHECK (UnitPrice >= 0),
        CONSTRAINT CK_FactSales_DiscountRate CHECK (DiscountRate BETWEEN 0 AND 1),
        CONSTRAINT CK_FactSales_SalesAmount CHECK (SalesAmount >= 0)
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dw.FactSales')
      AND name = N'IX_FactSales_DateKey'
)
    CREATE INDEX IX_FactSales_DateKey ON dw.FactSales (DateKey);
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dw.FactSales')
      AND name = N'IX_FactSales_CustomerKey'
)
    CREATE INDEX IX_FactSales_CustomerKey ON dw.FactSales (CustomerKey);
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dw.FactSales')
      AND name = N'IX_FactSales_ProductKey'
)
    CREATE INDEX IX_FactSales_ProductKey ON dw.FactSales (ProductKey);
GO
