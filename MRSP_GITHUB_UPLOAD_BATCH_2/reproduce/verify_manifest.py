from pathlib import Path
import csv,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
rows=list(csv.DictReader((ROOT/'audit/MANIFEST.csv').open(encoding='utf-8-sig')))
bad=[]
for r in rows:
    p=ROOT/r['path']
    if not p.exists() or sha(p)!=r['sha256']: bad.append(r['path'])
if bad:
    print('MANIFEST_FAIL',*bad,sep='\n'); raise SystemExit(2)
print('MANIFEST_PASS',len(rows))
