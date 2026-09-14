"""Ask uv to install every compiled package on 3.15, binary-only.

The tag classification answers the maintainer's question: does the latest
release publish a wheel this Python can use? This answers the user's: can I
install the thing today, on this machine? They differ in two ways, both real —
a resolver may fall back to an older release that does have a wheel, and a wheel
may exist for Linux but not for this laptop's arm64 macOS.
"""
from __future__ import annotations
import concurrent.futures as cf
import json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY315 = str(ROOT / ".venv-verify" / "bin" / "python")

def resolve(row):
    pkg = row["package"]
    try:
        p = subprocess.run(
            ["uv","pip","install","--python",PY315,"--only-binary",":all:",
             "--dry-run","--no-cache", pkg],
            capture_output=True, text=True, timeout=300)
        ok = p.returncode == 0
        blob = (p.stdout or "") + (p.stderr or "")
        ver = None
        m = re.search(rf"\+ {re.escape(pkg)}==([^\s]+)", blob)
        if m: ver = m.group(1)
        return {**{k: row[k] for k in ("rank","package","version","py315","py314")},
                "resolver_ok": ok, "resolver_version": ver,
                "latest_is_installable": bool(ok and ver == row["version"])}
    except subprocess.TimeoutExpired:
        return {**{k: row[k] for k in ("rank","package","version","py315","py314")},
                "resolver_ok": None, "resolver_version": None,
                "latest_is_installable": None}

rows = json.load(open(ROOT/"results"/"classified-1000.json"))["rows"]
compiled = [r for r in rows if r["py315"] != "pure"]
print(f"resolving {len(compiled)} compiled packages on 3.15 …")
out = []
with cf.ThreadPoolExecutor(max_workers=6) as pool:
    for i, r in enumerate(pool.map(resolve, compiled), 1):
        out.append(r)
        if i % 20 == 0: print(f"  {i}/{len(compiled)}", flush=True)

(ROOT/"results"/"resolve_all.json").write_text(json.dumps({"rows": out}, indent=2))
from collections import Counter
print("resolver says installable:", Counter(r["resolver_ok"] for r in out))
print("latest release installable:", Counter(r["latest_is_installable"] for r in out))
agree = sum((r["resolver_ok"] is True) == (r["py315"] != "blocked") for r in out)
print(f"tag-vs-resolver agreement: {agree}/{len(out)} = {agree/len(out)*100:.1f}%")
