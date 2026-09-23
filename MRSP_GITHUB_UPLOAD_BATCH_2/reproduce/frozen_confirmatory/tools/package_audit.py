from __future__ import annotations
import argparse,csv,time,zipfile,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from code.common import read_json,write_json,sha256

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',default=str(ROOT/'w'));a=ap.parse_args();work=Path(a.work);res=work/'FULL/study_result.json'
    if not res.exists():raise SystemExit('FULL_RESULT_MISSING')
    x=read_json(res);ass=x.get('spec_assertions',{})
    if x.get('execution_status')!='RUN_PASS' or x.get('semantic_status')!='SEMANTIC_PASS':raise SystemExit('FULL_NOT_RELEASEABLE')
    needed={'p1_formula_frozen':True,'p1_cutoffs_recalibrated':False,'prior_gen1_groups_excluded':True,'selection_uses_week_le_22_only':True,'w3_w6_outcomes_used_for_selection':False,'b2_used':False,'learned_gate_used':False,'representative_and_challenge_disjoint':True}
    for k,v in needed.items():
        if ass.get(k)!=v:raise SystemExit('SPEC_ASSERTION_FAIL:'+k)
    sp=work/'state.json';state=read_json(sp);staged=dict(state);runid=time.strftime('%Y%m%d_%H%M%S');stage=work/'_audit_stage'
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for rel in ['cfg','code','tools','test','review','README.md','START.md','START_PROMPT.txt','CONTRACT.md','PACKAGE_INFO.json','SPEC_TRACE.csv','MANIFEST.csv','GATE_ACCEPT.md','SIMULATION_REVIEW.md']:
        p=ROOT/rel
        if not p.exists():continue
        d=stage/rel
        if p.is_dir():shutil.copytree(p,d,ignore=shutil.ignore_patterns('__pycache__'))
        else:d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    for rel in ['preflight.json','logs','repair_log.md','materialized/materialization_registry.json','materialized/selected_confirmatory_sets.json','materialized/candidate_pool_registry.parquet','materialized/candidate_pool_registry.csv.gz']:
        p=work/rel
        if p.exists():
            d=stage/'w'/rel
            if p.is_dir():shutil.copytree(p,d,ignore=shutil.ignore_patterns('__pycache__'))
            else:d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    fd=stage/'w/FULL';fd.mkdir(parents=True,exist_ok=True)
    for pat in ['study_result.json','summary.json','checkpoint.json','spec_assertions.json','selected_counts.json','confirmation_scorecard.json','event_panel.*','policy_results.*','action_map.*','product_summary.*','cohort_summary.*','department_summary.*','product_bootstrap.*']:
        for p in (work/'FULL').glob(pat):shutil.copy2(p,fd/p.name)
    staged['status']='AUDIT_PACKAGED';staged['audit_packaged_at']=time.time();write_json(stage/'w/state.json',staged);write_json(stage/'manifest.json',{'campaign':'MRSP_PREDICTABILITY_CONFIRMATORY_V1','run_id':runid,'raw_consumer_data_included':False,'state_in_archive':'AUDIT_PACKAGED'})
    rows=[]
    for p in sorted(stage.rglob('*')):
        if p.is_file():rows.append({'path':str(p.relative_to(stage)).replace('\\','/'),'size':p.stat().st_size,'sha256':sha256(p)})
    with (stage/'sha256.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['path','size','sha256']);w.writeheader();w.writerows(rows)
    z=ROOT/f'MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_{runid}.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as zz:
        for p in sorted(stage.rglob('*')):
            if p.is_file():zz.write(p,Path('MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT')/p.relative_to(stage))
    with zipfile.ZipFile(z) as zz:
        bad=zz.testzip()
    if bad:raise RuntimeError('ZIP_BAD:'+bad)
    write_json(sp,staged);print({'status':'PASS','audit_zip':str(z),'sha256':sha256(z),'files_hashed':len(rows)})
if __name__=='__main__':main()
