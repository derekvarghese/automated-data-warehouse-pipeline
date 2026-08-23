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


def main():
    conn = get_connection()
    cursor = conn.cursor()

    transform_customer_sales(cursor)
    conn.commit()
    print("Customer sales summary moved to Gold successfully")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
