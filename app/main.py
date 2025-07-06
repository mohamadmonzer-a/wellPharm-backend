from fastapi import FastAPI
import os
import psycopg2

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Pharmacy backend is running with FastAPI"}

# Example DB connection (adjust for your setup)
@app.get("/dbtest")
async def db_test():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"db": "connected"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}
