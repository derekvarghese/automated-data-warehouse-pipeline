from database import get_connection


def transform_customer_sales(cursor):
    cursor.execute("DELETE FROM gold.customer_sales_summary")

    cursor.execute("""
        SELECT
                CustomerID,
                count(distinct InvoiceNo) as TotalOrders,
                sum(Quantity) as TotalQuantity,
                sum(Quantity * UnitPrice) as TotalSales,
                sum(Quantity * UnitPrice)/count(distinct InvoiceNo) as AverageOrderValue,
                min(InvoiceDate) as FirstPurchaseDate,
                max(InvoiceDate) as LastPurchaseDate
        FROM silver.online_retail
        WHERE CustomerID IS NOT NULL
        GROUP BY CustomerID
    """)

    customer_sales = cursor.fetchall()

    insert_customer_sales_query = """
    INSERT INTO gold.customer_sales_summary(
        CustomerID,
        TotalOrders,
        TotalQuantity,
        TotalSales,
        AverageOrderValue,
        FirstPurchaseDate,
        LastPurchaseDate
    )
    VALUES (?,?,?,?,?,?,?)
    """

    for customer in customer_sales:
        cursor.execute(
            insert_customer_sales_query,
            customer[0],
            customer[1],
            customer[2],
            customer[3],
            customer[4],
            customer[5],
            customer[6],
        )


def transform_product_performance(cursor):
    cursor.execute("DELETE FROM gold.product_performance")

    cursor.execute("""
        with ProductMetrics as (
            select
                StockCode,
                sum(Quantity) as TotalQuantitySold,
                sum(Quantity * UnitPrice) as TotalRevenue,
                count(distinct InvoiceNo) as TotalOrders,
                count(distinct CustomerID) as UniqueCustomers,
                min(InvoiceDate) as FirstSaleDate,
                max(InvoiceDate) as LastSaleDate
            from silver.online_retail
            group by StockCode
            ),
            DescriptionCounts AS (
                SELECT
                    StockCode,
                    Description,
                    COUNT(*) AS DescriptionCount,
                    ROW_NUMBER() OVER (
                        PARTITION BY StockCode
                        ORDER BY COUNT(*) DESC
                    ) AS rn
                FROM silver.online_retail
                WHERE Description IS NOT NULL
                GROUP BY
                    StockCode,
                    Description
            ),
            CleanDescriptions AS (
                SELECT
                    StockCode,
                    Description
                FROM DescriptionCounts
                WHERE rn = 1
            )
            SELECT
                pm.StockCode,
                cd.Description,
                pm.TotalQuantitySold,
                pm.TotalRevenue,
                pm.TotalOrders,
                pm.UniqueCustomers,
                pm.FirstSaleDate,
                pm.LastSaleDate
            FROM ProductMetrics pm
            LEFT JOIN CleanDescriptions cd
                ON pm.StockCode = cd.StockCode
    """)
    product_performance = cursor.fetchall()

    insert_product_performance_query = """
        INSERT INTO gold.product_performance(
            StockCode,
            Description,
            TotalQuantitySold,
            TotalRevenue,
            TotalOrders,
            UniqueCustomers,
            FirstSaleDate,
            LastSaleDate    
        )
        VALUES (?,?,?,?,?,?,?,?)
    """
    for product in product_performance:
        cursor.execute(
            insert_product_performance_query,
            product[0],
            product[1],
            product[2],
            product[3],
            product[4],
            product[5],
            product[6],
            product[7],
        )


def transform_sales_summary(cursor):
    cursor.execute("DELETE FROM gold.sales_summary")

    cursor.execute("""
        select
            cast(datetrunc(month, InvoiceDate) as date) as SalesMonth,
            sum(Quantity * UnitPrice) as TotalSales,
            count(distinct InvoiceNo) as TotalOrders,
            sum(Quantity) as TotalQuantitySold,
            (sum(Quantity * UnitPrice) / count(distinct InvoiceNo)) as AverageOrderValue,
            min(InvoiceDate) as FirstSaleDate,
            max(InvoiceDate) as LastSaleDate
        from silver.online_retail
        group by cast(datetrunc(month, InvoiceDate) as date)
    """)
    sales_summary = cursor.fetchall()

    insert_sales_summary_query = """
        INSERT INTO gold.sales_summary(
            SalesMonth,
            TotalSales,
            TotalOrders,
            TotalQuantitySold,
            AverageOrderValue,
            FirstSaleDate,
            LastSaleDate
        )
        VALUES (?,?,?,?,?,?,?)
    """
    for summary in sales_summary:
        cursor.execute(
            insert_sales_summary_query,
            summary[0],
            summary[1],
            summary[2],
            summary[3],
            summary[4],
            summary[5],
            summary[6],
        )


def main():
    conn = get_connection()
    cursor = conn.cursor()

    transform_customer_sales(cursor)
    conn.commit()
    print("Customer sales summary moved to Gold successfully")

    transform_product_performance(cursor)
    conn.commit()
    print("Product performance moved to Gold successfully")

    transform_sales_summary(cursor)
    conn.commit()
    print("Sales summary moved to Gold successfully")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
