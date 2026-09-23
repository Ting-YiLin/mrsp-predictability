from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd, numpy as np
from code.generalization import simple_action,actions_from
# generic -> B0 all
h=pd.DataFrame({'block':['W1']*100+['W2']*100,'b0_correct':[1]*170+[0]*30,'b1_correct':[1]*171+[0]*29,'p1':np.linspace(0,1,200),'set_id':['X']*200})
d=simple_action(h,.7,{'cutoff':.5},.03,100,2,50);assert d['action']=='USE_B0_ALL',d
# personal -> B1 all
h['b0_correct']=[1]*80+[0]*120;h['b1_correct']=[1]*160+[0]*40
d=simple_action(h,.7,{'cutoff':.5},.03,100,2,50);assert d['action']=='USE_B1_ALL',d
# hard -> abstain
h['b0_correct']=[1]*40+[0]*160;h['b1_correct']=[1]*45+[0]*155
d=simple_action(h,.7,{'cutoff':.8},.03,100,2,50);assert d['action'] in {'ABSTAIN','USE_B0_SELECTIVE'},d
print('ACTION_RULES_PASS')
