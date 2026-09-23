from __future__ import annotations
import argparse,hashlib,os,subprocess,sys,time,traceback,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from code.common import read_json,write_json,sha256

def run_stream(cmd,log,env):
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf-8') as f:
        f.write(f"\n===== ATTEMPT {time.strftime('%Y-%m-%d %H:%M:%S')} =====\nCMD={' '.join(map(str,cmd))}\n");f.flush()
        p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=env,errors='replace')
        for line in p.stdout or []:print(line,end='',flush=True);f.write(line);f.flush()
        rc=p.wait();f.write(f'RETURN_CODE={rc}\n');return rc

def textsha(s):return hashlib.sha256(s.encode()).hexdigest()
def code_identity():return textsha('\n'.join(f'{p.relative_to(ROOT)}|{sha256(p)}' for base in ['code','cfg','tools'] for p in sorted((ROOT/base).glob('*')) if p.is_file()))
def source_identity(pre):
    parts=[f"{x['path']}|{x['size']}|{x['sha256']}" for x in pre.get('source_hashes',[])]
    parts += [f"{x['set_id']}|{x['stable_key']}|{x['meta_sha256']}|{x['events_sha256']}" for x in pre.get('selected_sets',[])]
    return textsha('\n'.join(sorted(parts)))
def failzip(work,reason):
    write_json(work/'failure.json',{'status':'FAIL','reason':reason,'time':time.time()});z=ROOT/f'MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE_{int(time.time())}.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as zz:
        for p in work.rglob('*'):
            if p.is_file() and p.stat().st_size<50_000_000:zz.write(p,Path('MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE')/'w'/p.relative_to(work))
        for rel in ['cfg','code','tools','test','review','README.md','START.md','START_PROMPT.txt','CONTRACT.md','SPEC_TRACE.csv','GATE_ACCEPT.md','SIMULATION_REVIEW.md']:
            p=ROOT/rel
            if p.is_dir():
                for q in p.rglob('*'):
                    if q.is_file() and q.stat().st_size<5_000_000:zz.write(q,Path('MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE')/'package'/rel/q.relative_to(p))
            elif p.exists():zz.write(p,Path('MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE')/'package'/rel)
    return z

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',default=str(ROOT/'w'));ap.add_argument('--cj9');ap.add_argument('--skip-tests',action='store_true');a=ap.parse_args();work=Path(a.work);work.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env.setdefault('OMP_NUM_THREADS','3');env.setdefault('MKL_NUM_THREADS','3');env.setdefault('OPENBLAS_NUM_THREADS','3')
    try:
        if not a.skip_tests:
            for sc in ['test_selection.py','test_frozen_rules.py','test_no_leak.py','test_action_rules.py']:
                if run_stream([sys.executable,str(ROOT/'test'/sc)],work/'logs'/sc.replace('.py','.log'),env):raise RuntimeError(sc+'_FAILED')
        if run_stream([sys.executable,str(ROOT/'tools/spec_trace_check.py')],work/'logs/spec_trace_check.log',env):raise RuntimeError('SPEC_TRACE_CHECK_FAILED')
        cmd=[sys.executable,str(ROOT/'tools/preflight.py'),'--work',str(work)]
        if a.cj9:cmd += ['--cj9',a.cj9]
        if run_stream(cmd,work/'logs/preflight.log',env):raise RuntimeError('PREFLIGHT_FAILED')
        pre=read_json(work/'preflight.json');ident={'source_identity':source_identity(pre),'code_config_identity':code_identity()};sp=work/'state.json';old=read_json(sp) if sp.exists() else None
        if old and old.get('identity')!=ident:raise RuntimeError('RESUME_IDENTITY_MISMATCH')
        st=old or {'campaign':'MRSP_PREDICTABILITY_CONFIRMATORY_V1','identity':ident,'status':'RUNNING','created_at':time.time()};st['last_started_at']=time.time();write_json(sp,st)
        rc=run_stream([sys.executable,str(ROOT/'code/run_confirmatory.py'),'--work',str(work/'FULL'),'--materialized-root',str(work/'materialized')],work/'logs/full.log',env)
        if rc:raise RuntimeError(f'FULL_FAILED_RC_{rc}')
        st['status']='FULL_COMPLETE';st['full_complete_at']=time.time();write_json(sp,st)
        if run_stream([sys.executable,str(ROOT/'tools/package_audit.py'),'--work',str(work)],work/'logs/package.log',env):raise RuntimeError('PACKAGE_FAILED')
        print('COMPLETE. Return only MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_<run_id>.zip')
    except Exception as e:
        traceback.print_exc();z=failzip(work,repr(e));print('FAILURE_BUNDLE='+str(z));raise
if __name__=='__main__':main()
