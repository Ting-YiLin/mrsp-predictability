from __future__ import annotations
import hashlib,json
from pathlib import Path
from collections import defaultdict
import pandas as pd
from code.common import read_json,read_table,write_json,write_table,sha256

ROOT=Path(__file__).resolve().parents[1]

def htxt(s:str)->str:return hashlib.sha256(s.encode('utf-8')).hexdigest()

def _table_file(base:Path)->Path:
    if base.suffix and base.exists():return base
    for suf in ['.parquet','.csv.gz','.csv']:
        p=base.with_suffix(suf)
        if p.exists():return p
    raise FileNotFoundError(str(base))

def _read_weeks(cj9:Path,weeks,columns):
    frames=[]
    for w in weeks:
        q=read_table(cj9/'tx'/f'w{w:02d}',columns=columns)
        for c in ['household_id','basket_id','product_id']:
            if c in q:q[c]=q[c].astype(str)
        frames.append(q)
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=columns)

def _legacy_exclusions(panel:dict):
    ss=panel['primary_sets']+panel['control_sets']
    names={str(x['group_name']).strip().casefold() for x in ss}
    tuples={tuple(map(str,x['candidate_products'])) for x in ss}
    return names,tuples

def build_candidate_pool(cj9:Path,legacy_panel:dict,min_events:int=120,min_households:int=25):
    products=read_table(cj9/'products').copy()
    products['product_id']=products.product_id.astype(str)
    products['product_type']=products.product_type.fillna('').astype(str)
    products['department']=products.department.fillna('').astype(str)
    products=products.drop_duplicates('product_id')
    tx=_read_weeks(cj9,range(1,23),['household_id','basket_id','product_id','week'])
    support=tx.groupby('product_id').size().rename('pre_support')
    meta=products[products.product_type!=''].merge(support,left_on='product_id',right_index=True,how='left').fillna({'pre_support':0})
    meta=meta.sort_values(['product_type','pre_support','product_id'],ascending=[True,False,True],kind='mergesort')
    top=meta.groupby('product_type',sort=True).head(6)
    valid=top.groupby('product_type').size();top=top[top.product_type.isin(valid[valid==6].index)]
    joined=tx.merge(top[['product_id','product_type']],on='product_id',how='inner')
    basket_products=joined.groupby(['product_type','basket_id']).product_id.nunique()
    single_keys=basket_products[basket_products==1].reset_index()[['product_type','basket_id']]
    single=joined.merge(single_keys,on=['product_type','basket_id'],how='inner').drop_duplicates(['product_type','basket_id'])
    counts=single.groupby('product_type').agg(events_pre22=('basket_id','nunique'),households_pre22=('household_id','nunique'))
    legacy_names,legacy_tuples=_legacy_exclusions(legacy_panel)
    raw=[]
    for name,row in counts.iterrows():
        if int(row.events_pre22)<min_events or int(row.households_pre22)<min_households:continue
        sname=str(name)
        if 'GAS' in sname.upper() or 'FUEL' in sname.upper():continue
        group=top[top.product_type==sname].sort_values(['pre_support','product_id'],ascending=[False,True],kind='mergesort')
        pids=group.product_id.astype(str).tolist()
        if sname.strip().casefold() in legacy_names or tuple(pids) in legacy_tuples:continue
        mode=group.department.mode();dept=str(mode.iat[0]) if len(mode) else ''
        raw.append({'group_name':sname,'department':dept,'candidate_products':pids,'events_pre22':int(row.events_pre22),'households_pre22':int(row.households_pre22),'raw_stable_key':htxt('|'.join(['cj11',sname,*pids]))})
    raw.sort(key=lambda x:x['raw_stable_key'])
    keep=[];dups=0
    for item in raw:
        ss=set(item['candidate_products']);nk=item['group_name'].strip().casefold();dup=False
        for prior in keep:
            ps=set(prior['candidate_products']);pk=prior['group_name'].strip().casefold();jac=len(ss&ps)/max(len(ss|ps),1)
            if nk==pk or jac>=.50:dup=True;break
        if dup:dups+=1
        else:keep.append(item)
    for i,item in enumerate(keep,1):
        item['candidate_source_set']=f'POOL{i:03d}'
        item['stable_key']=htxt('|'.join(['cj11',item['candidate_source_set'],*item['candidate_products']]))
    return keep,{'pre22_rows':int(len(tx)),'raw_candidates':len(raw),'duplicates_removed':dups,'pool_after_dedup':len(keep)}

