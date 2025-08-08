from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test_route():
    return {"message": "Тест успешен!", "status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_app:app", host="0.0.0.0", port=8000, reload=True)