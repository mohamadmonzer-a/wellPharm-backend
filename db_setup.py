import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()  # loads .env file

DATABASE_URL = os.getenv("DATABASE_URL")

def create_table_and_insert_data():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price NUMERIC(10,2),
        stock INT,
        manufacturer VARCHAR(255)
    );
    """)

    # Insert sample data
    cur.execute("""
    INSERT INTO medicines (name, description, price, stock, manufacturer)
    VALUES
        ('Paracetamol', 'Pain reliever', 3.50, 100, 'Acme Pharma'),
        ('Ibuprofen', 'Anti-inflammatory', 4.20, 50, 'HealthCorp'),
        ('Vitamin C', 'Supplement', 5.00, 75, 'NutraHealth'),
        ('Amoxicillin', 'Antibiotic', 10.00, 40, 'MediLab'),
        ('Cetirizine', 'Antihistamine', 7.00, 60, 'AllergyFree')
    ON CONFLICT DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Table created and sample data inserted successfully.")

if __name__ == "__main__":
    create_table_and_insert_data()
