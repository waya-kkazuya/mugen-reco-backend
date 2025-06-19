from fastapi import FastAPI
from database import get_dynamodb_client

app = FastAPI()

dynamodb = get_dynamodb_client()


@app.get("/")
def read_root():
    return {"message": "Welcome to Fast API"}

@app.get("/ping-dynamodb")
def ping_dynamodb():
    try:
        tables = dynamodb.list_tables()
        return {"status": "ok", "tables": tables.get("TableNames", [])}
    except Exception as e:
        return {"status": "error", "message": str(e)}