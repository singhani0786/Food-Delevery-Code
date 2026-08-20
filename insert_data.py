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
    INSERT INTO users (name, email, password, role)
    VALUES (%s, %s, %s, %s)
    RETURNING user_id;
""", (
    "Ani",
    "ani@example.com",
    "test123",
    "CUSTOMER"
))

user_id = cursor.fetchone()[0]

connection.commit()

print(f"User created successfully. User ID: {user_id}")

cursor.close()
connection.close()