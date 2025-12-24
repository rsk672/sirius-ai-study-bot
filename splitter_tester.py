from splitter.splitter import Splitter
import asyncio
model = Splitter()
with open("splitter_tester_input.txt", "r", encoding="utf-8") as q:
    lines = q.read()
    print(asyncio.run(model.query(lines)))