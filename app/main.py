from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def home():
    return {"message": "E-Commerce Backend is running"}