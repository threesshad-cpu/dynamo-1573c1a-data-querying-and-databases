import json

with open('comments.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

with open('b1_out.txt', 'w', encoding='utf-8') as out:
    for comment in data['comments']:
        if "QC Review" in comment['body'] or "B1" in comment['body'] or "Ambiguous Rule" in comment['body']:
            out.write("FOUND COMMENT:\n")
            out.write(comment['body'])
            out.write("\n===================================\n")
