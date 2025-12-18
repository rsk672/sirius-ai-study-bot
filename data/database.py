import chromadb
import sqlite3
from chromadb import CollectionMetadata
import time
import hashlib

class Data:
    def __init__(self, text:str, path:str, chat_id:int, message_id:int, time:int=0, label:str="None"):
        self.path = path
        self.text = text
        self.chat_id = chat_id
        self.time = time
        self.label = label
        self.message_id = message_id
    def toSql(self, hash):
        return f"('{hash}', '{self.path}', {self.chat_id}, {self.message_id}, {self.time}, '{self.label}')"

def hash(data:Data):
    HASH = "iag!@#1239s0df0sde??|9kudfrlkhgovb040259jf@#!#!esksekies"
    hashstr = data.text+str(data.chat_id)+str(data.message_id)+data.path+str(data.time)+str(time.time_ns())+HASH
    return hashlib.sha256(bytes(hashstr, encoding='utf-8')).hexdigest()

class Database:
    def __init__(self):
        self.sqldb = sqlite3.connect("sql.db")
        self.cur = self.sqldb.cursor()
        self.client = chromadb.PersistentClient()
        self.collection = self.client.get_or_create_collection(name="inner_db")
        self.sqldb.execute("CREATE TABLE IF NOT EXISTS database"
        " (id text, path text, chat_id int, message_id int, time int, label text)")
    def add(self, datas:list[Data])->None:
        for data in datas:
            NEWHASH = hash(data)
            #print(f"INSERT INTO database VALUES {data.toSql(NEWHASH)}")
            self.cur.execute(f"INSERT INTO database VALUES {data.toSql(NEWHASH)}")
            self.collection.upsert(ids=[NEWHASH], documents=[data.text])
            print(NEWHASH)
        self.sqldb.commit()
    def get(self, text:str, chat_id:int, count:int=10, label:str=None):
        query = self.cur.execute(f"SELECT id FROM database WHERE chat_id={chat_id} AND label='{label}'")
        result = query.fetchall()
        ids = []
        for i in result:
            ids.append(str(i[0]))
        # ids = list(set(ids)) #remove later
        print(ids)

        return self.collection.query(ids=ids, query_texts=text)
    
if __name__ == "__main__":
    database = Database()
    #database.add([Data("hi", "ho", 123, 124)])
    print(database.get("hi", 123))