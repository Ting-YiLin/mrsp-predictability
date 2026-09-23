from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
files=['test_public_claims.py','test_formula_trace.py','test_release_integrity.py']
for f in files:
    rc=subprocess.call([sys.executable,str(ROOT/'tests'/f)],cwd=ROOT)
    if rc: raise SystemExit(rc)
rc=subprocess.call([sys.executable,str(ROOT/'reproduce/verify_release.py')],cwd=ROOT)
raise SystemExit(rc)
