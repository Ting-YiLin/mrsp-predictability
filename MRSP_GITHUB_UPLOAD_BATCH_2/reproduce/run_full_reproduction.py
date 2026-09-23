from pathlib import Path
import argparse, subprocess, sys, shutil, os
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--cj9',required=True); ap.add_argument('--work',default=str(ROOT/'reproduction_work')); ap.add_argument('--skip-tests',action='store_true'); a=ap.parse_args()
frozen=ROOT/'reproduce/frozen_confirmatory'; work=Path(a.work).resolve(); work.mkdir(parents=True,exist_ok=True)
cmd=[sys.executable,str(frozen/'tools/run_pipeline.py'),'--work',str(work),'--cj9',str(Path(a.cj9).resolve())]
if a.skip_tests: cmd.append('--skip-tests')
print('RUN', ' '.join(cmd), flush=True)
rc=subprocess.call(cmd,cwd=frozen)
if rc: raise SystemExit(rc)
summary=work/'FULL/summary.json'
if not summary.exists(): raise SystemExit('MISSING_SUMMARY:'+str(summary))
verify=[sys.executable,str(ROOT/'reproduce/verify_expected_results.py'),'--summary',str(summary)]
raise SystemExit(subprocess.call(verify,cwd=ROOT))
