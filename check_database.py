import psycopg2

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="food_delivery",
    user="postgres",
    password="postgres"
)

cursor = connection.cursor()


tables = {

    "users": """
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(30) NOT NULL,
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "restaurants": """
        CREATE TABLE restaurants (
            restaurant_id SERIAL PRIMARY KEY,
            owner_id INTEGER NOT NULL,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_restaurant_owner
                FOREIGN KEY (owner_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        );
    """,

    "meals": """
        CREATE TABLE meals (
            meal_id SERIAL PRIMARY KEY,
            restaurant_id INTEGER NOT NULL,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            is_available BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_meal_restaurant
                FOREIGN KEY (restaurant_id)
                REFERENCES restaurants(restaurant_id)
                ON DELETE CASCADE
        );
    """,

    "coupons": """
        CREATE TABLE coupons (
            coupon_id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            discount_percentage DECIMAL(5, 2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            expiry_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "orders": """
        CREATE TABLE orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            restaurant_id INTEGER NOT NULL,
            coupon_id INTEGER,
            subtotal DECIMAL(10, 2) NOT NULL,
            discount DECIMAL(10, 2) DEFAULT 0,
            tip DECIMAL(10, 2) DEFAULT 0,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'Placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_order_customer
                FOREIGN KEY (customer_id)
                REFERENCES users(user_id),

            CONSTRAINT fk_order_restaurant
                FOREIGN KEY (restaurant_id)
                REFERENCES restaurants(restaurant_id),

            CONSTRAINT fk_order_coupon
                FOREIGN KEY (coupon_id)
                REFERENCES coupons(coupon_id)
        );
    """,

    "order_items": """
        CREATE TABLE order_items (
            order_item_id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            meal_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_purchase DECIMAL(10, 2) NOT NULL,

            CONSTRAINT fk_order_item_order
                FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_order_item_meal
                FOREIGN KEY (meal_id)
                REFERENCES meals(meal_id)
        );
    """,

    "order_status_history": """
        CREATE TABLE order_status_history (
            history_id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            old_status VARCHAR(30),
            new_status VARCHAR(30) NOT NULL,
            changed_by INTEGER NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_status_order
                FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_status_user
                FOREIGN KEY (changed_by)
                REFERENCES users(user_id)
        );
    """
}


for table_name, create_query in tables.items():

    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        );
    """, (table_name,))

    table_exists = cursor.fetchone()[0]

    if table_exists:
        print(f"\n{table_name} table already exists")

    else:
        print(f"\n{table_name} table does not exist. Creating it...")

        cursor.execute(create_query)

        connection.commit()

        print(f"{table_name} table created successfully")


print("\n----------------------------------------")
print("TABLE ATTRIBUTES")
print("----------------------------------------")


for table_name in tables.keys():

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))

    columns = cursor.fetchall()

    print(f"\n{table_name} table attributes:")

    for column in columns:
        print(column)


cursor.close()
connection.close()

print("\nDatabase check completed successfully.")