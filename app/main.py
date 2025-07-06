from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

app = FastAPI()

# Enable CORS if frontend served on different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()  # loads .env from current working directory

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.get("/api/medicines")
def read_medicines():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, stock, manufacturer FROM medicines ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    medicines = []
    for r in rows:
        medicines.append({
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "price": float(r[3]),
            "stock": r[4],
            "manufacturer": r[5]
        })
    return medicines

# Optional: serve a simple frontend page
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Pharmacy Medicines</title></head>
    <body>
    <h1>Medicines List</h1>
    <ul id="medicines-list"></ul>

    <script>
      async function loadMedicines() {
        const res = await fetch('/api/medicines');
        if (!res.ok) {
          document.getElementById('medicines-list').textContent = 'Failed to load medicines';
          return;
        }
        const medicines = await res.json();
        const ul = document.getElementById('medicines-list');
        ul.innerHTML = '';
        medicines.forEach(med => {
          const li = document.createElement('li');
          li.textContent = `${med.name} - ${med.description} - $${med.price} - Stock: ${med.stock}`;
          ul.appendChild(li);
        });
      }
      loadMedicines();
    </script>
    </body>
    </html>
    """
