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
    def __init__(self, text:str, path:str, chat_id:int, message_id:int, file_name:str=str(time.time_ns()), time:int=0, label:str="None"):
        self.path = path
        self.text = text
        self.chat_id = chat_id
        self.time = time
        self.label = label
        self.message_id = message_id
        self.file_name = file_name
    def toSql(self):
        return f"('{self.path}', {self.chat_id}, {self.message_id}, '{self.file_name}', {self.time}, '{self.label}')"
    def toStr(self):
        return f"('{self.text}', {self.toSql()[1:]}"    

def ListStrtoListData(strings:list[str], path:str, chat_id:int,
                       message_id:int, file_name:str=str(time.time_ns()), time:int=0, label:str="None")->list[Data]:
    datas = []
    for string in strings:
        datas.append(Data(string, path, chat_id, message_id, file_name, time, label))
    return datas

def hash(data:Data)->str:
    HASH = "iag!@#1239s0df0sde??|9kudfrlkhgovb040259jf@#!#!esksekies"
    hashstr = data.text+str(data.chat_id)+str(data.message_id)+data.path+str(data.time)+str(time.time_ns())+HASH
    return hashlib.sha256(bytes(hashstr, encoding='utf-8')).hexdigest()

class Database:
    def __init__(self):
        self.sqldb = sqlite3.connect("sql.db")
        self.cur = self.sqldb.cursor()
        self.client = chromadb.PersistentClient()
        self.collection = self.client.get_or_create_collection(name="inner_db", embedding_function=CustomEmbedder())
        self.sqldb.execute("CREATE TABLE IF NOT EXISTS database"
        " (path text, chat_id int, message_id int, file_name text, time int, label text)")
    def add(self, datas:list[Data])->None:
        if(DEBUG):print(f"INSERT INTO database VALUES {datas[0].toSql()}")
        self.cur.execute(f"INSERT INTO database VALUES {datas[0].toSql()}")
        for data in datas:
            NEWHASH = hash(data)
            self.collection.upsert(ids=[NEWHASH], documents=[data.text], metadatas=[{'path':data.path}])
            if(DEBUG):print(NEWHASH)
        self.sqldb.commit()

    def get(self, text:str, chat_id:int, count:int=10, label:str=None) -> list[Data]:
        if(DEBUG):print(f"SELECT id FROM database WHERE chat_id={chat_id} AND label='{label}'")
        query = self.cur.execute(f"SELECT path FROM database WHERE chat_id={chat_id} AND label='{label}'")
        result = query.fetchall()
        paths = []
        for i in result:
            paths.append(str(i[0]))
        if(DEBUG):print(paths)
        if(len(paths)==0):
            return []
        chromaquery = self.collection.query(query_texts=text, n_results=count, where={"path":{"$in":paths}})
        dataoutput = []
        for i in range(len(chromaquery["metadatas"][0])):
            if(DEBUG):print(f"SELECT * FROM database WHERE path='{chromaquery["metadatas"][0][i]["path"]}'")
            sqlquery = self.cur.execute(f"SELECT * FROM database WHERE path='{chromaquery["metadatas"][0][i]["path"]}'")
            sqlresult = sqlquery.fetchall()
            dataoutput.append(Data(chromaquery["documents"][0][i],
                                   sqlresult[0][0], sqlresult[0][1],
                                     sqlresult[0][2], sqlresult[0][3],
                                       sqlresult[0][4]))
        return dataoutput
    
    def remove(self, message_id:int, chat_id:int):
        if(DEBUG): print(f"SELECT path FROM database WHERE chat_id={chat_id} AND message_id={message_id}")
        query = self.cur.execute(f"SELECT path FROM database WHERE chat_id={chat_id} AND message_id={message_id}")
        result = query.fetchall()
        paths = []
        for i in result:
            paths.append(str(i[0]))
        if(DEBUG):print(paths)
        if(len(paths)==0):
            return
        self.cur.execute(f"DELETE FROM database WHERE message_id={message_id}")
        self.sqldb.commit()
        self.collection.delete(where={"path":{"$in":paths}})
    
    def path_to_name(self, chat_id:int, path:str):
        query = self.cur.execute(f"SELECT file_name from database WHERE chat_id={chat_id} AND path='{path}'")
        return query.fetchone()[0]