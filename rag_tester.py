from rag import rag
from data import database as db
rg = rag.RAG()
#rg.database.add([db.Data("""1+1=3""", "test/data/maths", 123, 1)])
print(rg.query("what is (1+1)+1 equal to and can the bees fly?", 123))