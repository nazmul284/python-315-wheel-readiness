"""Can the top PyPI packages be installed on a new CPython on day one?

The question every team asks in the fortnight before a release is "can we
upgrade". The answer is decided by what wheels a project publishes, so that is
what this measures, read from the official PyPI JSON API rather than inferred.

Four outcomes per package, in order of precedence:

  pure      a wheel whose Python tag is py3/py2.py3, so it is version
            independent. Usually py3-none-any, but also py3-none-<platform>:
            ruff and uv ship a Rust binary that way, and it installs on every
            CPython even though it is not portable across operating systems.
  abi3      a cp3X-abi3 wheel whose floor is <= the target. The stable ABI is
            forward compatible, so one build covers every later version.
  built     a version-specific wheel for exactly this target (cp315-cp315).
  blocked   compiled wheels exist, but none that this target can use. pip falls
            back to building from source, which needs a toolchain and often fails.
"""
from __future__ import annotations
import concurrent.futures as cf
import json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "py315-wheel-readiness (+github.com/nazmul284)"}


def fetch(pkg: str) -> dict | None:
    url = f"https://pypi.org/pypi/{pkg}/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            return json.load(r)
    except Exception:
        return None


def classify(files: list[dict], major: int, minor: int) -> tuple[str, list[str]]:
    tag = f"cp{major}{minor}"
    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    names = [f["filename"] for f in wheels]
    if not wheels:
        return ("blocked", names)              # sdist only: always a source build
    # the PYTHON tag is what matters here, not the platform tag: py3-none-any
    # and py3-none-macosx_11_0_arm64 are both version independent. Matching only
    # "-none-any" mislabelled ruff, uv and playwright as blocked.
    if any(re.search(r"-(?:py3|py2\.py3)-none-", n) for n in names):
        return ("pure", names)
    # abi3 is forward compatible: cp39-abi3 installs on 3.15
    for n in names:
        m = re.search(r"-cp3(\d+)-abi3-", n)
        if m and int(m.group(1)) <= minor:
            return ("abi3", names)
    if any(f"-{tag}-" in n or f"-{tag}-{tag}" in n for n in names):
        return ("built", names)
    return ("blocked", names)


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    top = json.loads((ROOT / "results" / "top-pypi.json").read_text())["rows"][:n]
    pkgs = [r["project"] for r in top]
    out = []

    def work(item):
        rank, pkg = item
        d = fetch(pkg)
        if not d:
            return {"rank": rank, "package": pkg, "error": "pypi fetch failed"}
        ver = d["info"]["version"]
        files = d["releases"].get(ver, [])
        row = {"rank": rank, "package": pkg, "version": ver,
               "files": len(files),
               "requires_python": d["info"].get("requires_python") or ""}
        for label, (maj, mi) in (("py315", (3, 15)), ("py314", (3, 14))):
            verdict, names = classify(files, maj, mi)
            row[label] = verdict
        row["wheel_sample"] = [f["filename"] for f in files
                               if f.get("packagetype") == "bdist_wheel"][:4]
        return row

    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        for i, row in enumerate(pool.map(work, enumerate(pkgs, 1)), 1):
            out.append(row)
            if i % 50 == 0:
                print(f"  {i}/{len(pkgs)}", flush=True)

    dest = ROOT / "results" / f"classified-{n}.json"
    dest.write_text(json.dumps({"n": n, "rows": out}, indent=2))
    from collections import Counter
    for label in ("py315", "py314"):
        c = Counter(r.get(label, "error") for r in out)
        print(f"{label}: {dict(c)}")
    print("wrote", dest)


if __name__ == "__main__":
    main()
