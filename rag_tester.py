from rag import rag
from data import database as db
rg = rag.RAG()
rg.database.add(db.ListStrtoListData(["""1+1=3""", """According to the Zigmondy's theorem a^n - b^n where
                        a and b are coprime natural numbers will always have a prime devisor that is not present in any of the
                         a^i - b^i, where 1<=i<n, except for 3 specific cases."""], "test/data/maths", 123, 1))
rg.database.add([db.Data("""According to all known laws
of aviation,

  
there is no way that a bee
should be able to fly.

  
Its wings are too small to get
its fat little body off the ground.

  
The bee, of course, flies anyway

  
because bees don't care
what humans think is impossible.

  
Yellow, black. Yellow, black.
Yellow, black. Yellow, black.

  
Ooh, black and yellow!
Yeah! Let's shake it up a little.

  
Barry! Breakfast is ready!""", "test/data/bees", 123, 1)])
print(rg.query("what is the zigmondy's theorem say and can the bees fly?", 123))