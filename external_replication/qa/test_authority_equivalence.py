#!/usr/bin/env python3
from pathlib import Path
import sys, importlib.util, subprocess
import pandas as pd, numpy as np
HERE=Path(__file__).resolve().parent; KIT=HERE.parent; OUTPUT=KIT.parent
# Ensure fixture exists.
if not (HERE/'fixture_events.csv').exists() or not (HERE/'fixture_groups.csv').exists():
    subprocess.run([sys.executable,str(HERE/'make_fixture.py')],check=True)
spec=importlib.util.spec_from_file_location('ext',KIT/'run_external_test.py'); ext=importlib.util.module_from_spec(spec); spec.loader.exec_module(ext)
AUTH=OUTPUT/'REPO'/'reproduce'/'frozen_confirmatory'
if not AUTH.exists():
    print('AUTHORITY_EQUIVALENCE_SKIP: sibling REPO authority not present'); raise SystemExit(3)
sys.path.insert(0,str(AUTH))
from code.data import build_sequential_frame
from code.models import tune_b1,b1_probs
from code.predictability import p1_household
G,fg=ext.read_groups(HERE/'fixture_groups.csv'); assert not fg,fg
rows,fe=ext.read_events(HERE/'fixture_events.csv',G); assert not fe,fe
r=[x for x in rows if x['group']=='G1']; skus=G['G1']['skus']
df0=pd.DataFrame([{'household_id':x['household_id'],'basket_id':x['event_id'],'week':x['week'],'transaction_timestamp':pd.Timestamp(x['event_time']),'product_id':skus[x['y']],'choice_idx':x['y'],'panel_set_id':'G1'} for x in r])
a=build_sequential_frame(df0); b=ext.build_features(rows,'G1'); p1a=p1_household(a)
max_p1=max(abs(float(p1a[i])-b[i]['p1']) for i in range(len(b)))
max_mp=max(abs(float(getattr(ra,f'market_p{j}'))-b[i]['mp'][j]) for i,ra in enumerate(a.itertuples(index=False)) for j in range(6))
max_hh=max(abs(float(getattr(ra,f'hh_count{j}'))-b[i]['hh'][j]) for i,ra in enumerate(a.itertuples(index=False)) for j in range(6))
assert max_p1<1e-12 and max_mp<1e-12 and max_hh<1e-12,(max_p1,max_mp,max_hh)
for block in ext.BLOCKS:
    w=a.week.to_numpy(int); m={'FIT':w<=block['fit_max'],'TUNE':(w>=block['tune_min'])&(w<=block['tune_max'])}
    la=tune_b1(a,m,ext.LAMBDA_GRID); lb=ext.tune_lambdas(b,block); assert la==lb,(block['id'],la,lb)
    pa=b1_probs(a,la)
    for i,xr in enumerate(b):
        if block['eval_min']<=xr['week']<=block['eval_max']:
            lam=lb[ext.coarse_bin(xr['k'])]; x=[lam*xr['mp'][j]+xr['hh'][j] for j in range(6)]
            assert ext.argmax_first(x)==int(np.argmax(pa[i]))
print('AUTHORITY_EQUIVALENCE_PASS',{'max_p1_abs':max_p1,'max_market_p_abs':max_mp,'max_hh_count_abs':max_hh})
