from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
readme=(ROOT/'README.md').read_text(encoding='utf-8')
assert 'six-SKU choice set' in readme
assert '40% of customers' not in readme
assert 'does **not** predict whether a household will buy bread' in readme
assert 'entire future basket' in readme
exp=json.loads((ROOT/'results/EXPECTED_RESULTS.json').read_text())
assert exp['confirmation_grade']=='CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT'
print('TEST_PUBLIC_CLAIMS_PASS')
