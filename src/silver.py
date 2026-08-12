from database import get_connection

# ==========================================
# SILVER LAYER - USERS TRANSFORMATION
# ==========================================


def transform_users(cursor):
    # Extract user data from Bronze layer
    select_user_query = """
    SELECT * FROM bronze.users
    """
    cursor.execute(select_user_query)
    users = cursor.fetchall()

    # Insert cleaned user data into Silver layer
    insert_user_query = """
    INSERT INTO silver.users
    (
        id,
        firstName,
        lastName,
        maidenName,
        age,
        gender,
        email,
        phone,
        username,
        birthDate,
        image,
        bloodGroup,
        height,
        weight,
        eyeColor
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for user in users:
        cursor.execute(
            insert_user_query,
            user[0],
            user[1].strip(),
            user[2].strip(),
            user[3].strip(),
            user[4],
            user[5].strip().title(),
            user[6].strip().lower(),
            user[7].strip(),
            user[8].strip(),
            user[9],
            user[10].strip(),
            user[11].strip(),
            user[12],
            user[13],
            user[14].strip(),
        )


# ==========================================
# SILVER LAYER - USER ADDRESS TRANSFORMATION
# ==========================================


def transform_user_address(cursor):
    # Extract user address data from Bronze layer
    select_address_query = """
    SELECT * FROM bronze.user_address
    """
    cursor.execute(select_address_query)
    addresses = cursor.fetchall()

    # Insert cleaned address data into Silver layer
    insert_address_query = """
    INSERT INTO silver.user_address
    (
        user_id,
        address,
        city,
        state,
        stateCode,
        postalCode,
        latitude,
        longitude,
        country
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for address in addresses:
        cursor.execute(
            insert_address_query,
            address[0],
            address[1].strip(),
            address[2].strip(),
            address[3].strip(),
            address[4].strip(),
            address[5].strip(),
            address[6],
            address[7],
            address[8].strip(),
        )


# ==========================================
# SILVER LAYER - CARTS TRANSFORMATION
# ==========================================


def transform_carts(cursor):
    # Extract cart data from Bronze layer
    select_carts_query = """
    SELECT * FROM bronze.carts
    """
    cursor.execute(select_carts_query)
    carts = cursor.fetchall()

    # Insert cleaned cart data into Silver layer
    insert_carts_query = """
    INSERT INTO silver.carts
    (
        id,
        userId,
        total,
        discountedTotal,
        totalProducts,
        totalQuantity
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """

    for cart in carts:
        cursor.execute(
            insert_carts_query,
            int(cart[0]),
            int(cart[1]),
            cart[2],
            cart[3],
            int(cart[4]),
            int(cart[5]),
        )


# ==========================================
# SILVER LAYER - CART PRODUCTS TRANSFORMATION
# ==========================================


def transform_cart_products(cursor):
    # Extract cart product data from Bronze layer
    select_cart_products_query = """
    SELECT * FROM bronze.cart_products
    """
    cursor.execute(select_cart_products_query)
    cart_products = cursor.fetchall()

    # Insert cleaned cart product data into Silver layer
    insert_cart_products_query = """
    INSERT INTO silver.cart_products
    (
        cart_id,
        product_id,
        title,
        price,
        quantity,
        total,
        discountPercentage,
        discountedTotal
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    for product in cart_products:
        cursor.execute(
            insert_cart_products_query,
            int(product[1]),
            int(product[2]),
            product[3].strip(),
            product[4],
            int(product[5]),
            product[6],
            product[7],
            product[8],
        )


# ==========================================
# SILVER LAYER - ONLINE RETAIL TRANSFORMATION
# ==========================================


def transform_online_retail(cursor):
    # Extract online retail data from Bronze layer
    select_online_retail_query = """
    SELECT * FROM bronze.online_retail
    """
    cursor.execute(select_online_retail_query)
    online_retail_data = cursor.fetchall()

    # Insert cleaned online retail data into Silver layer
    insert_online_retail_query = """
    INSERT INTO silver.online_retail
    (
        InvoiceNo,
        StockCode,
        Description,
        Quantity,
        InvoiceDate,
        UnitPrice,
        CustomerID,
        Country
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    for row in online_retail_data:
        cursor.execute(
            insert_online_retail_query,
            row[0].strip(),
            row[1].strip(),
            None if row[2] is None else row[2].strip(),
            row[3],
            row[4],
            row[5],
            row[6],
            row[7].strip(),
        )


# ==========================================
# MAIN SILVER PIPELINE
# ==========================================


def main():
    # Establish database connection
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------
    # Transform Users
    # ------------------------------------------
    transform_users(cursor)
    conn.commit()
    print("Users moved to Silver successfully")

    # ------------------------------------------
    # Transform User Addresses
    # ------------------------------------------
    transform_user_address(cursor)
    conn.commit()
    print("User addresses moved to Silver successfully")

    # ------------------------------------------
    # Transform Carts
    # ------------------------------------------
    transform_carts(cursor)
    conn.commit()
    print("Carts moved to Silver successfully")

    # ------------------------------------------
    # Transform Cart Products
    # ------------------------------------------
    transform_cart_products(cursor)
    conn.commit()
    print("Cart products moved to Silver successfully")

    # ------------------------------------------
    # Transform Online Retail
    # ------------------------------------------
    transform_online_retail(cursor)
    conn.commit()
    print("Online retail data moved to Silver successfully")

    # Close database resources
    cursor.close()
    conn.close()
    print("Database connection closed")


# Execute the Silver pipeline when this file is run directly
if __name__ == "__main__":
    main()
