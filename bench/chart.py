"""Two figures, both drawn from the result JSON.

Figure 1 (cover) is the whole argument: among packages that actually ship a
compiled wheel, the picture for 3.15 looks nothing like the settled picture for
3.14 — and the stable-ABI slice is identical in both, because those packages did
no work for either.

Every segment is directly labelled: the aqua sits below 3:1 on the light
surface, so the palette's relief rule requires visible labels.
"""
from __future__ import annotations
import json, pathlib
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROWS = json.loads((ROOT / "results" / "classified-1000.json").read_text())["rows"]
COMPILED = [r for r in ROWS if r["py315"] != "pure"]

SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"
GRID, AXIS, GREY = "#e1e0d9", "#c3c2b7", "#d8d7d0"
BLUE, AQUA, CRITICAL = "#2a78d6", "#1baf7a", "#d03b3b"

def stacked(ax, y, counts, keys, colors, total, labels):
    left = 0
    for k, c, lab in zip(keys, colors, labels):
        v = counts[k]
        ax.barh(y, v, left=left, height=0.5, color=c, zorder=3)
        if v / total > 0.04:                      # relief rule: label every segment
            ax.text(left + v / 2, y, str(v), ha="center", va="center",
                    fontsize=10, color="white", weight="bold", zorder=5)
        left += v
    return left

# ------------------------------------------------- figure 1: the compiled cut
fig, ax = plt.subplots(figsize=(8.6, 3.9), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
keys = ["abi3", "built", "blocked"]
cols = [BLUE, AQUA, CRITICAL]
labs = ["stable ABI (abi3)", "built for this version", "no usable wheel"]
n = len(COMPILED)
for y, field, name in ((0, "py315", "Python 3.15\nships Oct 1"),
                       (1, "py314", "Python 3.14\none year old")):
    stacked(ax, y, Counter(r[field] for r in COMPILED), keys, cols, n, labs)
ax.set_yticks([0, 1]); ax.set_yticklabels(
    ["Python 3.15\nships Oct 1", "Python 3.14\none year old"],
    fontsize=9.5, color=INK, linespacing=1.5)
ax.set_ylim(-0.55, 1.55)
ax.set_xlim(0, n)
ax.set_xlabel(f"the {n} of the top 1,000 PyPI packages that ship a compiled wheel",
              fontsize=9, color=MUTED, labelpad=8)
ax.tick_params(axis="x", colors=MUTED, labelsize=8.5, length=0)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(AXIS)
h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cols]
ax.legend(h, labs, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3,
          frameon=False, fontsize=8.8, labelcolor=MUTED,
          handlelength=1.1, handleheight=1.1)
fig.text(0.035, 0.945, "64 of the 140 compiled packages cannot install on Python 3.15",
         fontsize=13.5, color=INK, ha="left", va="center", weight="bold")
fig.text(0.035, 0.882, "Measured 2026-09-14 from the PyPI API. The stable-ABI slice is "
         "identical in both rows: those packages did nothing.",
         fontsize=9, color=MUTED, ha="left", va="center")
fig.subplots_adjust(left=0.175, right=0.98, top=0.80, bottom=0.30)
fig.savefig(ROOT / "results" / "compiled.png", facecolor=SURFACE)
print("wrote compiled.png")

# ------------------------------------------- figure 2: why 93.6% is misleading
fig2, ax2 = plt.subplots(figsize=(8.6, 3.1), dpi=200)
fig2.patch.set_facecolor(SURFACE); ax2.set_facecolor(SURFACE)
c15 = Counter(r["py315"] for r in ROWS)
left = 0
for k, c, lab in (("pure", GREY, "pure python"), ("abi3", BLUE, "stable ABI"),
                  ("built", AQUA, "built for 3.15"), ("blocked", CRITICAL, "no wheel")):
    v = c15[k]
    ax2.barh(0, v, left=left, height=0.42, color=c, zorder=3)
    txt = "white" if k != "pure" else INK
    if v > 30:
        ax2.text(left + v / 2, 0, str(v), ha="center", va="center",
                 fontsize=10, color=txt, weight="bold", zorder=5)
    else:
        ax2.text(left + v / 2, 0.30, str(v), ha="center", va="bottom",
                 fontsize=9, color=c, weight="bold", zorder=5)
    left += v
ax2.set_xlim(0, 1000); ax2.set_ylim(-0.45, 0.62)
ax2.set_yticks([])
ax2.set_xlabel("top 1,000 PyPI packages by download count", fontsize=9,
               color=MUTED, labelpad=8)
ax2.tick_params(axis="x", colors=MUTED, labelsize=8.5, length=0)
ax2.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax2.set_axisbelow(True)
for s in ("top", "right", "bottom", "left"): ax2.spines[s].set_visible(False)
h2 = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (GREY, BLUE, AQUA, CRITICAL)]
ax2.legend(h2, ["pure python, never at risk", "stable ABI", "built for 3.15",
                "no usable wheel"],
           loc="upper center", bbox_to_anchor=(0.5, -0.34), ncol=4, frameon=False,
           fontsize=8.6, labelcolor=MUTED, handlelength=1.1, handleheight=1.1)
fig2.text(0.035, 0.93, "The 93.6% \"ready\" figure is 860 packages that were never at risk",
          fontsize=13, color=INK, ha="left", va="center", weight="bold")
fig2.subplots_adjust(left=0.05, right=0.98, top=0.78, bottom=0.36)
fig2.savefig(ROOT / "results" / "breakdown.png", facecolor=SURFACE)
print("wrote breakdown.png")
