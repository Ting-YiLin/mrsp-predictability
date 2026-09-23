from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parents[1]
exp=json.loads((ROOT/'results/EXPECTED_RESULTS.json').read_text())
gen=json.loads((ROOT/'results/machine/generalization_summary.json').read_text())
con=json.loads((ROOT/'results/machine/confirmatory_summary.json').read_text())
score=json.loads((ROOT/'results/machine/confirmation_scorecard.json').read_text())
tol=float(exp['tolerance_abs'])

def close(name,a,b):
    ok=abs(float(a)-float(b))<=tol
    print(('PASS' if ok else 'FAIL'),name,a,'expected',b)
    return ok

oks=[]
oks.append(score['grade']==exp['confirmation_grade'])
print(('PASS' if oks[-1] else 'FAIL'),'confirmation_grade',score['grade'])
# batch1
for t in ['0.6','0.7','0.8']:
    r=next(x for x in gen['policy_summary'] if x['policy']=='GLOBAL_P1_B1' and str(x['target'])==t)
    oks += [close('batch1 '+t+' coverage',r['coverage'],exp['batch1']['p1'][t]['coverage']), close('batch1 '+t+' accuracy',r['accuracy'],exp['batch1']['p1'][t]['accuracy'])]
# representative
for t in ['0.6','0.7','0.8']:
    r=next(x for x in con['cohort_summary'] if x['cohort']=='REPRESENTATIVE' and x['policy']=='GLOBAL_P1_B1' and str(x['target'])==t)
    oks += [close('confirm '+t+' coverage',r['coverage'],exp['representative']['p1'][t]['coverage']), close('confirm '+t+' accuracy',r['accuracy'],exp['representative']['p1'][t]['accuracy'])]
r=next(x for x in con['cohort_summary'] if x['cohort']=='REPRESENTATIVE' and x['policy']=='BASE_B1_ALL' and x['target']==0.6)
oks.append(close('confirm B1 all accuracy',r['accuracy'],exp['representative']['b1_all_accuracy']))
r=next(x for x in con['cohort_summary'] if x['cohort']=='DEPARTMENT_CHALLENGE' and x['policy']=='GLOBAL_P1_B1' and x['target']==0.6)
oks += [close('department coverage',r['coverage'],exp['department_challenge']['p1_0.6']['coverage']), close('department accuracy',r['accuracy'],exp['department_challenge']['p1_0.6']['accuracy'])]
oks.append(score['department_supported']==exp['department_challenge']['supported_departments']); print(('PASS' if oks[-1] else 'FAIL'),'supported departments',score['department_supported'])
oks.append(score['department_positive']==exp['department_challenge']['positive_departments']); print(('PASS' if oks[-1] else 'FAIL'),'positive departments',score['department_positive'])
if all(oks):
    print('RELEASE_EVIDENCE_VERIFY_PASS')
    raise SystemExit(0)
print('RELEASE_EVIDENCE_VERIFY_FAIL')
raise SystemExit(2)
