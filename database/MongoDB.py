from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017/"
)
db = client["University"]
student = db["Student"]


for document in student.find():
    print(document)