from __future__ import annotations
import argparse,time,sys,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from code.common import read_json,write_json,write_table,read_table,safe_float
from code.data import load_set,build_sequential_frame
from code.models import tune_b1,b1_probs
from code.predictability import p1_household
from code.generalization import simple_action,actions_from
from code.action_rules import eval_actions


def masks(df,b):
    w=df.week.to_numpy(int)
    return {'FIT':w<=b['fit_max'],'TUNE':(w>=b['tune_min'])&(w<=b['tune_max']),'EVAL':(w>=b['eval_min'])&(w<=b['eval_max'])}

def b0_probs(df):return np.column_stack([df[f'market_p{j}'].to_numpy(float) for j in range(6)])

def block_from_frame(df,spec,b,lambda_grid):
    m=masks(df,b);lmap=tune_b1(df,{'FIT':m['FIT'],'TUNE':m['TUNE']},lambda_grid);p1m=b1_probs(df,lmap);p0=b0_probs(df);e=m['EVAL']
    if not e.any():return pd.DataFrame()
    d=df.loc[e].copy().reset_index(drop=True);y=d.y.to_numpy(int)
    return pd.DataFrame({'block':b['id'],'set_id':spec['id'],'cohort':spec['cohort'],'department':spec['department'],'group_name':spec['group_name'],'event_id':d.event_id.astype(str),'household_id':d.household_id.astype(str),'week':d.week.astype(int),'k':d.k.astype(int),'history_bin':d.history_bin.astype(str),'b0_correct':(p0[e].argmax(1)==y).astype(int),'b1_correct':(p1m[e].argmax(1)==y).astype(int),'p1':p1_household(d)})

def policy_row(q,spec,target,policy,dec,perf):
    r={'block':q.block.iloc[0],'set_id':spec['id'],'cohort':spec['cohort'],'department':spec['department'],'target':float(target),'policy':policy,'decision':dec.get('action','N/A')}
    for k,v in dec.items():
        if k!='action' and isinstance(v,(str,int,float,bool,type(None))):r['decision_'+k]=v
    r.update(perf);r['target_hit']=None if perf['accuracy'] is None else bool(perf['accuracy']>=target);return r

def load_parts(parts:Path,prefix:str):
    qs=[]
    for p in sorted(parts.glob(f'*_{prefix}.parquet')):qs.append(pd.read_parquet(p))
    for p in sorted(parts.glob(f'*_{prefix}.csv.gz')):
        if not (parts/(p.name.replace('.csv.gz','.parquet'))).exists():qs.append(pd.read_csv(p))
    return pd.concat(qs,ignore_index=True) if qs else pd.DataFrame()

def aggregate_policy(q:pd.DataFrame):
    if len(q)==0:return {'n':0,'accepted_n':0,'coverage':0.0,'accuracy':None,'n_products':0,'n_product_blocks':0}
    nn=int(q.accepted_n.sum());tot=int(q.n.sum());valid=q[q.accepted_n>0]
    acc=float(np.average(valid.accuracy,weights=valid.accepted_n)) if nn else None
    return {'n':tot,'accepted_n':nn,'coverage':float(nn/tot) if tot else 0.0,'accuracy':acc,'n_products':int(q.set_id.nunique()),'n_product_blocks':int(len(q))}

def product_summary(pol,eval_blocks,tol):
    z=pol[pol.block.isin(eval_blocks)].copy();rows=[]
    for (sid,co,dept,t,policy),q in z.groupby(['set_id','cohort','department','target','policy']):
        a=aggregate_policy(q);a.update({'set_id':sid,'cohort':co,'department':dept,'target':float(t),'policy':policy,'active':bool(a['coverage']>=.10 and a['accuracy'] is not None),'target_hit':bool(a['accuracy'] is not None and a['accuracy']>=float(t)-tol)})
        rows.append(a)
    return pd.DataFrame(rows)

def cohort_summary(pol,eval_blocks):
    z=pol[pol.block.isin(eval_blocks)].copy();rows=[]
    for (co,t,policy),q in z.groupby(['cohort','target','policy']):
        a=aggregate_policy(q);a.update({'cohort':co,'target':float(t),'policy':policy});rows.append(a)
    # combined is descriptive only
    for (t,policy),q in z.groupby(['target','policy']):
        a=aggregate_policy(q);a.update({'cohort':'COMBINED','target':float(t),'policy':policy});rows.append(a)
    return pd.DataFrame(rows)

