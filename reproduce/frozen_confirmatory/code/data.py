from __future__ import annotations
from collections import defaultdict, deque
from pathlib import Path
import math
import numpy as np
import pandas as pd

from code.common import read_json, read_table, entropy_from_counts, history_bin

REQ_EVENT=['household_id','basket_id','week','transaction_timestamp','product_id','choice_idx']


def resolve_root(root_value:str, root_overrides:dict[str,str]|None, key:str)->Path:
    if root_overrides and key in root_overrides:return Path(root_overrides[key])
    return Path(root_value)


def validate_set(spec:dict, roots_cfg:dict, root_overrides:dict[str,str]|None=None)->dict:
    root=resolve_root(roots_cfg[spec['source_root']],root_overrides,spec['source_root']);base=root/'cat'/spec['source_set'];meta_path=base/'meta.json'
    if not meta_path.exists():return {'set_id':spec['id'],'ok':False,'error':'META_MISSING','path':str(meta_path)}
    meta=read_json(meta_path); got_name=str(meta.get('group_name','')); got=[str(x) for x in meta.get('candidate_products',[])]
    expected=[str(x) for x in spec['candidate_products']]
    checks={'group_name_exact':got_name==spec['group_name'],'candidate_products_exact_order':got==expected,'n_alternatives_6':int(meta.get('n_alternatives',len(got)))==6}
    try:
        ev=read_table(base/'events',columns=REQ_EVENT)
        checks['events_nonempty']=len(ev)>0
        checks['choice_idx_range']=bool(len(ev)) and int(pd.to_numeric(ev.choice_idx).min())>=0 and int(pd.to_numeric(ev.choice_idx).max())<6
        checks['product_membership']=set(ev.product_id.astype(str).unique()).issubset(set(expected))
        multi_dup=int(ev.duplicated('basket_id').sum());checks['one_event_per_basket']=multi_dup==0
    except Exception as e:
        return {'set_id':spec['id'],'ok':False,'error':'EVENT_READ_FAIL:'+repr(e),'path':str(base)}
    return {'set_id':spec['id'],'ok':all(checks.values()),'checks':checks,'path':str(base),'source_set':spec['source_set'],'source_root':spec['source_root']}


def load_set(spec:dict, roots_cfg:dict, root_overrides:dict[str,str]|None=None, hh_limit:int|None=None)->tuple[pd.DataFrame,dict]:
    chk=validate_set(spec,roots_cfg,root_overrides)
    if not chk['ok']:raise RuntimeError('SEMANTIC_FAIL:'+spec['id']+':'+str(chk))
    root=resolve_root(roots_cfg[spec['source_root']],root_overrides,spec['source_root']);base=root/'cat'/spec['source_set'];meta=read_json(base/'meta.json');ev=read_table(base/'events',columns=REQ_EVENT)
    ev=ev.copy();ev['household_id']=ev.household_id.astype(str);ev['basket_id']=ev.basket_id.astype(str);ev['product_id']=ev.product_id.astype(str);ev['week']=pd.to_numeric(ev.week).astype(int);ev['choice_idx']=pd.to_numeric(ev.choice_idx).astype(int);ev['transaction_timestamp']=pd.to_datetime(ev.transaction_timestamp,errors='raise')
    ev=ev.sort_values(['transaction_timestamp','basket_id'],kind='mergesort').reset_index(drop=True)
    if hh_limit is not None:
        ids=sorted(ev.household_id.unique())[:int(hh_limit)];ev=ev[ev.household_id.isin(ids)].copy().reset_index(drop=True)
    ev['panel_set_id']=spec['id'];ev['is_control']=bool(spec.get('control',False))
    return ev,meta


