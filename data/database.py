import chromadb
import numpy as np
import httpx
import asyncio
from chromadb import Documents, EmbeddingFunction, Embeddings
import sqlite3
import time
import hashlib

DEBUG = False

class CustomEmbedder(chromadb.EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = [[0.0]]
        return embeddings


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
    def tostr(self):
        return f"'{self.text}', {self.toSql("hash")[1:]}"
    

def hash(data:Data)->str:
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
            if(DEBUG):print(f"INSERT INTO database VALUES {data.toSql(NEWHASH)}")
            self.cur.execute(f"INSERT INTO database VALUES {data.toSql(NEWHASH)}")
            self.collection.upsert(ids=[NEWHASH], documents=[data.text])
            if(DEBUG):print(NEWHASH)
        self.sqldb.commit()

    def get(self, text:str, chat_id:int, count:int=10, label:str=None) -> list[Data]:
        print(f"SELECT id FROM database WHERE chat_id={chat_id} AND label='{label}'")
        query = self.cur.execute(f"SELECT id FROM database WHERE chat_id={chat_id} AND label='{label}'")
        result = query.fetchall()
        ids = []
        for i in result:
            ids.append(str(i[0]))
        if(DEBUG):print(ids)
        if(len(ids)==0):
            return []
        chromaquery = self.collection.query(ids=ids, query_texts=text)
        dataoutput = []
        for i in range(len(chromaquery["ids"][0])):
            if(DEBUG):print(f"SELECT * FROM database WHERE id='{chromaquery["ids"][0][i]}'")
            sqlquery = self.cur.execute(f"SELECT * FROM database WHERE id='{chromaquery["ids"][0][i]}'")
            sqlresult = sqlquery.fetchall()
            dataoutput.append(Data(chromaquery["documents"][0][i],
                                   sqlresult[0][1], sqlresult[0][2],
                                     sqlresult[0][3], sqlresult[0][4],
                                       sqlresult[0][5]))
        return dataoutput
    
    def remove(self, message_id:int, chat_id:int):
        if(DEBUG): print(f"SELECT id FROM database WHERE chat_id={chat_id} AND message_id={message_id}")
        query = self.cur.execute(f"SELECT id FROM database WHERE chat_id={chat_id} AND message_id={message_id}")
        result = query.fetchall()
        ids = []
        for i in result:
            ids.append(str(i[0]))
        if(DEBUG):print(ids)
        if(len(ids)==0):
            return
        self.cur.execute(f"DELETE FROM database WHERE message_id={message_id}")
        self.sqldb.commit()
        self.collection.delete(ids=ids)
if __name__ == "__main__":
    # test = CustomEmbedder()
    # out = test.__call__(["hi"])
    # print(out)


    database = Database()
    #database.add([Data("hey", "ho", 123, 128), Data("hah", "ho", 123, 126)])
    #database.remove(126, 123)
    print(database.collection.query(query_texts=["hi"]))
    for i in database.get("hi", 123):
        print(i.tostr())