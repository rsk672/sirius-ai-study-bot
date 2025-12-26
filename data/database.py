from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass
from typing import List, Optional

import chromadb
from chromadb import Documents, Embeddings

from models.embedding_service import RemoteEmbeddingService
from utils.config import (
    MODEL,
    MODEL_DIMENSIONS,
    DB_DEBUG,
    SQL_DB_PATH,
    CHROMA_COLLECTION_NAME,
    DB_DEFAULT_LABEL,
    DB_HASH_SALT,
)


class RemoteEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Chroma embedding function that calls a remote embedding service.
    If the service fails, returns zero-vectors of the correct dimension.
    """

    def __init__(self):
        self.embedder = RemoteEmbeddingService()
        self.dimension = MODEL_DIMENSIONS.get(MODEL, 312)

    def __call__(self, input: Documents) -> Embeddings:
        try:
            return self.embedder.embed_documents(input)
        except Exception as e:
            if DB_DEBUG:
                print(f"Ошибка генерации эмбеддингов: {e}")
            return [[0.0] * self.dimension for _ in range(len(input))]


@dataclass
class Data:
    text: str
    path: str
    chat_id: int
    message_id: int
    file_name: str
    time: int = 0
    label: str = DB_DEFAULT_LABEL

    @staticmethod
    def default_file_name() -> str:
        return str(time.time_ns())


def list_str_to_list_data(
    strings: List[str],
    path: str,
    chat_id: int,
    message_id: int,
    file_name: Optional[str] = None,
    time_value: int = 0,
    label: str = DB_DEFAULT_LABEL,
) -> List[Data]:
    if file_name is None:
        file_name = Data.default_file_name()
    return [
        Data(
            text=s,
            path=path,
            chat_id=chat_id,
            message_id=message_id,
            file_name=file_name,
            time=time_value,
            label=label,
        )
        for s in strings
    ]


ListStrtoListData = list_str_to_list_data


def _chunk_id(data: Data) -> str:
    raw = (
        data.text
        + str(data.chat_id)
        + str(data.message_id)
        + data.path
        + str(data.time)
        + str(time.time_ns())
        + DB_HASH_SALT
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Database:
    def __init__(self, sql_path: str = SQL_DB_PATH):
        self.sqldb = sqlite3.connect(sql_path, check_same_thread=False)
        self.cur = self.sqldb.cursor()
        self._init_sql()

        self.client = chromadb.PersistentClient()
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=RemoteEmbeddingFunction(),
        )

    def _init_sql(self) -> None:
        self.sqldb.execute(
            "CREATE TABLE IF NOT EXISTS database ("
            "path TEXT, "
            "chat_id INTEGER, "
            "message_id INTEGER, "
            "file_name TEXT, "
            "time INTEGER, "
            "label TEXT"
            ")"
        )
        self.sqldb.commit()
        
    def isempty(self, chat_id:int) -> bool:
        query = self.cur.execute(f"SELECT COUNT() FROM database WHERE chat_id={chat_id}").fetchone()[0]
        return query == 0

    def add(self, datas: List[Data]) -> None:
        if not datas:
            return

        meta = datas[0]
        if DB_DEBUG:
            print(f"INSERT database meta: {meta}")

        self.cur.execute(
            "INSERT INTO database (path, chat_id, message_id, file_name, time, label) VALUES (?, ?, ?, ?, ?, ?)",
            (meta.path, meta.chat_id, meta.message_id, meta.file_name, meta.time, meta.label),
        )

        for d in datas:
            cid = _chunk_id(d)
            self.collection.upsert(
                ids=[cid],
                documents=[d.text],
                metadatas=[{"path": d.path}],
            )

        self.sqldb.commit()

    def get(
        self,
        text: str,
        chat_id: int,
        count: int = 10,
        label: Optional[str] = None,
    ) -> List[Data]:
        label_value = label if label is not None else DB_DEFAULT_LABEL

        q = self.cur.execute(
            "SELECT path FROM database WHERE chat_id=? AND label=?",
            (chat_id, label_value),
        )
        paths = [row[0] for row in q.fetchall()]
        if DB_DEBUG:
            print(f"paths={paths}")

        if not paths:
            return []

        chromaquery = self.collection.query(
            query_texts=text,
            n_results=count,
            where={"path": {"$in": paths}},
        )

        docs = chromaquery.get("documents", [[]])[0]
        metas = chromaquery.get("metadatas", [[]])[0]
        if not docs or not metas:
            return []

        out: List[Data] = []
        for doc_text, meta in zip(docs, metas):
            path = meta.get("path")
            if not path:
                continue

            sqlq = self.cur.execute(
                "SELECT path, chat_id, message_id, file_name, time, label FROM database WHERE path=? LIMIT 1",
                (path,),
            )
            row = sqlq.fetchone()
            if not row:
                continue

            out.append(
                Data(
                    text=doc_text,
                    path=row[0],
                    chat_id=row[1],
                    message_id=row[2],
                    file_name=row[3],
                    time=row[4],
                    label=row[5],
                )
            )

        return out

    def remove(self, message_id: int, chat_id: int) -> List[str]:
        q = self.cur.execute(
            "SELECT path FROM database WHERE chat_id=? AND message_id=?",
            (chat_id, message_id),
        )
        paths = [row[0] for row in q.fetchall()]
        if DB_DEBUG:
            print(f"remove paths={paths}")

        if not paths:
            return []

        self.cur.execute(
            "DELETE FROM database WHERE chat_id=? AND message_id=?",
            (chat_id, message_id),
        )
        self.sqldb.commit()

        self.collection.delete(where={"path": {"$in": paths}})
        return paths

    def path_to_name(self, chat_id: int, path: str) -> str:
        q = self.cur.execute(
            "SELECT file_name FROM database WHERE chat_id=? AND path=? LIMIT 1",
            (chat_id, path),
        )
        row = q.fetchone()
        return row[0] if row else "document"