def select_confirmatory(pool:list[dict],frozen_prior:dict,cfg:dict):
    prior_expected=frozen_prior['selected']
    ordered=sorted(pool,key=lambda x:x['stable_key'])
    actual_first=ordered[:int(cfg['expected_prior_gen1'])]
    exp_keys=[x['stable_key'] for x in prior_expected];got_keys=[x['stable_key'] for x in actual_first]
    if got_keys!=exp_keys:raise RuntimeError('PRIOR_GEN1_RECONSTRUCTION_MISMATCH')
    prior=set(exp_keys);rem=[x.copy() for x in pool if x['stable_key'] not in prior]
    for x in rem:x['rep_hash']=htxt(cfg['representative_salt']+'|'+x['stable_key'])
    rep=sorted(rem,key=lambda x:x['rep_hash'])[:int(cfg['representative_n'])]
    repkeys={x['stable_key'] for x in rep};rem2=[x.copy() for x in rem if x['stable_key'] not in repkeys]
    by=defaultdict(list)
    for x in rem2:
        x['dept_hash']=htxt(cfg['department_salt']+'|'+x['stable_key']);by[x['department']].append(x)
    for dept in by:by[dept].sort(key=lambda x:x['dept_hash'])
    dept_order=sorted(by,key=lambda d:htxt(cfg['department_order_salt']+'|'+str(d)))
    caps=cfg['department_challenge_caps'];taken=defaultdict(int);challenge=[];target=int(cfg['department_challenge_target_n'])
    while len(challenge)<target:
        progress=False
        for dept in dept_order:
            cap=int(caps.get(dept,caps.get('__default__',25)))
            if taken[dept]>=cap or not by[dept]:continue
            challenge.append(by[dept].pop(0));taken[dept]+=1;progress=True
            if len(challenge)>=target:break
        if not progress:break
    if len(challenge)<int(cfg['department_challenge_min_n']):raise RuntimeError(f'DEPARTMENT_CHALLENGE_TOO_SMALL:{len(challenge)}')
    out=[]
    for i,x in enumerate(rep,1):
        z=x.copy();z.update({'set_id':f'R{i:03d}','cohort':'REPRESENTATIVE'});out.append(z)
    for i,x in enumerate(challenge,1):
        z=x.copy();z.update({'set_id':f'D{i:03d}','cohort':'DEPARTMENT_CHALLENGE'});out.append(z)
    keys=[x['stable_key'] for x in out]
    if len(keys)!=len(set(keys)):raise RuntimeError('SELECTED_OVERLAP')
    return out,{'remaining_after_prior':len(rem),'representative_n':len(rep),'challenge_n':len(challenge),'challenge_department_counts':dict(taken)}

def _source_hashes(cj9:Path):
    files=[_table_file(cj9/'products')]+[_table_file(cj9/'tx'/f'w{w:02d}') for w in range(1,54)]
    return [{'path':str(p),'size':p.stat().st_size,'sha256':sha256(p)} for p in files]

