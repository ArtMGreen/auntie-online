from datetime import datetime

from pymongo import MongoClient

MONGO_ADDRESS = "mongodb://localhost:27017/"
DB_NAME = "messages"

db = MongoClient(MONGO_ADDRESS)[DB_NAME]


def write_data(
    user: str,
    message: str,
    reply: str,
) -> None:
    collection = db[user]
    data = {
        "user": user,
        "message": message,
        "reply": reply,
        "timestamp": datetime.now(),
    }
    collection.insert_one(data)


def read_data(user: str, query: dict | None = None) -> list[dict]:
    collection = db[user]
    if query is None:
        query = {}
    results = collection.find(query)
    return list(results)