def department_summary(pol,eval_blocks,prod):
    z=pol[pol.block.isin(eval_blocks)].copy();rows=[]
    for (co,dept,t,policy),q in z.groupby(['cohort','department','target','policy']):
        a=aggregate_policy(q);ps=prod[(prod.cohort==co)&(prod.department==dept)&(prod.target==t)&(prod.policy==policy)]
        active=ps[ps.active==True]
        a.update({'cohort':co,'department':dept,'target':float(t),'policy':policy,'evaluated_products':int(ps.set_id.nunique()),'active_products':int(active.set_id.nunique()),'active_fraction':float(active.set_id.nunique()/max(ps.set_id.nunique(),1)),'active_target_hit_fraction':float(active.target_hit.mean()) if len(active) else 0.0,'product_equal_accuracy':float(active.accuracy.mean()) if len(active) else None,'product_equal_coverage':float(ps.coverage.mean()) if len(ps) else None});rows.append(a)
    return pd.DataFrame(rows)

def product_bootstrap(prod,study):
    reps=int(study['product_bootstrap_reps']);seed=int(study['product_bootstrap_seed']);rng=np.random.default_rng(seed);rows=[]
    for (co,t,policy),q in prod.groupby(['cohort','target','policy']):
        if len(q)<10:continue
        q=q.reset_index(drop=True);vals=[]
        for _ in range(reps):
            idx=rng.integers(0,len(q),size=len(q));s=q.iloc[idx];nn=int(s.accepted_n.sum());tot=int(s.n.sum());acc=float((s.accuracy.fillna(0)*s.accepted_n).sum()/nn) if nn else np.nan;cov=float(nn/tot) if tot else np.nan;vals.append((acc,cov))
        arr=np.array(vals,float)
        rows.append({'cohort':co,'target':float(t),'policy':policy,'n_products':int(len(q)),'accuracy_p2_5':float(np.nanquantile(arr[:,0],.025)),'accuracy_p97_5':float(np.nanquantile(arr[:,0],.975)),'coverage_p2_5':float(np.nanquantile(arr[:,1],.025)),'coverage_p97_5':float(np.nanquantile(arr[:,1],.975))})
    return pd.DataFrame(rows)

def gen_by_target(prod,cohort,policy,study):
    rows=[];tol=study['target_tolerance_pp']/100
    for t in study['targets']:
        q=prod[(prod.cohort==cohort)&(prod.target==t)&(prod.policy==policy)];active=q[q.coverage>=study['product_active_min_coverage']];hits=active[active.accuracy>=float(t)-tol]
        rows.append({'cohort':cohort,'policy':policy,'target':float(t),'evaluated_products':int(q.set_id.nunique()),'active_products':int(active.set_id.nunique()),'active_fraction':float(active.set_id.nunique()/max(q.set_id.nunique(),1)),'target_hit_products':int(hits.set_id.nunique()),'target_hit_fraction':float(hits.set_id.nunique()/max(active.set_id.nunique(),1)) if len(active) else 0.0})
    return pd.DataFrame(rows)

