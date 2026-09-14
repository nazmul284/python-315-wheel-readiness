"""Render every table in the article and README from the result JSON."""
from __future__ import annotations
import json, pathlib
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent / "results"
ROWS = json.loads((R / "classified-1000.json").read_text())["rows"]
RES = json.loads((R / "resolve_all.json").read_text())["rows"]
COMPILED = [r for r in ROWS if r["py315"] != "pure"]

def row(c, w): return "".join(str(x).ljust(n) for x, n in zip(c, w)).rstrip()
def rule(w):   return "-" * sum(w)

def breakdown() -> str:
    c15, c14 = Counter(r["py315"] for r in ROWS), Counter(r["py314"] for r in ROWS)
    w = [30, 12, 12]
    out = [row(["wheel kind", "on 3.15", "on 3.14"], w), rule(w)]
    labels = [("pure", "pure python (any version)"), ("abi3", "stable ABI (abi3)"),
              ("built", "built for this version"), ("blocked", "no usable wheel")]
    for k, lab in labels:
        out.append(row([lab, c15[k], c14[k]], w))
    out += [rule(w), row(["total", len(ROWS), len(ROWS)], w), "",
            f'"ready" = {c15["pure"]+c15["abi3"]+c15["built"]}/1000 '
            f'({(c15["pure"]+c15["abi3"]+c15["built"])/10:.1f}%) on 3.15.',
            f'{c15["pure"]} of those are pure python and were never at risk.']
    return "\n".join(out)

def compiled_cut() -> str:
    c15, c14 = Counter(r["py315"] for r in COMPILED), Counter(r["py314"] for r in COMPILED)
    n = len(COMPILED)
    w = [26, 10, 10, 10, 10]
    out = [row(["of the 140 compiled", "3.15", "share", "3.14", "share"], w), rule(w)]
    for k, lab in (("abi3", "stable ABI"), ("built", "built for it"),
                   ("blocked", "NOT installable")):
        out.append(row([lab, c15[k], f"{c15[k]/n*100:.1f}%",
                        c14[k], f"{c14[k]/n*100:.1f}%"], w))
    out += ["", "3.14 is what settled looks like, one year on."]
    return "\n".join(out)

def blockers() -> str:
    tread = [r for r in ROWS if r["py314"] == "built" and r["py315"] == "blocked"]
    w = [10, 29, 14, 16]
    out = [row(["pypi rank", "package", "version", "had 3.14 wheel"], w), rule(w)]
    for r in sorted(tread, key=lambda x: x["rank"])[:16]:
        out.append(row([f"#{r['rank']}", r["package"], r["version"], "yes"], w))
    out += ["", f"{len(tread)} packages shipped a version-specific wheel for 3.14",
            "and have not yet shipped one for 3.15."]
    return "\n".join(out)

def resolver() -> str:
    ok = sum(1 for r in RES if r["resolver_ok"])
    latest = sum(1 for r in RES if r["latest_is_installable"])
    agree = sum((r["resolver_ok"] is True) == (r["py315"] != "blocked") for r in RES)
    w = [46, 12]
    out = [row(["of the 140 compiled packages", "count"], w), rule(w),
           row(["uv installs something, binary only", ok], w),
           row(["uv installs the LATEST release", latest], w),
           row(["uv installs nothing", len(RES) - ok], w), "",
           f"tag reading and resolver agree on {agree}/{len(RES)} "
           f"({agree/len(RES)*100:.1f}%).",
           f"{ok - latest} packages install only by silently taking an older release."]
    return "\n".join(out)

if __name__ == "__main__":
    for name, fn in (("BREAKDOWN", breakdown), ("COMPILED", compiled_cut),
                     ("BLOCKERS", blockers), ("RESOLVER", resolver)):
        print(f"\n===== {name} =====\n{fn()}")
