import json

with open('comments.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

with open('parsed.txt', 'w', encoding='utf-8') as out:
    for comment in reversed(data['comments']):
        if "tier1-addressal" in comment['body'] or "## 🚦 Tier-1" in comment['body'] or "QC Review" in comment['body'] or "## 🔬" in comment['body']:
            out.write("FOUND COMMENT:\n")
            out.write(comment['body'])
            out.write("\n" + "-" * 80 + "\n")
