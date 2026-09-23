from pathlib import Path
import csv, importlib, re, sys
ROOT=Path(__file__).resolve().parents[1]
claims=(ROOT/'CLAIMS.md').read_text(encoding='utf-8')
for c in [f'C{i}' for i in range(1,9)]:
    assert c in claims, c
for r in ['R1','R2','R3','R6']:
    assert r in claims, r
assert 'R4' not in claims and 'R5' not in claims
# claim/evidence map
ledger={r['id'] for r in csv.DictReader((ROOT/'audit/RELEASE_EVIDENCE_LEDGER.csv').open(encoding='utf-8-sig'))}
for r in csv.DictReader((ROOT/'audit/CLAIM_TO_EVIDENCE_MAP.csv').open(encoding='utf-8-sig')):
    assert r['evidence_id'] in ledger, r
    assert (ROOT/r['public_file']).exists(), r
# exact frozen package completeness
for rel in ['go.bat','PACKAGE_INFO.json','MANIFEST.csv','code/data.py','code/models.py','code/predictability.py','cfg/frozen_p1_cutoffs.json','cfg/study.json']:
    assert (ROOT/'reproduce/frozen_confirmatory'/rel).exists(), rel
# public source importability
sys.path.insert(0,str(ROOT))
import src.models, src.data, src.predictability
# privacy scan
bad=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() in {'.png','.zip','.parquet','.gz'}: continue
    try: s=p.read_text(encoding='utf-8')
    except Exception: continue
    needle1='C:'+chr(92)+'Users'+chr(92); needle2='oho'+'0o'
    if needle1 in s or needle2 in s: bad.append(str(p.relative_to(ROOT)))
assert not bad, bad
# Final-language scan in outward-facing docs
for rel in ['README.md','README_zh-TW.md','REPORT.md','REPORT_zh-TW.md','RELEASE_NOTES.md','RELEASE_VERSION']:
    s=(ROOT/rel).read_text(encoding='utf-8')
    assert 'Round 2 release candidate' not in s
    assert 'MRSP_PREDICTABILITY_RELEASE_V1_R2/' not in s
print('TEST_RELEASE_INTEGRITY_PASS')
