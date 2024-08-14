from pymongo import MongoClient


client = MongoClient("mongodb://admin:%2Faksrldi09a!@localhost:27017/")
db = client["crm"]
