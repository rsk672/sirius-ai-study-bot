from splitter.splitter import Splitter
model = Splitter()
with open("splitter_tester_input.txt", "r", encoding="utf-8") as q:
    lines = q.readlines()
    text = ""
    for line in lines:
        text += line
        text += "\n"
    query = model.query(text)
    print(query.batches)