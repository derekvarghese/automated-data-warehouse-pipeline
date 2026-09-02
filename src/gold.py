from datetime import datetime
from database import get_connection


def get_run_id(cursor):
    cursor.execute("SELECT ISNULL(MAX(RunId),0) + 1 FROM gold.pipeline_monitoring")
    return cursor.fetchone()[0]


def log_pipeline_monitoring(
    cursor,
    run_id,
    pipeline_name,
    table_name,
    start_time,
    end_time,
    status,
    records_processed,
    error_message,
):
    cursor.execute(
        """
        INSERT INTO gold.pipeline_monitoring(
            RunId,
            PipelineName,
            TableName,
            StartTime,
            EndTime,
            Status,
            RecordsProcessed,
            ErrorMessage
        )
        VALUES (?,?,?,?,?,?,?,?)
    """,
        run_id,
        pipeline_name,
        table_name,
        start_time,
        end_time,
        status,
        records_processed,
        error_message,
    )


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

    return len(customer_sales)


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

    return len(product_performance)


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

    return len(sales_summary)


def transform_cart_analysis(cursor):
    cursor.execute("DELETE FROM gold.cart_analysis")

    cursor.execute("""
        select
            id,
            userId,
            totalProducts,
            totalQuantity,
            total,
            discountedTotal,
            (total - discountedTotal) as TotalDiscount
        from silver.carts
    """)
    cart_analysis = cursor.fetchall()

    insert_cart_analysis_query = """
        INSERT INTO gold.cart_analysis(
            CartID,
            UserID,
            TotalProducts,
            TotalQuantity,
            CartValue,
            DiscountedCartValue,
            TotalDiscount
        )
        VALUES (?,?,?,?,?,?,?)
    """
    for cart in cart_analysis:
        cursor.execute(
            insert_cart_analysis_query,
            cart[0],
            cart[1],
            cart[2],
            cart[3],
            cart[4],
            cart[5],
            cart[6],
        )
    return len(cart_analysis)


def main():
    conn = get_connection()
    cursor = conn.cursor()

    run_id = get_run_id(cursor)
    print(f"Starting Gold pipeline - RunID: {run_id}")

    customer_sales_status = "SUCCESS"
    customer_sales_count = 0
    start_time = datetime.now()
    try:
        customer_sales_count = transform_customer_sales(cursor)

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "customer_sales_summary",
            start_time,
            end_time,
            customer_sales_status,
            customer_sales_count,
            None,
        )

        conn.commit()
        print(
            f"Customer sales summary completed successfully - {customer_sales_count} records processed"
        )

    except Exception as e:
        conn.rollback()
        customer_sales_status = "FAILED"

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "customer_sales_summary",
            start_time,
            end_time,
            customer_sales_status,
            customer_sales_count,
            str(e),
        )

        conn.commit()
        print(f"Customer sales summary FAILED - 0 records processed - {str(e)}")

    product_performance_status = "SUCCESS"
    product_performance_count = 0
    start_time = datetime.now()
    try:
        product_performance_count = transform_product_performance(cursor)

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "product_performance",
            start_time,
            end_time,
            product_performance_status,
            product_performance_count,
            None,
        )

        conn.commit()
        print(
            f"Product performance completed successfully - {product_performance_count} records processed"
        )

    except Exception as e:
        conn.rollback()
        product_performance_status = "FAILED"

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "product_performance",
            start_time,
            end_time,
            product_performance_status,
            product_performance_count,
            str(e),
        )

        conn.commit()
        print(f"Product performance FAILED - 0 records processed - {str(e)}")

    sales_summary_status = "SUCCESS"
    sales_summary_count = 0
    start_time = datetime.now()
    try:
        sales_summary_count = transform_sales_summary(cursor)

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "sales_summary",
            start_time,
            end_time,
            sales_summary_status,
            sales_summary_count,
            None,
        )

        conn.commit()
        print(
            f"Sales summary completed successfully - {sales_summary_count} records processed"
        )

    except Exception as e:
        conn.rollback()
        sales_summary_status = "FAILED"

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "sales_summary",
            start_time,
            end_time,
            sales_summary_status,
            sales_summary_count,
            str(e),
        )

        conn.commit()
        print(f"Sales summary FAILED - 0 records processed - {str(e)}")

    cart_analysis_status = "SUCCESS"
    cart_analysis_count = 0
    start_time = datetime.now()
    try:
        cart_analysis_count = transform_cart_analysis(cursor)

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "cart_analysis",
            start_time,
            end_time,
            cart_analysis_status,
            cart_analysis_count,
            None,
        )

        conn.commit()
        print(
            f"Cart analysis completed successfully - {cart_analysis_count} records processed"
        )

    except Exception as e:
        conn.rollback()
        cart_analysis_status = "FAILED"

        end_time = datetime.now()
        log_pipeline_monitoring(
            cursor,
            run_id,
            "Gold Transformation",
            "cart_analysis",
            start_time,
            end_time,
            cart_analysis_status,
            cart_analysis_count,
            str(e),
        )

        conn.commit()
        print(f"Cart analysis FAILED - 0 records processed - {str(e)}")

    cursor.close()
    conn.close()

    print("=" * 50)
    print(f"Gold Pipeline Completed - RunID: {run_id}")
    print("=" * 50)
    print(
        f"Customer Sales       : {customer_sales_status} - {customer_sales_count} records"
    )
    print(
        f"Product Performance  : {product_performance_status} - {product_performance_count} records"
    )
    print(
        f"Sales Summary        : {sales_summary_status} - {sales_summary_count} records"
    )
    print(
        f"Cart Analysis        : {cart_analysis_status} - {cart_analysis_count} records"
    )
    print("=" * 50)


if __name__ == "__main__":
    main()
