from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/'src/predictability.py').read_text(encoding='utf-8')
assert 'core=.30*top+.25*(1-ent)+.25*(1-sw)+.20*rc' in p
assert 'math.log(21.0)' in p
m=(ROOT/'src/models.py').read_text(encoding='utf-8')
assert 'x=lam*mp+hc' in m
print('TEST_FORMULA_TRACE_PASS')
