import psycopg2


def get_connection():
    connection = psycopg2.connect(
        host="localhost",
        port=5432,
        database="food_delivery",
        user="postgres",
        password="postgres"
    )

    return connection