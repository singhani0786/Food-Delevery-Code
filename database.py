import psycopg2

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="food_delivery",
    user="postgres",
    password="postgres"
)

print("PostgreSQL connection successful")