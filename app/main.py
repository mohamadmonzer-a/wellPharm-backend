from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Backend is running"}

@app.get("/products")
def get_products():
    return [
        {"id": 1, "name": "Paracetamol", "price": 3.5},
        {"id": 2, "name": "Vitamin C", "price": 5.0},
    ]
