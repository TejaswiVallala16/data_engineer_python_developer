import pandas as pd
import json

with open("books_scrapper/books.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Clean "prize" → float "price"
df["price"] = df["price"].str.replace("£", "").astype(float)

# Save as CSV for PostgreSQL
df.to_csv("books_scrapper/books.csv", index=False, encoding="utf-8")
print("Saved data to csv")