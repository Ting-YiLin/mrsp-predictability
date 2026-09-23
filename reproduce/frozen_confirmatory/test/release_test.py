from __future__ import annotations
from pathlib import Path
import tempfile,shutil,subprocess,sys,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
tmp=Path(tempfile.mkdtemp(prefix='confirm_exec_'))
try:
    pkg=tmp/'pkg';shutil.copytree(ROOT,pkg,ignore=shutil.ignore_patterns('w','__pycache__','MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_*.zip','MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE_*.zip'))
    data=tmp/'cj9';subprocess.check_call([sys.executable,str(pkg/'test/make_synth_cj9.py'),'--out',str(data),'--groups','40'])
    sys.path.insert(0,str(pkg));from code.materialize_confirmatory import build_candidate_pool
    legacy=json.loads((pkg/'cfg/legacy_panel.json').read_text(encoding='utf-8'))
    pool,_=build_candidate_pool(data,legacy,20,8);assert len(pool)==40,len(pool)
    ordered=sorted(pool,key=lambda x:x['stable_key']);prior=ordered[:10]
    (pkg/'cfg/frozen_gen1_selected.json').write_text(json.dumps({'source_campaign':'SYNTH','n':10,'selected':[{'stable_key':x['stable_key']} for x in prior]},indent=2)+'\n',encoding='utf-8')
    roots=json.loads((pkg/'cfg/roots.json').read_text());roots.update({'cj9':str(data),'expected_candidate_pool':40,'expected_prior_gen1':10,'representative_n':12,'department_challenge_target_n':12,'department_challenge_min_n':8,'min_pre_events':20,'min_pre_households':8,'department_challenge_caps':{'GROCERY':3,'__default__':4}});(pkg/'cfg/roots.json').write_text(json.dumps(roots,indent=2)+'\n')
    study=json.loads((pkg/'cfg/study.json').read_text());study['min_representative_evaluated_products']=5;study['min_challenge_evaluated_products']=5;study['min_product_prior_events']=20;study['min_subset_prior_events']=5;study['product_bootstrap_reps']=50;(pkg/'cfg/study.json').write_text(json.dumps(study,indent=2)+'\n')
    w=tmp/'w';cmd=[sys.executable,str(pkg/'tools/run_pipeline.py'),'--work',str(w),'--cj9',str(data),'--skip-tests'];subprocess.check_call(cmd,cwd=pkg)
    res=json.loads((w/'FULL/study_result.json').read_text());assert res['execution_status']=='RUN_PASS' and res['semantic_status']=='SEMANTIC_PASS';assert res['selected_counts']['representative_selected']==12;assert res['selected_counts']['challenge_selected']>=8
    # Normal resume must not recompute/mix completed sets.
    cp0=json.loads((w/'FULL/checkpoint.json').read_text());subprocess.check_call(cmd,cwd=pkg);cp1=json.loads((w/'FULL/checkpoint.json').read_text());assert cp0['completed_sets']==cp1['completed_sets']
    # Core config change must refuse old state.
    study['target_tolerance_pp']=4.0;(pkg/'cfg/study.json').write_text(json.dumps(study,indent=2)+'\n');p=subprocess.run(cmd,cwd=pkg,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert p.returncode!=0 and 'RESUME_IDENTITY_MISMATCH' in p.stdout,p.stdout[-4000:]
    # Audit ZIP from successful runs must be healthy.
    zs=sorted(pkg.glob('MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_*.zip'));assert zs
    with zipfile.ZipFile(zs[-1]) as z:assert z.testzip() is None
    print('RELEASE_TEST_PASS',res['confirmation_grade'])
finally:shutil.rmtree(tmp,ignore_errors=True)
