import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Sample medicine data
medicines = [
    ('Paracetamol', 'Pain reliever', 3.50, 100, 'Acme Pharma', 'https://via.placeholder.com/100?text=Paracetamol'),
    ('Ibuprofen', 'Anti-inflammatory', 4.20, 50, 'HealthCorp', 'https://via.placeholder.com/100?text=Ibuprofen'),
    ('Vitamin C', 'Supplement', 5.00, 75, 'NutraHealth', 'https://via.placeholder.com/100?text=Vitamin+C'),
    ('Amoxicillin', 'Antibiotic', 10.00, 40, 'MediLab', 'https://via.placeholder.com/100?text=Amoxicillin'),
    ('Cetirizine', 'Antihistamine', 7.00, 60, 'AllergyFree', 'https://via.placeholder.com/100?text=Cetirizine'),
]

def create_connection():
    return psycopg2.connect(DATABASE_URL)

def reset_table():
    with create_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS medicines;")
            cur.execute("""
            CREATE TABLE medicines (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                price NUMERIC(10,2),
                stock INT,
                manufacturer VARCHAR(255),
                image TEXT
            );
            """)
            conn.commit()
            print("✅ Table dropped and recreated.")

def insert_new_data():
    with create_connection() as conn:
        with conn.cursor() as cur:
            for med in medicines:
                cur.execute("""
                INSERT INTO medicines (name, description, price, stock, manufacturer, image)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
                """, med)
            conn.commit()
            print("✅ New items inserted (existing skipped).")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_table()
    insert_new_data()
