from __future__ import annotations
import hashlib, json, math, os, pickle, time, threading
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    json.loads(tmp.read_text(encoding='utf-8'))
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_table(base: Path, columns: list[str] | None=None) -> pd.DataFrame:
    if base.suffix in ('.parquet','.csv','.gz') and base.exists():
        p=base
    elif base.with_suffix('.parquet').exists():
        p=base.with_suffix('.parquet')
    elif base.with_suffix('.csv.gz').exists():
        p=base.with_suffix('.csv.gz')
    elif base.with_suffix('.csv').exists():
        p=base.with_suffix('.csv')
    else:
        raise FileNotFoundError(str(base)+'[.parquet|.csv.gz|.csv]')
    if p.suffix=='.parquet':
        try:
            return pd.read_parquet(p, columns=columns)
        except Exception as e:
            raise RuntimeError('PARQUET_READ_FAILED:'+repr(e)) from e
    df=pd.read_csv(p)
    if columns is not None:
        miss=[c for c in columns if c not in df.columns]
        if miss: raise RuntimeError('CSV_SCHEMA_MISSING:'+','.join(miss))
        df=df[columns]
    return df


def write_table(df: pd.DataFrame, base: Path) -> Path:
    base.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow  # noqa
        p=base.with_suffix('.parquet'); df.to_parquet(p,index=False); return p
    except Exception:
        p=base.with_suffix('.csv.gz'); df.to_csv(p,index=False,compression='gzip'); return p


def normalize_rows(p: np.ndarray) -> np.ndarray:
    p=np.asarray(p,float)
    if p.ndim!=2: raise ValueError('PROBS_NOT_2D')
    p=np.maximum(p,1e-15)
    s=p.sum(1,keepdims=True)
    if np.any(~np.isfinite(s)) or np.any(s<=0): raise ValueError('BAD_PROB_ROW')
    return p/s


def ece10(probs: np.ndarray, y: np.ndarray) -> float | None:
    probs=normalize_rows(probs); y=np.asarray(y,int)
    if not len(y): return None
    pred=probs.argmax(1); conf=probs.max(1); edges=np.linspace(0,1,11); e=0.0
    for i in range(10):
        lo,hi=edges[i],edges[i+1]
        m=(conf>=lo)&((conf<=hi) if i==9 else (conf<hi))
        if m.any(): e+=float(m.mean())*abs(float((pred[m]==y[m]).mean())-float(conf[m].mean()))
    return float(e)


def metrics(probs: np.ndarray, y: np.ndarray, hh: np.ndarray | None=None) -> dict:
    probs=normalize_rows(probs); y=np.asarray(y,int)
    if len(y)==0:
        return {'n':0,'accuracy':None,'mean_log_score':None,'top3':None,'ece_10':None,'n_households':0}
    if probs.shape[0]!=len(y): raise ValueError('METRIC_SHAPE_MISMATCH')
    pred=probs.argmax(1); order=np.argsort(-probs,axis=1)
    ranks=np.array([int(np.where(order[i]==y[i])[0][0])+1 for i in range(len(y))])
    out={'n':int(len(y)),'accuracy':float((pred==y).mean()),'mean_log_score':float(np.log(np.maximum(probs[np.arange(len(y)),y],1e-15)).mean()),'top3':float((ranks<=min(3,probs.shape[1])).mean()),'ece_10':ece10(probs,y)}
    out['n_households']=int(len(np.unique(hh))) if hh is not None else None
    return out


def binary_ece(p: np.ndarray, y: np.ndarray, bins: int=10) -> float | None:
    p=np.asarray(p,float); y=np.asarray(y,int)
    if not len(y): return None
    edges=np.linspace(0,1,bins+1); e=0.0
    for i in range(bins):
        m=(p>=edges[i])&((p<=edges[i+1]) if i==bins-1 else (p<edges[i+1]))
        if m.any(): e+=float(m.mean())*abs(float(y[m].mean())-float(p[m].mean()))
    return float(e)


def history_bin(k: int) -> str:
    if k==0:return '0'
    if k<=3:return '1_3'
    if k<=9:return '4_9'
    if k<=19:return '10_19'
    return '20_plus'

def coarse_bin(k:int)->str:
    if k<=2:return '0_2'
    if k<=9:return '3_9'
    return '10_plus'


def entropy_from_counts(c: np.ndarray) -> tuple[float,float,float,int]:
    c=np.asarray(c,float); k=float(c.sum())
    if k<=0:return 0.0,1.0,0.0,0
    p=c/k; nz=p[p>0]; h=float(-(nz*np.log(nz)).sum()); hn=float(h/math.log(len(c))) if len(c)>1 else 0.0
    return hn,float(p.max()),float((p>0).sum()/len(c)),int((p>0).sum())


