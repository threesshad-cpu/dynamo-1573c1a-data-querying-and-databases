import codecs

with codecs.open('failed.log', 'r', 'utf-16le') as f:
    text = f.read()

with open('failed_utf8.log', 'w', encoding='utf-8') as out:
    out.write(text.replace('\ufeff', ''))
