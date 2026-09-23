from __future__ import annotations
import argparse,json,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from code.common import read_json,write_json,sha256
from code.materialize_confirmatory import materialize,_source_hashes

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--cj9');a=ap.parse_args();work=Path(a.work);work.mkdir(parents=True,exist_ok=True);cfg=read_json(ROOT/'cfg/roots.json');cj9=Path(a.cj9 or cfg['cj9']);mat=work/'materialized';regp=mat/'materialization_registry.json'
    if regp.exists():
        reg=read_json(regp);cur=_source_hashes(cj9);curmap={(x['path'],x['size'],x['sha256']) for x in cur};oldmap={(x['path'],x['size'],x['sha256']) for x in reg.get('source_hashes',[])}
        if curmap!=oldmap:raise RuntimeError('MATERIALIZED_SOURCE_IDENTITY_MISMATCH')
        if reg.get('materializer_sha256')!=sha256(ROOT/'code/materialize_confirmatory.py'):raise RuntimeError('MATERIALIZER_IDENTITY_MISMATCH')
        if reg.get('roots_cfg_sha256')!=sha256(ROOT/'cfg/roots.json') or reg.get('frozen_prior_sha256')!=sha256(ROOT/'cfg/frozen_gen1_selected.json'):raise RuntimeError('MATERIALIZER_CONFIG_IDENTITY_MISMATCH')
    else:
        mat.mkdir(parents=True,exist_ok=True);reg=materialize(cj9,mat)
    specs=read_json(mat/'selected_confirmatory_sets.json');prior=read_json(ROOT/'cfg/frozen_gen1_selected.json');prior_keys={x['stable_key'] for x in prior['selected']};rep=[x for x in specs if x['cohort']=='REPRESENTATIVE'];dep=[x for x in specs if x['cohort']=='DEPARTMENT_CHALLENGE'];allkeys=[x['stable_key'] for x in specs]
    selected_checks=[]
    for s in specs:
        base=mat/'cat'/s['source_set'];meta=base/'meta.json';ev=base/'events.parquet' if (base/'events.parquet').exists() else base/'events.csv.gz' if (base/'events.csv.gz').exists() else base/'events.csv'
        selected_checks.append({'set_id':s['id'],'cohort':s['cohort'],'department':s['department'],'stable_key':s['stable_key'],'meta_sha256':sha256(meta),'events_sha256':sha256(ev),'events_size':ev.stat().st_size})
    structural={'source_exists':cj9.exists(),'pool_exact_expected':int(reg['pool_summary']['pool_after_dedup'])==int(cfg['expected_candidate_pool']),'prior_reconstruction_exact':True,'representative_exact_n':len(rep)==int(cfg['representative_n']),'challenge_min_n':len(dep)>=int(cfg['department_challenge_min_n']),'challenge_cap_n':len(dep)<=int(cfg['department_challenge_target_n']),'selected_unique':len(allkeys)==len(set(allkeys)),'no_prior_overlap':not bool(set(allkeys)&prior_keys),'future_outcome_free_selection':reg.get('future_outcome_used_for_selection') is False,'p1_not_recalibrated':reg.get('p1_recalibrated') is False}
    status='PASS' if all(structural.values()) else 'SEMANTIC_FAIL';repout={'status':status,'campaign':'MRSP_PREDICTABILITY_CONFIRMATORY_V1','platform':platform.platform(),'python':sys.version,'source_cj9':str(cj9),'pool_summary':reg['pool_summary'],'selection_summary':reg['selection_summary'],'n_selected':len(specs),'n_representative':len(rep),'n_department_challenge':len(dep),'structural':structural,'selected_sets':selected_checks,'source_hashes':reg['source_hashes'],'cfg_hashes':{p.name:sha256(p) for p in (ROOT/'cfg').glob('*.json')}};write_json(work/'preflight.json',repout);print(json.dumps(repout,ensure_ascii=False,indent=2));raise SystemExit(0 if status=='PASS' else 42)
if __name__=='__main__':main()
