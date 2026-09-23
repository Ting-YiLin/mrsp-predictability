#!/usr/bin/env python3
from pathlib import Path
import csv, json, subprocess, sys, tempfile
HERE=Path(__file__).resolve().parent; KIT=HERE.parent
if not (HERE/'fixture_events.csv').exists() or not (HERE/'fixture_groups.csv').exists(): subprocess.run([sys.executable,str(HERE/'make_fixture.py')],check=True)
base=list(csv.reader((HERE/'fixture_events.csv').open(encoding='utf-8')))
cases={}
r=[x[:] for x in base]; r[2][0]=r[1][0]; cases['duplicate_event']=r
r=[x[:] for x in base]; r[1][4]='UNKNOWN'; cases['unknown_group']=r
r=[x[:] for x in base]; r[1][5]='NOT_A_SKU'; cases['outside_choice_set']=r
r=[x[:] for x in base]; r[-1][3]='1'; cases['week_inversion']=r
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    for name,rows in cases.items():
        p=td/f'{name}.csv'; o=td/f'{name}.json'
        with p.open('w',newline='',encoding='utf-8') as f: csv.writer(f).writerows(rows)
        cp=subprocess.run([sys.executable,str(KIT/'run_external_test.py'),'--events',str(p),'--groups',str(HERE/'fixture_groups.csv'),'--output',str(o)],capture_output=True,text=True)
        d=json.loads(o.read_text())
        assert cp.returncode==2 and d['execution_status']=='FAIL' and d['failures'],(name,cp.returncode,d)
        print('FAIL_CLOSED_PASS',name)
