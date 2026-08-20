import psycopg2

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="food_delivery",
    user="postgres",
    password="postgres"
)

cursor = connection.cursor()

cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'users'
    );
""")

table_exists = cursor.fetchone()[0]

if table_exists:
    print("Users table already exists")

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """)

    columns = cursor.fetchall()

    print("Users table attributes:")
    for column in columns:
        print(column)

else:
    print("Users table does not exist. Creating it...")

    cursor.execute("""
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(30) NOT NULL,
            is_blocked BOOLEAN DEFAULT FALSE
        );
    """)

    connection.commit()

    print("Users table created successfully")

cursor.close()
connection.close()