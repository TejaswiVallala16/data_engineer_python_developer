import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# 1. Load your cleaned CSV
df = pd.read_csv("books_scrapper/books.csv")

# 2. Connection string from Atlas
MONGO_URI = os.getenv("MONGO_URI")

# 3. Connect to Atlas
client = MongoClient(MONGO_URI)

# 4. Choose database & collection
db = client["books_db"]
collection = db["books"]

# 5. Optional: clear old data
collection.drop()

# 6. Insert documents
collection.insert_many(df.to_dict(orient="records"))

print(f"✅ Inserted {collection.count_documents({})} documents into MongoDB Atlas!")