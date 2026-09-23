from __future__ import annotations
import math
import numpy as np
import pandas as pd
from code.action_rules import eval_actions


def choose_cutoff(hist:pd.DataFrame,target:float,coverages:list[float],min_n:int,correct_col='b1_correct'):
    z=hist[np.isfinite(hist.p1)].copy()
    if len(z)<min_n:return None
    for cov in sorted(coverages,reverse=True):
        q=max(1,int(math.ceil(len(z)*cov)));order=np.argsort(-z.p1.to_numpy(float),kind='mergesort');cut=float(z.iloc[order[:q]].p1.min());sel=z[z.p1>=cut]
        if len(sel)<min_n:continue
        ac=float(sel[correct_col].mean())
        if ac>=target:return {'cutoff':cut,'hist_coverage':float(len(sel)/len(z)),'hist_accuracy':ac,'n_hist':int(len(sel))}
    return None


def product_state(hist:pd.DataFrame):
    if len(hist)==0:return {'n':0,'n_blocks':0,'b0_acc':None,'b1_acc':None,'gain':None,'b1_std':None}
    b0=float(hist.b0_correct.mean());b1=float(hist.b1_correct.mean());by=hist.groupby('block').b1_correct.mean()
    return {'n':int(len(hist)),'n_blocks':int(hist.block.nunique()),'b0_acc':b0,'b1_acc':b1,'gain':float(b1-b0),'b1_std':float(by.std(ddof=0)) if len(by)>1 else 0.0}


def simple_action(hist:pd.DataFrame,target:float,cut:dict|None,gain_min:float,min_product_n:int,min_blocks:int,min_subset_n:int):
    st=product_state(hist)
    if st['n']<min_product_n or st['n_blocks']<min_blocks:return {'action':'DATA_LIMITED',**st}
    if st['b0_acc']>=target and st['gain']<gain_min:return {'action':'USE_B0_ALL',**st}
    if st['b1_acc']>=target and st['gain']>=gain_min:return {'action':'USE_B1_ALL',**st}
    if cut is None:return {'action':'ABSTAIN',**st}
    sel=hist[hist.p1>=float(cut['cutoff'])]
    if len(sel)<min_subset_n:return {'action':'ABSTAIN',**st,'cutoff':float(cut['cutoff'])}
    b0=float(sel.b0_correct.mean());b1=float(sel.b1_correct.mean());gain=b1-b0
    if b0>=target and gain<gain_min:return {'action':'USE_B0_SELECTIVE',**st,'cutoff':float(cut['cutoff']),'subset_n':int(len(sel)),'subset_b0':b0,'subset_b1':b1,'subset_gain':gain}
    if b1>=target and gain>=gain_min:return {'action':'USE_B1_SELECTIVE',**st,'cutoff':float(cut['cutoff']),'subset_n':int(len(sel)),'subset_b0':b0,'subset_b1':b1,'subset_gain':gain}
    return {'action':'ABSTAIN',**st,'cutoff':float(cut['cutoff']),'subset_n':int(len(sel)),'subset_b0':b0,'subset_b1':b1,'subset_gain':gain}


def actions_from(dec:dict,cur:pd.DataFrame):
    a=np.full(len(cur),'ABSTAIN',dtype=object);act=dec.get('action')
    if act=='USE_B0_ALL':a[:] = 'B0'
    elif act=='USE_B1_ALL':a[:] = 'B1'
    elif act=='USE_B0_SELECTIVE':a[cur.p1.to_numpy(float)>=float(dec['cutoff'])]='B0'
    elif act=='USE_B1_SELECTIVE':a[cur.p1.to_numpy(float)>=float(dec['cutoff'])]='B1'
    return a


def summarize(rows:pd.DataFrame,targets:list[float],blocks:list[str]):
    z=rows[rows.block.isin(blocks)].copy();out=[]
    for (pol,t),q in z.groupby(['policy','target']):
        valid=q[q.accepted_n>0];nn=int(valid.accepted_n.sum());tot=int(q.n.sum());acc=float(np.average(valid.accuracy,weights=valid.accepted_n)) if nn else None
        out.append({'policy':pol,'target':float(t),'coverage':float(nn/tot) if tot else 0.0,'accuracy':acc,'n_products':int(q.set_id.nunique()),'n_product_blocks':int(len(q)),'target_hit_product_blocks':int(valid.target_hit.sum()) if len(valid) else 0})
    return pd.DataFrame(out)


def action_stability(actions:pd.DataFrame,eval_blocks:list[str]):
    z=actions[actions.block.isin(eval_blocks)].copy();rows=[]
    for (sid,t,pol),q in z.groupby(['set_id','target','policy']):
        vals=[x for x in q.action.astype(str) if x not in ('DATA_LIMITED',)]
        if not vals: rows.append({'set_id':sid,'target':t,'policy':pol,'n_blocks':0,'modal_action':'DATA_LIMITED','modal_count':0,'stable_3of4':False});continue
        vc=pd.Series(vals).value_counts();rows.append({'set_id':sid,'target':float(t),'policy':pol,'n_blocks':int(len(vals)),'modal_action':str(vc.index[0]),'modal_count':int(vc.iloc[0]),'stable_3of4':bool(vc.iloc[0]>=3)})
    return pd.DataFrame(rows)

def choose_balanced_global_cutoff(hist:pd.DataFrame,target:float,coverages:list[float],min_selected_per_product:int,min_products:int,min_hit_fraction:float):
    z=hist[np.isfinite(hist.p1)].copy()
    if len(z)==0:return None
    for cov in sorted(coverages,reverse=True):
        q=max(1,int(math.ceil(len(z)*cov)));order=np.argsort(-z.p1.to_numpy(float),kind='mergesort');cut=float(z.iloc[order[:q]].p1.min());sel=z[z.p1>=cut]
        stats=[]
        for sid,g in sel.groupby('set_id'):
            if len(g)>=min_selected_per_product:stats.append((sid,len(g),float(g.b1_correct.mean())))
        if len(stats)<min_products:continue
        hit=sum(1 for _,_,a in stats if a>=target);frac=hit/len(stats);pool=float(sel.b1_correct.mean())
        if frac>=min_hit_fraction and pool>=target:
            return {'cutoff':cut,'coverage_actual_hist':float(len(sel)/len(z)),'hist_accuracy':pool,'n_hist':int(len(sel)),'qualifying_products':int(len(stats)),'hit_products':int(hit),'hit_fraction':float(frac),'balanced_across_products':True}
    return None
