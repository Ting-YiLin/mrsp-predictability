#!/usr/bin/env python3
"""Regression check: changing the current target must not change that event's pre-event features."""
import importlib.util, copy
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'run_external_test.py'
spec=importlib.util.spec_from_file_location('runner',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from datetime import datetime,timezone,timedelta
rows=[]
for i in range(8): rows.append({'event_id':f'E{i}','household_id':'H1','event_time':datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(days=i),'week':i+1,'group':'G','y':i%6})
a=m.build_features(rows,'G'); rows2=copy.deepcopy(rows); rows2[5]['y']=(rows2[5]['y']+1)%6; b=m.build_features(rows2,'G')
keys=['k','hh','mp','p1']
assert all(a[5][k]==b[5][k] for k in keys), (a[5],b[5])
print('NO_CURRENT_LABEL_LEAK_PASS')
