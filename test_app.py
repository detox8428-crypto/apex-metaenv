from fastapi import FastAPI

app = FastAPI(title="Test App")

@app.get("/test")
def test():
    return {"status": "ok"}

@app.get("/hello")
def hello():
    return {"message": "hello"}
