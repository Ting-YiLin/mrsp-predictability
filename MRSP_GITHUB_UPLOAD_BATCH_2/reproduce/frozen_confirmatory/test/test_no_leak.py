from pathlib import Path
import sys,inspect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd,numpy as np
from code.predictability import p1_household
from code import materialize_confirmatory as mc
# P1 cannot see current outcome.
d=pd.DataFrame({'k':[5,10],'hh_top_share':[.8,.4],'hh_entropy':[.2,.8],'switch_rate':[.1,.7],'recent_concentration':[.9,.3],'y':[0,1]})
a=p1_household(d);d['y']=[5,5];b=p1_household(d);assert np.allclose(a,b)
# Candidate construction must explicitly use weeks 1..22, not future evaluation metrics.
s=inspect.getsource(mc.build_candidate_pool)
assert 'range(1,23)' in s
for bad in ['b0_correct','b1_correct','accuracy','W3','W4','W5','W6']:
    assert bad not in s,bad
print('NO_LEAK_PASS')
