#!/usr/bin/env python3
"""MRSP V1 strict external replication runner.

Input is a canonical event table plus a pre-frozen six-SKU group manifest.
The runner itself constructs all pre-event B1/P1 quantities, tunes B1 only
with the frozen lambda grid inside the frozen walk-forward TUNE windows,
applies the previously frozen P1 cutoffs, and returns aggregate statistics.

Python standard library only. No household identifiers or event-level rows are
written to the output.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "MRSP_EXTERNAL_STRICT_ZERO_SHOT_V1"
PROTOCOL_VERSION = "1.0.0"
J = 6
LAMBDA_GRID = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 40.0]
CUTOFFS = {"0.6": 0.3608488067145302, "0.7": 0.5231119438280639, "0.8": 0.6660270791857679}
BLOCKS = [
    {"id":"W1","fit_max":17,"tune_min":18,"tune_max":22,"eval_min":23,"eval_max":27},
    {"id":"W2","fit_max":22,"tune_min":23,"tune_max":27,"eval_min":28,"eval_max":32},
    {"id":"W3","fit_max":27,"tune_min":28,"tune_max":32,"eval_min":33,"eval_max":37},
    {"id":"W4","fit_max":32,"tune_min":33,"tune_max":37,"eval_min":38,"eval_max":42},
    {"id":"W5","fit_max":37,"tune_min":38,"tune_max":42,"eval_min":43,"eval_max":47},
    {"id":"W6","fit_max":42,"tune_min":43,"tune_max":47,"eval_min":48,"eval_max":53},
]
EVAL_BLOCKS = {"W3", "W4", "W5", "W6"}
EVENT_COLUMNS = ["event_id","household_id","event_time","week_index","product_group_id","target_sku"]
GROUP_COLUMNS = ["product_group_id","department","sku_0","sku_1","sku_2","sku_3","sku_4","sku_5"]


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def parse_time(s: str) -> datetime:
    s=s.strip()
    if s.endswith('Z'): s=s[:-1]+'+00:00'
    return datetime.fromisoformat(s)


def coarse_bin(k: int) -> str:
    if k <= 2: return "0_2"
    if k <= 9: return "3_9"
    return "10_plus"


def entropy_top(counts: list[float]) -> tuple[float,float]:
    k=sum(counts)
    if k <= 0: return 0.0, 1.0
    p=[c/k for c in counts]
    nz=[x for x in p if x>0]
    h=-sum(x*math.log(x) for x in nz)
    return h/math.log(J), max(p)


def p1_score(k: int, top: float, ent: float, sw: float, recent_conc: float) -> float:
    maturity=min(1.0,max(0.0,math.log1p(k)/math.log(21.0)))
    core=.30*top+.25*(1-ent)+.25*(1-sw)+.20*recent_conc
    return min(1.0,max(0.0,maturity*core))


def read_groups(path: Path) -> tuple[dict[str,dict[str,Any]],list[str]]:
    failures=[]; groups={}
    try:
        with path.open(newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f)
            if (rd.fieldnames or []) != GROUP_COLUMNS:
                return {}, ["groups_header_mismatch: expected="+','.join(GROUP_COLUMNS)]
            for i,r in enumerate(rd,2):
                gid=r['product_group_id'].strip(); dept=r['department'].strip()
                skus=[r[f'sku_{j}'].strip() for j in range(J)]
                if not gid: failures.append(f"groups_row_{i}: blank product_group_id"); continue
                if gid in groups: failures.append(f"groups_row_{i}: duplicate product_group_id={gid}"); continue
                if any(not x for x in skus) or len(set(skus))!=J:
                    failures.append(f"groups_row_{i}: six distinct nonblank SKUs required for {gid}"); continue
                groups[gid]={"department":dept,"skus":skus,"sku_to_idx":{s:j for j,s in enumerate(skus)}}
    except Exception as e:
        failures.append("groups_read_error: "+repr(e))
    if not groups and not failures: failures.append("groups_empty")
    return groups, failures


def read_events(path: Path, groups: dict[str,dict[str,Any]]) -> tuple[list[dict[str,Any]],list[str]]:
    failures=[]; rows=[]; seen=set(); hh_time=set()
    try:
        with path.open(newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f)
            if (rd.fieldnames or []) != EVENT_COLUMNS:
                return [], ["events_header_mismatch: expected="+','.join(EVENT_COLUMNS)]
            for i,r in enumerate(rd,2):
                try:
                    eid=r['event_id'].strip(); hid=r['household_id'].strip(); gid=r['product_group_id'].strip(); sku=r['target_sku'].strip()
                    if not eid or not hid or not gid or not sku: raise ValueError('blank required value')
                    if eid in seen: raise ValueError('duplicate event_id')
                    seen.add(eid)
                    if gid not in groups: raise ValueError('unknown product_group_id')
                    if sku not in groups[gid]['sku_to_idx']: raise ValueError('target_sku not in frozen six-SKU group')
                    w=int(r['week_index'])
                    if w < 1 or w > 53: raise ValueError('week_index must be in 1..53')
                    t=parse_time(r['event_time'])
                    amb=(gid,hid,t.isoformat())
                    if amb in hh_time: raise ValueError('ambiguous duplicate household/group/event_time')
                    hh_time.add(amb)
                    rows.append({"event_id":eid,"household_id":hid,"event_time":t,"week":w,"group":gid,"y":groups[gid]['sku_to_idx'][sku]})
                except Exception as e:
                    failures.append(f"events_row_{i}: {e}")
    except Exception as e:
        failures.append("events_read_error: "+repr(e))
    # Check that week labels are temporally coherent globally: later timestamps cannot map to earlier weeks.
    if rows:
        z=sorted(rows,key=lambda x:(x['event_time'],x['event_id']))
        last_week=0
        for r in z:
            if r['week'] < last_week:
                failures.append('week_time_inversion: week_index decreases as event_time increases')
                break
            last_week=max(last_week,r['week'])
    return rows, failures


def build_features(rows: list[dict[str,Any]], gid: str) -> list[dict[str,Any]]:
    ev=sorted((r for r in rows if r['group']==gid), key=lambda x:(x['event_time'],x['event_id']))
    g=[0.0]*J; hh=defaultdict(lambda:[0.0]*J); last={}; switch_n=defaultdict(int); transition_n=defaultdict(int); recent=defaultdict(lambda:deque(maxlen=5))
    out=[]
    for r in ev:
        h=r['household_id']; y=r['y']; hc=list(hh[h]); k=int(sum(hc))
        other=[max(g[j]-hc[j],0.0)+1.0 for j in range(J)]; den=sum(other); mp=[x/den for x in other]
        ent,top=entropy_top(hc)
        lc=last.get(h,-1)
        sw=(switch_n[h]/transition_n[h]) if transition_n[h]>0 else 0.0
        if recent[h]:
            rc=[0]*J
            for q in recent[h]: rc[q]+=1
            recent_conc=max(rc)/len(recent[h])
        else: recent_conc=0.0
        out.append({"event_id":r['event_id'],"week":r['week'],"y":y,"k":k,"hh":hc,"mp":mp,"p1":p1_score(k,top,ent,sw,recent_conc)})
        # Current target mutates state only after its feature row is frozen.
        if lc>=0:
            transition_n[h]+=1
            if lc!=y: switch_n[h]+=1
        last[h]=y; recent[h].append(y); g[y]+=1.0; hh[h][y]+=1.0
    return out


def tune_lambdas(feat: list[dict[str,Any]], block: dict[str,int]) -> dict[str,float]:
    tune=[r for r in feat if block['tune_min'] <= r['week'] <= block['tune_max']]
    chosen={}; present=[]
    for b in ['0_2','3_9','10_plus']:
        q=[r for r in tune if coarse_bin(r['k'])==b]
        if not q: continue
        best_score=-1e99; best_lam=5.0
        for lam in LAMBDA_GRID:
            logs=[]
            for r in q:
                x=[lam*r['mp'][j]+r['hh'][j] for j in range(J)]; den=sum(x); p=max(x[r['y']]/den,1e-15)
                logs.append(math.log(p))
            score=sum(logs)/len(logs)
            if score>best_score: best_score=score; best_lam=float(lam)
        chosen[b]=best_lam; present.append(best_lam)
    fallback=float(statistics.median(present)) if present else 5.0
    for b in ['0_2','3_9','10_plus']:
        chosen.setdefault(b,fallback)
    return chosen


def argmax_first(xs: list[float]) -> int:
    return max(range(len(xs)),key=lambda i:xs[i])


def evaluate(rows: list[dict[str,Any]], groups: dict[str,dict[str,Any]]) -> dict[str,Any]:
    eval_rows=[]; group_eval_counts={}; data_limited=[]
    for gid in sorted(groups):
        feat=build_features(rows,gid)
        n_group=0
        for block in BLOCKS:
            if block['id'] not in EVAL_BLOCKS: continue
            lmap=tune_lambdas(feat,block)
            q=[r for r in feat if block['eval_min'] <= r['week'] <= block['eval_max']]
            for r in q:
                lam=lmap[coarse_bin(r['k'])]
                b1x=[lam*r['mp'][j]+r['hh'][j] for j in range(J)]
                b1=argmax_first(b1x); b0=argmax_first(r['mp'])
                eval_rows.append({"gid":gid,"dept":groups[gid]['department'],"block":block['id'],"p1":r['p1'],"b1_correct":int(b1==r['y']),"b0_correct":int(b0==r['y'])})
                n_group+=1
        group_eval_counts[gid]=n_group
        if n_group==0: data_limited.append(gid)
    total=len(eval_rows)
    out={
        "total_eval_events":total,
        "evaluated_groups":sum(1 for n in group_eval_counts.values() if n>0),
        "configured_groups":len(groups),
        "data_limited_groups":len(data_limited),
        "b0_all_accuracy":(sum(r['b0_correct'] for r in eval_rows)/total if total else None),
        "b1_all_accuracy":(sum(r['b1_correct'] for r in eval_rows)/total if total else None),
        "cutoffs":{},
        "by_department":{}
    }
    for label,cut in CUTOFFS.items():
        acc=[r for r in eval_rows if r['p1']>=cut]
        out['cutoffs'][label]={"cutoff":cut,"accepted_events":len(acc),"coverage":len(acc)/total if total else 0.0,"accuracy":sum(r['b1_correct'] for r in acc)/len(acc) if acc else None}
    depts=sorted(set(r['dept'] for r in eval_rows if r['dept']))
    for dept in depts:
        q=[r for r in eval_rows if r['dept']==dept]; d={"events":len(q),"b1_all_accuracy":sum(r['b1_correct'] for r in q)/len(q),"cutoffs":{}}
        for label,cut in CUTOFFS.items():
            a=[r for r in q if r['p1']>=cut]
            d['cutoffs'][label]={"accepted_events":len(a),"coverage":len(a)/len(q),"accuracy":sum(r['b1_correct'] for r in a)/len(a) if a else None}
        out['by_department'][dept]=d
    return out


def main() -> int:
    ap=argparse.ArgumentParser(description='Run frozen MRSP external replication from canonical events.')
    ap.add_argument('--events',type=Path,required=True)
    ap.add_argument('--groups',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    groups,fail_g=read_groups(args.groups)
    rows,fail_e=read_events(args.events,groups)
    failures=fail_g+fail_e
    metrics=evaluate(rows,groups) if not failures else {}
    if not failures and metrics.get('total_eval_events',0)==0:
        failures.append('no_evaluation_events_in_frozen_W3_W6_windows')
    code_path=Path(__file__).resolve()
    result={
        "protocol":PROTOCOL,
        "protocol_version":PROTOCOL_VERSION,
        "execution_status":"PASS" if not failures else "FAIL",
        "scientific_interpretation":"UNASSESSED_REQUIRES_HUMAN_REVIEW",
        "evidence_scope":"INDEPENDENT_EXTERNAL_ENVIRONMENT_ONLY_IF_INPUT_IS_INDEPENDENT_AND_PROTOCOL_WAS_FROZEN_BEFORE_OUTCOME_REVIEW",
        "adaptation_performed":False,
        "p1_cutoffs_recalibrated":False,
        "b2_used":False,
        "learned_gate_used":False,
        "input_manifest":{"events_sha256":sha256_file(args.events),"groups_sha256":sha256_file(args.groups)},
        "runner_sha256":sha256_file(code_path),
        "frozen":{"choice_set_size":6,"weeks":53,"evaluation_blocks":["W3","W4","W5","W6"],"lambda_grid":LAMBDA_GRID,"p1_cutoffs":CUTOFFS},
        "metrics":metrics,
        "failures":failures,
        "privacy":{"household_ids_written":False,"event_level_rows_written":False}
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding='utf-8')
    print('MRSP_EXTERNAL_RUN_'+result['execution_status'])
    return 0 if not failures else 2

if __name__=='__main__': raise SystemExit(main())
