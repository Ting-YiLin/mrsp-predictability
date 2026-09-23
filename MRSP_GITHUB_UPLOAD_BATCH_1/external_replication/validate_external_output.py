#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
EXPECTED={"0.6":0.3608488067145302,"0.7":0.5231119438280639,"0.8":0.6660270791857679}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); a=ap.parse_args()
    d=json.loads(a.input.read_text(encoding='utf-8')); errs=[]
    if d.get('protocol')!='MRSP_EXTERNAL_STRICT_ZERO_SHOT_V1': errs.append('protocol')
    if d.get('execution_status')!='PASS': errs.append('execution_status')
    if d.get('adaptation_performed') is not False: errs.append('adaptation_performed')
    if d.get('p1_cutoffs_recalibrated') is not False: errs.append('p1_cutoffs_recalibrated')
    if d.get('privacy',{}).get('household_ids_written') is not False: errs.append('privacy_household')
    if d.get('privacy',{}).get('event_level_rows_written') is not False: errs.append('privacy_events')
    if d.get('failures'): errs.append('failures_nonempty')
    cuts=d.get('frozen',{}).get('p1_cutoffs',{})
    for k,v in EXPECTED.items():
        if k not in cuts or not math.isclose(float(cuts[k]),v,rel_tol=0,abs_tol=1e-15): errs.append('cutoff_'+k)
    m=d.get('metrics',{})
    if int(m.get('total_eval_events',0))<=0: errs.append('no_eval_events')
    # Output must not contain obvious household/event row keys anywhere.
    txt=a.input.read_text(encoding='utf-8').lower()
    for forbidden in ['"household_id"','"event_id"']:
        if forbidden in txt: errs.append('forbidden_key_'+forbidden)
    if errs:
        print('EXTERNAL_OUTPUT_VALIDATE_FAIL',','.join(errs)); return 2
    print('EXTERNAL_OUTPUT_VALIDATE_PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
