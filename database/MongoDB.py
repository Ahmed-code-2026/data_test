from pymongo import MongoClient
import pandas as pd

# client = MongoClient(
#     "mongodb://localhost:27017/"
# )
# db = client["University"]
# student = db["Student"]


# for document in student.find():
#     print(document)
df = pd.read_csv("C:/Users/Ahmed/Desktop/student_data_pipeline/data/processed/books_dataset.csv")

client = MongoClient("mongodb://localhost:27017/")

db = client["University"]

collection = db["books"]

data = df.to_dict("records")
collection.insert_many(data)

print("OK")