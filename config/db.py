from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["financial_close"]

transactions_collection = db["transactions"]
matches_collection = db["matches"]
journal_collection = db["journal_entries"]
audit_collection = db["audit_logs"]