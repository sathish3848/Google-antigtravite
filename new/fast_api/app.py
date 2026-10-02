from fastapi import FastAPI
from enum import Enum

app = FastAPI()

@app.get("/")
def read_root():
    return {"text": "sathish"}


@app.get("/items/")
def sk(skip:int = 0, limit: int=10 ,q : str | None = None):
    return {"skip" : skip, "limit" : limit, "q" : q}