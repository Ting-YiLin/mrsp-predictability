from __future__ import annotations
import math
import numpy as np
from scipy.optimize import minimize


def maturity(k):
    k=np.asarray(k,float)
    return np.clip(np.log1p(k)/math.log(21.0),0.0,1.0)


def p1_household(df):
    m=maturity(df.k.to_numpy(float))
    top=np.clip(df.hh_top_share.to_numpy(float),0,1)
    ent=np.clip(df.hh_entropy.to_numpy(float),0,1)
    sw=np.clip(df.switch_rate.to_numpy(float),0,1)
    rc=np.clip(df.recent_concentration.to_numpy(float),0,1)
    core=.30*top+.25*(1-ent)+.25*(1-sw)+.20*rc
    return np.clip(m*core,0,1)


def distribution_score(y_past, week_past, eval_min, drift_weeks=5, J=6):
    y=np.asarray(y_past,int);w=np.asarray(week_past,int)
    if len(y)==0:return {'score':0.5,'concentration':1/J,'entropy_stability':0.0,'drift':1.0}
    c=np.bincount(y,minlength=J).astype(float)+1e-6;p=c/c.sum();conc=float(p.max())
    nz=p[p>0]; h=float(-(nz*np.log(nz)).sum()/math.log(J)); est=1-h
    recent=y[w>=int(eval_min)-int(drift_weeks)]
    if len(recent)<5:drift=.5
    else:
        cr=np.bincount(recent,minlength=J).astype(float)+1e-6;pr=cr/cr.sum();drift=float(.5*np.abs(pr-p).sum())
    stable=1-min(drift/.35,1.0)
    score=.35*conc+.30*est+.35*stable
    return {'score':float(np.clip(score,0,1)),'concentration':conc,'entropy_stability':est,'drift':drift}


def _fit_logistic(X,y,l2=1.0):
    X=np.asarray(X,float);y=np.asarray(y,float)
    if len(y)<50 or len(np.unique(y))<2:return None
    def fg(b):
        z=np.clip(X@b,-35,35);p=1/(1+np.exp(-z))
        loss=float(np.mean(np.logaddexp(0,z)-y*z)+.5*l2*np.sum(b[1:]**2)/len(y))
        g=X.T@(p-y)/len(y);g[1:]+=l2*b[1:]/len(y)
        return loss,g
    res=minimize(lambda b:fg(b),np.zeros(X.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':300})
    return {'beta':res.x,'success':bool(res.success),'message':str(res.message)}


def fit_logistic(X,y,l2=1.0):
    return _fit_logistic(X,y,l2)


def apply_logistic(model,X):
    if model is None:return np.full(len(X),np.nan)
    z=np.clip(np.asarray(X,float)@np.asarray(model['beta'],float),-35,35)
    return 1/(1+np.exp(-z))
