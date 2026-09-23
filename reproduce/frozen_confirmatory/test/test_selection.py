from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from code.materialize_confirmatory import select_confirmatory
cfg={'expected_prior_gen1':100,'representative_n':100,'department_challenge_target_n':100,'department_challenge_min_n':60,'department_challenge_caps':{'GROCERY':10,'__default__':25},'representative_salt':'R','department_salt':'D','department_order_salt':'O'}
depts=['GROCERY','PRODUCE','MEAT','MEAT-PCKGD','DRUG GM','DELI','PASTRY','SEAFOOD-PCKGD']
pool=[]
for i in range(360):
    pool.append({'stable_key':f'{i:064x}','group_name':f'G{i}','department':depts[i%len(depts)],'candidate_products':[str(i*10+j) for j in range(6)],'events_pre22':150,'households_pre22':50})
frozen={'selected':[{'stable_key':f'{i:064x}'} for i in range(100)]}
a,summary=select_confirmatory(pool,frozen,cfg);b,_=select_confirmatory(pool,frozen,cfg)
assert [x['stable_key'] for x in a]==[x['stable_key'] for x in b]
rep=[x for x in a if x['cohort']=='REPRESENTATIVE'];dep=[x for x in a if x['cohort']=='DEPARTMENT_CHALLENGE']
assert len(rep)==100 and len(dep)>=60 and len(dep)<=100
assert not ({x['stable_key'] for x in rep}&{x['stable_key'] for x in dep})
assert not ({x['stable_key'] for x in a}&{f'{i:064x}' for i in range(100)})
from collections import Counter
c=Counter(x['department'] for x in dep);assert c['GROCERY']<=10 and all(v<=25 for k,v in c.items() if k!='GROCERY')
print('SELECTION_PASS',summary,c)