def build_sequential_frame(ev:pd.DataFrame,J:int=6)->pd.DataFrame:
    """Build only pre-event features. Current choice mutates state after row construction."""
    g=np.zeros(J,float);hh=defaultdict(lambda:np.zeros(J,float));last={};streak=defaultdict(int);recent=defaultdict(lambda:deque(maxlen=5));last_time=defaultdict(lambda:[None]*J);last_any={};switch_n=defaultdict(int);transition_n=defaultdict(int)
    rows=[]
    for r in ev.sort_values(['transaction_timestamp','basket_id'],kind='mergesort').itertuples(index=False):
        h=str(r.household_id); y=int(r.choice_idx); t=pd.Timestamp(r.transaction_timestamp); hc=hh[h].copy();k=int(hc.sum())
        other=np.maximum(g-hc,0.0)+1.0;mp=other/other.sum(); hshare=hc/k if k>0 else np.zeros(J)
        hn,top,distinct_frac,distinct=entropy_from_counts(hc); lc=last.get(h,-1); rc=np.bincount(list(recent[h]),minlength=J).astype(float)/max(len(recent[h]),1) if len(recent[h]) else np.zeros(J)
        elapsed=[]
        for j in range(J):
            lt=last_time[h][j]
            d=max((t-lt).total_seconds()/86400.0,0.0) if lt is not None else 9999.0
            elapsed.append(d)
        ea=max((t-last_any[h]).total_seconds()/86400.0,0.0) if h in last_any else 9999.0
        sw=float(switch_n[h]/transition_n[h]) if transition_n[h]>0 else 0.0
        row={'event_id':f"{getattr(r,'panel_set_id','S')}_{r.basket_id}",'panel_set_id':getattr(r,'panel_set_id','S'),'household_id':h,'basket_id':str(r.basket_id),'week':int(r.week),'transaction_timestamp':t,'y':y,'product_id':str(r.product_id),'k':k,'history_bin':history_bin(k),'last_choice':int(lc),'streak':int(streak[h]),'hh_entropy':float(hn),'hh_top_share':float(top),'hh_distinct_frac':float(distinct_frac),'hh_distinct_n':int(distinct),'switch_rate':float(sw),'recent_concentration':float(rc.max()) if len(rc) else 0.0,'elapsed_any_days':float(ea)}
        for j in range(J):
            row[f'market_p{j}']=float(mp[j]);row[f'hh_count{j}']=float(hc[j]);row[f'hh_share{j}']=float(hshare[j]);row[f'recent_share{j}']=float(rc[j]);row[f'elapsed_days{j}']=float(elapsed[j]);row[f'last_is{j}']=1.0 if lc==j else 0.0
        rows.append(row)
        # mutate only after feature row is complete
        if lc>=0:
            transition_n[h]+=1
            if lc!=y:switch_n[h]+=1
        streak[h]=streak[h]+1 if lc==y else 1
        last[h]=y;recent[h].append(y);last_time[h][y]=t;last_any[h]=t;g[y]+=1;hh[h][y]+=1
    return pd.DataFrame(rows)


def split_masks(df:pd.DataFrame,time_cfg:dict)->dict[str,np.ndarray]:
    w=df.week.to_numpy(int)
    return {
      'FIT':w<=int(time_cfg['fit_max_week']),
      'TUNE':(w>=int(time_cfg['tune_min_week']))&(w<=int(time_cfg['tune_max_week'])),
      'TEST_A':(w>=int(time_cfg['test_a_min_week']))&(w<=int(time_cfg['test_a_max_week'])),
      'TEST_B':w>=int(time_cfg['test_b_min_week'])
    }


def f_common(df:pd.DataFrame,J:int=6)->np.ndarray:
    cols=[]
    for prefix in ['market_p','hh_share','recent_share']:
        cols += [df[f'{prefix}{j}'].to_numpy(float)[:,None] for j in range(J)]
    # bounded elapsed transforms and last-choice one hot
    cols += [np.exp(-np.minimum(df[f'elapsed_days{j}'].to_numpy(float),3650.0)/30.0)[:,None] for j in range(J)]
    cols += [df[f'last_is{j}'].to_numpy(float)[:,None] for j in range(J)]
    scalars=[np.log1p(df.k.to_numpy(float)),df.hh_entropy.to_numpy(float),df.hh_top_share.to_numpy(float),df.switch_rate.to_numpy(float),df.hh_distinct_frac.to_numpy(float),np.log1p(df.streak.to_numpy(float)),np.log1p(np.minimum(df.elapsed_any_days.to_numpy(float),3650.0)),df.recent_concentration.to_numpy(float)]
    cols += [x[:,None] for x in scalars]
    return np.concatenate(cols,axis=1)


def e2_features(df:pd.DataFrame)->np.ndarray:
    return np.column_stack([
      np.log1p(df.k.to_numpy(float)),df.hh_entropy.to_numpy(float),df.hh_top_share.to_numpy(float),df.switch_rate.to_numpy(float),df.hh_distinct_frac.to_numpy(float),np.log1p(df.streak.to_numpy(float)),df.recent_concentration.to_numpy(float),np.log1p(np.minimum(df.elapsed_any_days.to_numpy(float),3650.0))
    ])
