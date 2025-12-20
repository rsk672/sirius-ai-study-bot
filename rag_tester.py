from rag import rag
from data import database as db
rg = rag.RAG()
# rg.database.add(db.ListStrtoListData(["""Первая мировая началась в 1932"""], "test/data/history", 123, 1))
# rg.database.add([db.Data("""Вторая мировая началась в 1941""", "test/data/historic", 123, 2)])
# rg.database.add([db.Data("""1+1=3""", "test/data/math", 123, 3)])
print(rg.query("когда была первая мировая", 123))