def clustered_bootstrap_delta(pa: np.ndarray,pb: np.ndarray,y: np.ndarray,clusters: np.ndarray,n_boot:int=400,seed:int=20260917)->dict:
    pa=normalize_rows(pa);pb=normalize_rows(pb);y=np.asarray(y,int);clusters=np.asarray(clusters).astype(str)
    if not len(y):return {'n_boot':n_boot,'n_clusters':0,'accuracy_delta':None,'log_score_delta':None}
    uniq,inv=np.unique(clusters,return_inverse=True)
    da=(pb.argmax(1)==y).astype(float)-(pa.argmax(1)==y).astype(float)
    dl=np.log(np.maximum(pb[np.arange(len(y)),y],1e-15))-np.log(np.maximum(pa[np.arange(len(y)),y],1e-15))
    n=np.bincount(inv,minlength=len(uniq)).astype(float); sa=np.bincount(inv,weights=da,minlength=len(uniq)); sl=np.bincount(inv,weights=dl,minlength=len(uniq))
    rng=np.random.default_rng(seed); draws=rng.integers(0,len(uniq),size=(int(n_boot),len(uniq))); den=n[draws].sum(1)
    va=sa[draws].sum(1)/den; vl=sl[draws].sum(1)/den
    def s(v):return {'mean':float(np.mean(v)),'p2_5':float(np.quantile(v,.025)),'p97_5':float(np.quantile(v,.975))}
    return {'n_boot':int(n_boot),'n_clusters':int(len(uniq)),'accuracy_delta':s(va),'log_score_delta':s(vl)}


def delta_point(pa:np.ndarray,pb:np.ndarray,y:np.ndarray)->dict:
    a=metrics(pa,y);b=metrics(pb,y)
    return {'accuracy_delta':None if a['accuracy'] is None else float(b['accuracy']-a['accuracy']), 'log_score_delta':None if a['mean_log_score'] is None else float(b['mean_log_score']-a['mean_log_score'])}


class RSSMonitor:
    def __init__(self, interval:float=.05):
        self.interval=interval;self._stop=False;self.peak_mb=None;self._t=None
    def __enter__(self):
        try:
            import psutil
            proc=psutil.Process(os.getpid()); self.peak_mb=proc.memory_info().rss/1048576
            def loop():
                while not self._stop:
                    try:self.peak_mb=max(self.peak_mb,proc.memory_info().rss/1048576)
                    except Exception:pass
                    time.sleep(self.interval)
            self._t=threading.Thread(target=loop,daemon=True);self._t.start()
        except Exception:self.peak_mb=None
        return self
    def __exit__(self,*args):
        self._stop=True
        if self._t:self._t.join(timeout=.5)


def model_size_bytes(model: Any) -> int:
    try:return len(pickle.dumps(model,protocol=pickle.HIGHEST_PROTOCOL))
    except Exception:return -1


def safe_float(x: Any) -> Any:
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,)):return float(x) if math.isfinite(float(x)) else None
    if isinstance(x,np.ndarray):return [safe_float(v) for v in x.tolist()]
    if isinstance(x,dict):return {str(k):safe_float(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [safe_float(v) for v in x]
    if isinstance(x,float):return x if math.isfinite(x) else None
    return x

def clustered_bootstrap_accuracy(probs: np.ndarray, y: np.ndarray, clusters: np.ndarray, n_boot:int=400, seed:int=20260917)->dict:
    probs=normalize_rows(probs); y=np.asarray(y,int); clusters=np.asarray(clusters).astype(str)
    if len(y)==0:
        return {'n_boot':int(n_boot),'n_clusters':0,'mean':None,'p2_5':None,'p97_5':None}
    pred=(probs.argmax(1)==y).astype(float)
    uniq,inv=np.unique(clusters,return_inverse=True)
    n=np.bincount(inv,minlength=len(uniq)).astype(float)
    s=np.bincount(inv,weights=pred,minlength=len(uniq))
    rng=np.random.default_rng(seed)
    draws=rng.integers(0,len(uniq),size=(int(n_boot),len(uniq)))
    den=n[draws].sum(1)
    vals=s[draws].sum(1)/den
    return {'n_boot':int(n_boot),'n_clusters':int(len(uniq)),'mean':float(vals.mean()),'p2_5':float(np.quantile(vals,.025)),'p97_5':float(np.quantile(vals,.975))}


def conservative_interval(a:dict,b:dict)->dict:
    vals=[a.get('p2_5'),b.get('p2_5'),a.get('p97_5'),b.get('p97_5')]
    if any(v is None for v in vals):
        return {'p2_5':None,'p97_5':None,'source':'unavailable'}
    return {'p2_5':float(min(a['p2_5'],b['p2_5'])),'p97_5':float(max(a['p97_5'],b['p97_5'])),'source':'envelope_household_week'}
