from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
cut=json.loads((ROOT/'cfg/frozen_p1_cutoffs.json').read_text())
assert abs(cut['0.6']['cutoff']-0.3608488067145302)<1e-15
assert abs(cut['0.7']['cutoff']-0.5231119438280639)<1e-15
assert abs(cut['0.8']['cutoff']-0.6660270791857679)<1e-15
frozen=json.loads((ROOT/'cfg/frozen_core_hashes.json').read_text())['hashes']
for rel,h in frozen.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,(rel,h)
s=(ROOT/'code/run_confirmatory.py').read_text()
assert "frozen_p1_cutoffs.json" in s and 'choose_cutoff' not in s and 'choose_balanced_global_cutoff' not in s
print('FROZEN_RULES_PASS')
