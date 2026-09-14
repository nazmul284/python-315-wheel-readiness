"""Check the wheel-tag classification against what a resolver actually does.

The classification is a reading of filenames. This asks uv to resolve each
package for 3.15 with --only-binary, which fails exactly when no usable wheel
exists. If the two disagree, the classification is wrong, not uv.
"""
from __future__ import annotations
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# uv refuses to install into a bare interpreter, so resolve into a real venv.
# Without this every install fails with "consider creating a virtual environment"
# and the whole comparison silently reads as agreement for the blocked bucket.
PY315 = str(ROOT / ".venv-verify" / "bin" / "python")

SAMPLE = {
    "pure":    ["requests", "click", "ruff", "uv"],
    "abi3":    ["cryptography", "tokenizers", "psutil", "pynacl"],
    "built":   ["numpy", "orjson", "msgspec", "duckdb"],
    "blocked": ["pandas", "pyyaml", "aiohttp", "pyarrow", "asyncpg", "lz4"],
}

def resolve(pkg: str) -> tuple[bool, str]:
    p = subprocess.run(
        ["uv","pip","install","--python",PY315,"--only-binary",":all:",
         "--dry-run","--no-cache", pkg],
        capture_output=True, text=True, timeout=240)
    ok = p.returncode == 0
    blob = (p.stdout or "") + (p.stderr or "")
    note = ""
    if not ok:
        m = re.search(r"(no.*(wheel|binary|version).*)", blob, re.I)
        note = (m.group(1) if m else blob.strip().splitlines()[-1] if blob.strip() else "")[:110]
    return ok, note

def main() -> None:
    cls = {r["package"]: r["py315"]
           for r in json.load(open(ROOT/"results"/"classified-1000.json"))["rows"]}
    rows, mismatch = [], 0
    print(f"python: {PY315}\n")
    for bucket, pkgs in SAMPLE.items():
        for pkg in pkgs:
            ok, note = resolve(pkg)
            predicted_ok = bucket != "blocked"
            agree = ok == predicted_ok
            mismatch += (not agree)
            rows.append({"package": pkg, "classified": cls.get(pkg, bucket),
                         "resolver_installs": ok, "agrees": agree, "note": note})
            flag = "ok " if agree else "MISMATCH"
            print(f"  {flag} {pkg:<14} classified={bucket:<8} uv_installs={str(ok):<5} {note}")
    out = {"python": PY315, "mismatches": mismatch, "rows": rows}
    (ROOT/"results"/"verify.json").write_text(json.dumps(out, indent=2))
    print(f"\n{len(rows)-mismatch}/{len(rows)} agree with the resolver")

if __name__ == "__main__":
    main()
