from __future__ import annotations
import csv,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'SPEC_TRACE.csv').open(encoding='utf-8-sig')));bad=[]
for r in rows:
    for role in ['spec_file','implementation_file','evidence_file']:
        p=ROOT/r[role]
        if not p.exists():bad.append((r['rule_id'],role,'MISSING',r[role]))
    ip=ROOT/r['implementation_file'];ep=ROOT/r['evidence_file']
    if ip.exists() and r.get('implementation_anchor') and r['implementation_anchor'] not in ip.read_text(encoding='utf-8-sig',errors='replace'):bad.append((r['rule_id'],'implementation_anchor',r['implementation_anchor']))
    if ep.exists() and r.get('evidence_anchor') and r['evidence_anchor'] not in ep.read_text(encoding='utf-8-sig',errors='replace'):bad.append((r['rule_id'],'evidence_anchor',r['evidence_anchor']))
if bad:print('SPEC_TRACE_FAIL',bad);raise SystemExit(2)
print('SPEC_TRACE_PASS',len(rows))
