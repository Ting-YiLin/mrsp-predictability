from __future__ import annotations
import importlib,sys
bad=[]
for m in ["numpy","pandas","scipy"]:
    try: importlib.import_module(m)
    except Exception as e: bad.append((m,repr(e)))
parquet_ok=False
for m in ["pyarrow","fastparquet"]:
    try: importlib.import_module(m); parquet_ok=True; break
    except Exception: pass
if not parquet_ok: bad.append(("parquet_engine","pyarrow_or_fastparquet_required_for_real_CJ9"))
if bad:
    print("DEPENDENCY_FAIL",bad); raise SystemExit(2)
print("DEPENDENCY_PASS",sys.version)
