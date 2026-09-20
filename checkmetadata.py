import csv
import re
from pathlib import Path

D = Path('data/ecommerce')
REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience']

mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D / 'sources.csv', encoding='utf-8')))

ids, auds = [], {}

for p in mds:
    text = p.read_text(encoding='utf-8')
    parts = text.split('---')
    fm_text = parts[1] if len(parts) >= 3 else ''
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
    
    doc_id = fm.get('doc_id', '').strip('"')
    ids.append(doc_id)
    
    aud = fm.get('audience', '').strip().strip('"')
    if aud:
        auds[aud] = auds.get(aud, 0) + 1
        
    ok = all(k in fm for k in REQ) and doc_id == p.stem
    status = "OK" if ok else "!!! THIEU METADATA !!!"
    print(f'{p.name:50} {status}')

print()
print('So file   :', len(mds), '(can 5-10)')
csv_ids = sorted(r['doc_id'] for r in rows)
print('CSV khop  :', 'OK' if csv_ids == sorted(ids) else '!!! LECH !!!')
print('Audience  :', auds)
print('Filter OK :', 'OK' if len(auds) >= 2 else '!!! CHI CO 1 GIA TRI, FILTER SE KHONG HOAT DONG !!!')