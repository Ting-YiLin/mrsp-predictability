from __future__ import annotations
import numpy as np
import pandas as pd

def eval_actions(cur:pd.DataFrame,actions:np.ndarray)->dict:
    a=np.asarray(actions,object);accpt=a!='ABSTAIN';n=len(cur);na=int(accpt.sum())
    if na==0:return {'n':int(n),'accepted_n':0,'coverage':0.0,'accuracy':None,'b0_accuracy_same':None,'personalization_gain_same':None,'b0_fraction':0.0,'b1_fraction':0.0,'abstain_fraction':1.0}
    c=np.zeros(n,float);b0=a=='B0';b1=a=='B1';c[b0]=cur.loc[b0,'b0_correct'];c[b1]=cur.loc[b1,'b1_correct'];bb=cur.loc[accpt,'b0_correct'].to_numpy(float)
    return {'n':int(n),'accepted_n':na,'coverage':float(na/n),'accuracy':float(c[accpt].mean()),'b0_accuracy_same':float(bb.mean()),'personalization_gain_same':float(c[accpt].mean()-bb.mean()),'b0_fraction':float(b0.mean()),'b1_fraction':float(b1.mean()),'abstain_fraction':float((~accpt).mean())}
