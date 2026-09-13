-- Run after 01_create_oltp.sql. Copy the generated CSV files to C:\data\sales-dw\ first.
SET NOCOUNT ON;

BULK INSERT oltp.Customers
FROM 'C:\data\sales-dw\customers.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);

BULK INSERT oltp.Products
FROM 'C:\data\sales-dw\products.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);

BULK INSERT oltp.Sales
FROM 'C:\data\sales-dw\sales.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO
