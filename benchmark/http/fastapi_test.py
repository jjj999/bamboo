
from fastapi import FastAPI


app = FastAPI()


@app.get("/test")
def hello():
    return "Hello, World"
