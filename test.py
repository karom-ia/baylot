from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    return {"message": "Тестовый маршрут работает!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)