def materialize(cj9:Path,out:Path):
    cfg=read_json(ROOT/'cfg/roots.json');legacy=read_json(ROOT/'cfg/legacy_panel.json');prior=read_json(ROOT/'cfg/frozen_gen1_selected.json')
    pool,ps=build_candidate_pool(cj9,legacy,int(cfg['min_pre_events']),int(cfg['min_pre_households']))
    if len(pool)!=int(cfg['expected_candidate_pool']):raise RuntimeError(f'CANDIDATE_POOL_SIZE_MISMATCH:{len(pool)}')
    selected,ss=select_confirmatory(pool,prior,cfg)
    allp={p for x in selected for p in x['candidate_products']}
    cols=['household_id','store_id','basket_id','product_id','quantity','sales_value','retail_disc','coupon_disc','coupon_match_disc','week','transaction_timestamp','net_price','gross_proxy']
    frames=[]
    for w in range(1,54):
        q=read_table(cj9/'tx'/f'w{w:02d}',columns=cols);q['product_id']=q.product_id.astype(str);q=q[q.product_id.isin(allp)].copy()
        if len(q):
            q['household_id']=q.household_id.astype(str);q['basket_id']=q.basket_id.astype(str);frames.append(q)
    alltx=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=cols)
    products=read_table(cj9/'products').copy();products['product_id']=products.product_id.astype(str);pmeta=products.set_index('product_id').to_dict(orient='index')
    cat=out/'cat';cat.mkdir(parents=True,exist_ok=True);specs=[]
    for item in selected:
        sid=item['set_id'];pids=item['candidate_products'];idx={p:i for i,p in enumerate(pids)};obs=alltx[alltx.product_id.isin(pids)].copy();obs['choice_idx']=obs.product_id.map(idx).astype('int16')
        basket_n=obs.groupby('basket_id').product_id.nunique();single=set(basket_n[basket_n==1].index.astype(str));events=obs[obs.basket_id.astype(str).isin(single)].sort_values(['transaction_timestamp','basket_id'],kind='mergesort').drop_duplicates('basket_id',keep='first').copy();events['event_id']=sid+'_'+events.basket_id.astype(str)
        events=events[['event_id','household_id','store_id','basket_id','week','transaction_timestamp','product_id','choice_idx']]
        base=cat/sid;base.mkdir(parents=True,exist_ok=True);write_table(events,base/'events')
        meta={'set_id':sid,'cohort':item['cohort'],'group_field':'product_type','group_name':item['group_name'],'department':item['department'],'candidate_products':pids,'product_meta':[pmeta[p] for p in pids if p in pmeta],'n_alternatives':6,'single_events':int(len(events)),'pre22_events':item['events_pre22'],'pre22_households':item['households_pre22'],'choice_semantics':'same-product-type observed substitute proxy; not shelf availability','selection_source':'CJ9 weeks<=22 metadata/support only; second-batch outcome blind','stable_key':item['stable_key']};write_json(base/'meta.json',meta)
        specs.append({'id':sid,'control':False,'source_root':'confirm','source_set':sid,'group_name':item['group_name'],'display_name':item['group_name'],'department':item['department'],'cohort':item['cohort'],'candidate_products':pids,'stable_key':item['stable_key']})
    pooldf=pd.DataFrame(pool);selkeys={x['stable_key']:x for x in selected};pooldf['prior_gen1']=pooldf.stable_key.isin({x['stable_key'] for x in prior['selected']});pooldf['selected_confirmatory']=pooldf.stable_key.isin(selkeys);pooldf['cohort']=pooldf.stable_key.map(lambda k:selkeys.get(k,{}).get('cohort'))
    write_table(pooldf,out/'candidate_pool_registry');write_json(out/'selected_confirmatory_sets.json',specs)
    source_hashes=_source_hashes(cj9)
    registry={'status':'PASS','campaign':'MRSP_PREDICTABILITY_CONFIRMATORY_V1','source_cj9':str(cj9),'pool_summary':ps,'selection_summary':ss,'selected_sets':specs,'source_hashes':source_hashes,'materializer_sha256':sha256(ROOT/'code/materialize_confirmatory.py'),'roots_cfg_sha256':sha256(ROOT/'cfg/roots.json'),'frozen_prior_sha256':sha256(ROOT/'cfg/frozen_gen1_selected.json'),'future_outcome_used_for_selection':False,'p1_recalibrated':False}
    write_json(out/'materialization_registry.json',registry);return registry

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--cj9',default=r'C:\MR\data\CJ9');ap.add_argument('--out',required=True);a=ap.parse_args();print(json.dumps(materialize(Path(a.cj9),Path(a.out)),ensure_ascii=False,indent=2))
