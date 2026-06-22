from database import get_connection
import requests
import json

# ==========================================
# DATABASE CONNECTION
# ==========================================

conn = get_connection()
cursor = conn.cursor()

# ==========================================
# API DATA INGESTION - CARTS
# ==========================================

url = "https://dummyjson.com/carts"
response = requests.get(url)

cart_data = response.json()

carts_data = []
carts_products_data = []

for cart in cart_data['carts']:

    cart_record = {
        "id": cart["id"],
        "userId": cart["userId"],
        "total": cart["total"],
        "discountedTotal": cart["discountedTotal"],
        "totalProducts": cart["totalProducts"],
        "totalQuantity": cart["totalQuantity"]
    }

    carts_data.append(cart_record)

    cart_id = cart["id"]

    for product in cart["products"]:

        product_record = {
            "cart_id": cart_id,
            "product_id": product["id"],
            "title": product["title"],
            "price": product["price"],
            "quantity": product["quantity"],
            "total": product["total"],
            "discountPercentage": product["discountPercentage"],
            "discountedTotal": product["discountedTotal"]
        }

        carts_products_data.append(product_record)

print(f"Carts to insert: {len(carts_data)}")
print(f"Products to insert: {len(carts_products_data)}")

insert_carts_query = """
INSERT INTO bronze.carts
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

for cart in carts_data:
    cursor.execute(
        insert_carts_query,
        cart["id"],
        cart["userId"],
        cart["total"],
        cart["discountedTotal"],
        cart["totalProducts"],
        cart["totalQuantity"]
    )

print("Carts loaded successfully")

insert_products_query = """
INSERT INTO bronze.cart_products
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

for product in carts_products_data:
    cursor.execute(
        insert_products_query,
        product["cart_id"],
        product["product_id"],
        product["title"],
        product["price"],
        product["quantity"],
        product["total"],
        product["discountPercentage"],
        product["discountedTotal"]
    )

print("Cart products loaded successfully")

conn.commit()

print("API data ingestion successful")

# ==========================================
# JSON DATA INGESTION - USERS
# ==========================================

with open("data/json/users.json", "r", encoding="utf-8") as file:
    user_json = json.load(file)

user_data = []
user_address_data = []

for user in user_json["users"]:

    user_record = {
        "id": user["id"],
        "firstName": user["firstName"],
        "lastName": user["lastName"],
        "maidenName": user["maidenName"],
        "age": user["age"],
        "gender": user["gender"],
        "email": user["email"],
        "phone": user["phone"],
        "username": user["username"],
        "birthDate": user["birthDate"],
        "image": user["image"],
        "bloodGroup": user["bloodGroup"],
        "height": user["height"],
        "weight": user["weight"],
        "eyeColor": user["eyeColor"]
    }

    user_data.append(user_record)

    address_record = {
        "user_id": user["id"],
        "address": user["address"]["address"],
        "city": user["address"]["city"],
        "state": user["address"]["state"],
        "stateCode": user["address"]["stateCode"],
        "postalCode": user["address"]["postalCode"],
        "latitude": user["address"]["coordinates"]["lat"],
        "longitude": user["address"]["coordinates"]["lng"],
        "country": user["address"]["country"]
    }

    user_address_data.append(address_record)

print(f"Users to insert: {len(user_data)}")
print(f"Addresses to insert: {len(user_address_data)}")

insert_user_query = """
INSERT INTO bronze.users
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

for user in user_data:
    cursor.execute(
        insert_user_query,
        user["id"],
        user["firstName"],
        user["lastName"],
        user["maidenName"],
        user["age"],
        user["gender"],
        user["email"],
        user["phone"],
        user["username"],
        user["birthDate"],
        user["image"],
        user["bloodGroup"],
        user["height"],
        user["weight"],
        user["eyeColor"]
    )

print("Users loaded successfully")

insert_address_query = """
INSERT INTO bronze.user_address
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

for address in user_address_data:
    cursor.execute(
        insert_address_query,
        address["user_id"],
        address["address"],
        address["city"],
        address["state"],
        address["stateCode"],
        address["postalCode"],
        address["latitude"],
        address["longitude"],
        address["country"]
    )

print("User addresses loaded successfully")

conn.commit()

print("JSON data ingestion successful")

# ==========================================
# CLOSE CONNECTION
# ==========================================

cursor.close()
conn.close()

print("Database connection closed")