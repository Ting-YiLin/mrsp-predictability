from __future__ import annotations
import math,time
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .common import normalize_rows, coarse_bin, RSSMonitor, model_size_bytes


def b1_probs(df:pd.DataFrame,lmap:dict,J:int=6)->np.ndarray:
    out=np.zeros((len(df),J),float)
    for i,r in enumerate(df.itertuples(index=False)):
        mp=np.array([getattr(r,f'market_p{j}') for j in range(J)],float);hc=np.array([getattr(r,f'hh_count{j}') for j in range(J)],float);lam=float(lmap[coarse_bin(int(r.k))]);x=lam*mp+hc;out[i]=x/x.sum()
    return out


def tune_b1(df:pd.DataFrame,masks:dict,grid:list[float],J:int=6)->dict:
    fit_tune=masks['TUNE']; y=df.y.to_numpy(int); out={}
    # TUNE is used for hyperparameter selection; each event's mp/hh counts are strictly pre-event.
    for b in ['0_2','3_9','10_plus']:
        m=fit_tune & np.array([coarse_bin(int(k))==b for k in df.k])
        best=(-1e99,5.0)
        for lam in grid:
            if not m.any():continue
            p=[]
            for r in df.loc[m].itertuples(index=False):
                mp=np.array([getattr(r,f'market_p{j}') for j in range(J)],float);hc=np.array([getattr(r,f'hh_count{j}') for j in range(J)],float);x=float(lam)*mp+hc;p.append(x/x.sum())
            p=np.asarray(p); yy=y[m];sc=float(np.log(np.maximum(p[np.arange(len(yy)),yy],1e-15)).mean())
            if sc>best[0]:best=(sc,float(lam))
        out[b]=best[1]
    # machine-safe fallback if a maturity bin is absent in TUNE
    present=[v for b,v in out.items() if np.any(fit_tune & np.array([coarse_bin(int(k))==b for k in df.k]))]
    fb=float(np.median(present)) if present else 5.0
    for b in out:
        if not np.any(fit_tune & np.array([coarse_bin(int(k))==b for k in df.k])):out[b]=fb
    return out


def behavior_tensor(df:pd.DataFrame,J:int=6)->np.ndarray:
    # Features are alternative-specific and all are pre-event.
    X=np.zeros((len(df),J,4),float)
    for j in range(J):
        last=df[f'last_is{j}'].to_numpy(float);X[:,j,0]=last
        X[:,j,1]=last*np.log1p(df.streak.to_numpy(float))
        X[:,j,2]=df[f'recent_share{j}'].to_numpy(float)
        X[:,j,3]=np.exp(-np.minimum(df[f'elapsed_days{j}'].to_numpy(float),3650.0)/30.0)
    return X


def offset_nll(beta:np.ndarray,X:np.ndarray,base_p:np.ndarray,y:np.ndarray,l2:float=1e-3)->tuple[float,np.ndarray]:
    b=normalize_rows(base_p);u=np.log(b)+np.tensordot(X,beta,axes=([2],[0]));u-=u.max(1,keepdims=True);p=np.exp(np.clip(u,-50,50));p/=p.sum(1,keepdims=True);n=len(y);loss=-np.log(np.maximum(p[np.arange(n),y],1e-15)).mean()+.5*l2*float(beta@beta);chosen=X[np.arange(n),y];expected=(p[:,:,None]*X).sum(1);grad=-(chosen-expected).mean(0)+l2*beta;return float(loss),grad


def fit_offset(X:np.ndarray,base_p:np.ndarray,y:np.ndarray,idx:list[int],l2:float=1e-3)->dict:
    if len(y)<20:return {'status':'DATA_LIMITED','beta':[0.0]*len(idx),'idx':idx,'loss':None}
    XX=X[:,:,idx];b0=np.zeros(len(idx),float);res=minimize(lambda b:offset_nll(b,XX,base_p,y,l2),b0,jac=True,method='L-BFGS-B',options={'maxiter':250})
    return {'status':'PASS' if res.success else 'WARN','beta':res.x.tolist(),'idx':idx,'loss':float(res.fun),'nit':int(getattr(res,'nit',0)),'message':str(res.message)}


def apply_offset(fit:dict,X:np.ndarray,base_p:np.ndarray)->np.ndarray:
    idx=fit['idx'];beta=np.asarray(fit['beta'],float);u=np.log(normalize_rows(base_p))+np.tensordot(X[:,:,idx],beta,axes=([2],[0]));u-=u.max(1,keepdims=True);p=np.exp(np.clip(u,-50,50));return p/p.sum(1,keepdims=True)


def tune_b2(df:pd.DataFrame,masks:dict,b1:np.ndarray,J:int=6)->dict:
    X=behavior_tensor(df,J);y=df.y.to_numpy(int);fitmask=masks['FIT'];tunemask=masks['TUNE'];specs={'repeat':[0],'repeat_streak':[0,1],'repeat_recent':[0,2],'full':[0,1,2,3]};cand=[]
    for name,idx in specs.items():
        fit=fit_offset(X[fitmask],b1[fitmask],y[fitmask],idx)
        if fit['status']=='DATA_LIMITED':score=-1e99
        else:
            p=apply_offset(fit,X[tunemask],b1[tunemask]); yy=y[tunemask];score=float(np.log(np.maximum(p[np.arange(len(yy)),yy],1e-15)).mean()) if len(yy) else -1e99
        cand.append({'name':name,'idx':idx,'fit':fit,'tune_log_score':score})
    best=max(cand,key=lambda z:z['tune_log_score']); final=fit_offset(X[fitmask|tunemask],b1[fitmask|tunemask],y[fitmask|tunemask],best['idx']); return {'selected_spec':best['name'],'selected_idx':best['idx'],'selection_candidates':cand,'final_fit':final}


def b2_probs(df:pd.DataFrame,b1:np.ndarray,b2fit:dict,J:int=6)->np.ndarray:
    return apply_offset(b2fit['final_fit'],behavior_tensor(df,J),b1)


