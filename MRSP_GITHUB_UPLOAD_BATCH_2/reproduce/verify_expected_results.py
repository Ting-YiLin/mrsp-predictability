from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--summary',required=True); a=ap.parse_args()
exp=json.loads((ROOT/'results/EXPECTED_RESULTS.json').read_text()); obj=json.loads(Path(a.summary).read_text()); tol=float(exp['tolerance_abs']); score=obj['confirmation_scorecard']; oks=[]
def close(name,a,b):
    ok=abs(float(a)-float(b))<=tol; print(('PASS' if ok else 'FAIL'),name,a,'expected',b); return ok
oks.append(score['grade']==exp['confirmation_grade']); print(('PASS' if oks[-1] else 'FAIL'),'confirmation grade',score['grade'])
for t in ['0.6','0.7','0.8']:
    r=next(x for x in obj['cohort_summary'] if x['cohort']=='REPRESENTATIVE' and x['policy']=='GLOBAL_P1_B1' and str(x['target'])==t)
    oks += [close('coverage '+t,r['coverage'],exp['representative']['p1'][t]['coverage']),close('accuracy '+t,r['accuracy'],exp['representative']['p1'][t]['accuracy'])]
r=next(x for x in obj['cohort_summary'] if x['cohort']=='DEPARTMENT_CHALLENGE' and x['policy']=='GLOBAL_P1_B1' and x['target']==0.6)
oks += [close('department coverage',r['coverage'],exp['department_challenge']['p1_0.6']['coverage']),close('department accuracy',r['accuracy'],exp['department_challenge']['p1_0.6']['accuracy'])]
if all(oks): print('FULL_REPRODUCTION_EXPECTED_RESULTS_PASS'); raise SystemExit(0)
print('FULL_REPRODUCTION_EXPECTED_RESULTS_FAIL'); raise SystemExit(2)
