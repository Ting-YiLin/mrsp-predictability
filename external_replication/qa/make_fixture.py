#!/usr/bin/env python3
from pathlib import Path
import csv, datetime
ROOT=Path(__file__).resolve().parent
# Two groups, six SKUs each, 53 weeks, deterministic synthetic history.
groups=[['G1','GROCERY']+[f'G1_S{i}' for i in range(6)],['G2','PRODUCE']+[f'G2_S{i}' for i in range(6)]]
with (ROOT/'fixture_groups.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['product_group_id','department','sku_0','sku_1','sku_2','sku_3','sku_4','sku_5']); w.writerows(groups)
start=datetime.datetime(2025,1,6,tzinfo=datetime.timezone.utc); rows=[]; n=0
for week in range(1,54):
    for gid,_dept,*skus in groups:
        for h in range(12):
            n+=1
            # Stable households dominate; a few switch, creating a meaningful selective frontier.
            idx=h%6 if h<9 else (week+h)%6
            t=start+datetime.timedelta(days=7*(week-1),hours=h)
            rows.append([f'E{n:06d}',f'H{h:02d}',t.isoformat().replace('+00:00','Z'),week,gid,skus[idx]])
with (ROOT/'fixture_events.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['event_id','household_id','event_time','week_index','product_group_id','target_sku']); w.writerows(rows)
print('FIXTURE_WRITTEN',len(rows))