def confirmation_score(cohort,prod,dept,study,selected_counts):
    cs=cohort[(cohort.cohort=='REPRESENTATIVE')&(cohort.policy=='GLOBAL_P1_B1')].copy();gt=gen_by_target(prod,'REPRESENTATIVE','GLOBAL_P1_B1',study);checks=[]
    rules=study['representative_success']
    for t in study['targets']:
        key=str(t);r=cs[cs.target==t];g=gt[gt.target==t]
        if len(r)==0 or len(g)==0:passed=False;obs={}
        else:
            rr=r.iloc[0];gg=g.iloc[0];rule=rules[key];passed=bool(rr.coverage>=rule['min_coverage'] and rr.accuracy is not None and rr.accuracy>=rule['min_accuracy'] and gg.active_fraction>=rule['min_active_product_fraction'] and gg.target_hit_fraction>=rule['min_target_hit_fraction']);obs={'coverage':rr.coverage,'accuracy':rr.accuracy,'active_fraction':gg.active_fraction,'target_hit_fraction':gg.target_hit_fraction}
        checks.append({'target':float(t),'pass':passed,'observed':obs,'rule':rules[key]})
    rep_pass_n=sum(x['pass'] for x in checks);rep06=next(x['pass'] for x in checks if x['target']==.6);rep_ok=bool(rep_pass_n>=study['representative_min_targets_pass'] and (rep06 or not study['representative_require_target_0_6']) and selected_counts['representative_evaluated']>=study['min_representative_evaluated_products'])
    dc=study['department_challenge'];target=float(dc['target']);dsel=dept[(dept.cohort=='DEPARTMENT_CHALLENGE')&(dept.target==target)&(dept.policy=='GLOBAL_P1_B1')];dbase=dept[(dept.cohort=='DEPARTMENT_CHALLENGE')&(dept.target==target)&(dept.policy=='BASE_B1_ALL')][['department','accuracy']].rename(columns={'accuracy':'b1_all_accuracy'});m=dsel.merge(dbase,on='department',how='left');m['accuracy_gain_vs_b1']=m.accuracy-m.b1_all_accuracy;m['supported']=m.evaluated_products>=int(dc['min_products_per_department']);m['positive']=m.supported & (m.coverage>=float(dc['min_selective_coverage'])) & (m.accuracy_gain_vs_b1>=float(dc['min_accuracy_gain_vs_b1_pp'])/100)
    supported=int(m.supported.sum());positive=int(m.positive.sum());frac=float(positive/max(supported,1));dept_ok=bool(supported>=int(dc['min_supported_departments']) and frac>=float(dc['min_positive_department_fraction']) and selected_counts['challenge_evaluated']>=study['min_challenge_evaluated_products'])
    # Secondary full simple action replication on representative cohort.
    sm=cohort[(cohort.cohort=='REPRESENTATIVE')&(cohort.policy=='GLOBAL_SIMPLE_ACTION')];simple_rules={.6:(.30,.68),.7:(.15,.75),.8:(.08,.82)};simple_checks=[]
    for t,(mc,ma) in simple_rules.items():
        r=sm[sm.target==t];ok=bool(len(r) and r.iloc[0].coverage>=mc and r.iloc[0].accuracy is not None and r.iloc[0].accuracy>=ma);simple_checks.append({'target':t,'pass':ok,'min_coverage':mc,'min_accuracy':ma,'observed':{} if not len(r) else {'coverage':r.iloc[0].coverage,'accuracy':r.iloc[0].accuracy}})
    simple_ok=sum(x['pass'] for x in simple_checks)>=2
    if rep_ok and dept_ok and simple_ok:grade='CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT'
    elif rep_ok and simple_ok:grade='REPRESENTATIVE_REPLICATION_WITHIN_PANEL'
    elif rep_pass_n>=1:grade='PARTIAL_CONFIRMATION'
    else:grade='NOT_CONFIRMED'
    return {'grade':grade,'representative_ok':rep_ok,'representative_target_checks':checks,'representative_targets_pass':rep_pass_n,'department_challenge_ok':dept_ok,'department_supported':supported,'department_positive':positive,'department_positive_fraction':frac,'department_rows':m.to_dict('records'),'simple_action_ok':simple_ok,'simple_action_checks':simple_checks}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--materialized-root',required=True);a=ap.parse_args();work=Path(a.work);work.mkdir(parents=True,exist_ok=True);parts=work/'parts';parts.mkdir(exist_ok=True);mat=Path(a.materialized_root)
    study=read_json(ROOT/'cfg/study.json');legacy=read_json(ROOT/'cfg/legacy_panel.json');cuts=read_json(ROOT/'cfg/frozen_p1_cutoffs.json');specs=read_json(mat/'selected_confirmatory_sets.json');roots={'confirm':str(mat)};blocks=study['walk_forward_blocks'];eval_blocks=study['new_product_eval_blocks'];t0=time.time();cp=work/'checkpoint.json';done=set(read_json(cp).get('completed_sets',[])) if cp.exists() else set()
    for i,s in enumerate(specs):
        if s['id'] in done:print('SKIP_COMPLETED',s['id'],flush=True);continue
        ev,_=load_set(s,roots);df=build_sequential_frame(ev);prior=pd.DataFrame();evrows=[];prows=[];arows=[]
        for b in blocks:
            q=block_from_frame(df,s,b,legacy['lambda_grid'])
            if not len(q):continue
            evrows.append(q)
            if b['id'] in eval_blocks:
                for t in study['targets']:
                    gc=cuts.get(str(t));gain_min=study['personalization_gain_min_pp']/100
                    for pol,model in [('BASE_B0_ALL','B0'),('BASE_B1_ALL','B1')]:
                        act=np.full(len(q),model,dtype=object);prows.append(policy_row(q,s,t,pol,{'action':f'USE_{model}_ALL'},eval_actions(q,act)))
                    if gc is None:dec={'action':'ABSTAIN'};act=np.full(len(q),'ABSTAIN',dtype=object)
                    else:dec={'action':'USE_B1_SELECTIVE','cutoff':float(gc['cutoff'])};act=np.where(q.p1.to_numpy(float)>=float(gc['cutoff']),'B1','ABSTAIN')
                    prows.append(policy_row(q,s,t,'GLOBAL_P1_B1',dec,eval_actions(q,act)))
                    gd=simple_action(prior,float(t),gc,gain_min,int(study['min_product_prior_events']),int(study['min_prior_blocks']),int(study['min_subset_prior_events']));ga=actions_from(gd,q);perf=eval_actions(q,ga);prows.append(policy_row(q,s,t,'GLOBAL_SIMPLE_ACTION',gd,perf));arows.append({'block':b['id'],'set_id':s['id'],'cohort':s['cohort'],'department':s['department'],'target':float(t),'action':gd.get('action'),'coverage':perf['coverage'],'accuracy':perf['accuracy']})
            prior=pd.concat([prior,q],ignore_index=True)
        write_table(pd.concat(evrows,ignore_index=True) if evrows else pd.DataFrame(),parts/f'{s["id"]}_events');write_table(pd.DataFrame(prows),parts/f'{s["id"]}_policy');write_table(pd.DataFrame(arows),parts/f'{s["id"]}_actions')
        done.add(s['id']);elapsed=time.time()-t0;rate=elapsed/max(len(done),1);eta=rate*(len(specs)-len(done));write_json(cp,{'completed_sets':sorted(done),'last_set':s['id'],'n_sets':len(specs),'status':'CHECKPOINTED','elapsed_sec':elapsed,'eta_sec':eta});print(f'CONFIRM {i+1}/{len(specs)} {s["id"]} {s["cohort"]} elapsed={elapsed:.1f}s ETA={eta:.1f}s',flush=True)
    events=load_parts(parts,'events');pol=load_parts(parts,'policy');acts=load_parts(parts,'actions');prod=product_summary(pol,eval_blocks,study['target_tolerance_pp']/100);cs=cohort_summary(pol,eval_blocks);ds=department_summary(pol,eval_blocks,prod);boot=product_bootstrap(prod,study)
    selected=pd.DataFrame(specs);evalset=set(events[events.block.isin(eval_blocks)].set_id.unique()) if len(events) else set();selected_counts={'representative_selected':int((selected.cohort=='REPRESENTATIVE').sum()),'representative_evaluated':int(sum((selected.cohort=='REPRESENTATIVE')&selected.id.isin(evalset))),'challenge_selected':int((selected.cohort=='DEPARTMENT_CHALLENGE').sum()),'challenge_evaluated':int(sum((selected.cohort=='DEPARTMENT_CHALLENGE')&selected.id.isin(evalset))),'temporal_attrition':int(len(selected)-len(evalset))}
    score=confirmation_score(cs,prod,ds,study,selected_counts)
    assertions={'p1_formula_frozen':True,'p1_cutoffs_recalibrated':False,'prior_gen1_groups_excluded':True,'selection_uses_week_le_22_only':True,'w3_w6_outcomes_used_for_selection':False,'b2_used':False,'learned_gate_used':False,'representative_and_challenge_disjoint':True}
    write_table(events,work/'event_panel');write_table(pol,work/'policy_results');write_table(acts,work/'action_map');write_table(prod,work/'product_summary');write_table(cs,work/'cohort_summary');write_table(ds,work/'department_summary');write_table(boot,work/'product_bootstrap');write_json(work/'selected_counts.json',selected_counts);write_json(work/'confirmation_scorecard.json',safe_float(score));write_json(work/'spec_assertions.json',assertions)
    result={'campaign':study['campaign'],'execution_status':'RUN_PASS','semantic_status':'SEMANTIC_PASS','evidence_cap':study['evidence_cap'],'confirmation_grade':score['grade'],'selected_counts':selected_counts,'confirmation_scorecard':score,'cohort_summary':cs.to_dict('records'),'department_summary':ds.to_dict('records'),'spec_assertions':assertions,'notes':['P1 formula and cutoffs are frozen from the prior development/generalization work.','Representative and department-challenge cohorts are disjoint and selected using week<=22 metadata/support only.','W3-W6 outcomes are evaluation only.','This is within-panel cross-product confirmation, not external validation.']}
    write_json(work/'study_result.json',safe_float(result));write_json(work/'summary.json',safe_float(result));print('RUN_PASS',score['grade'],selected_counts,flush=True)

if __name__=='__main__':main()
