# python-315-wheel-readiness

How ready are the top PyPI packages for Python 3.15, split by the kind of wheel they
publish? Companion repository for *93.6% of the Top 1,000 PyPI Packages Are Python
3.15-Ready. 64 of the 140 That Compile Are Not.*

Measured **2026-09-14** against CPython **3.15.0rc2** on an Apple M2 / macOS 26.6.2
(arm64). Package list generated 2026-09-01 from PyPI's ClickHouse download statistics.

The point of this repo is a distinction the published readiness trackers explicitly do not
make: they count pure-Python, stable-ABI and version-specific wheels as equally "ready".
Those three mean completely different things.

## Headline

```
wheel kind                    on 3.15     on 3.14
------------------------------------------------------
pure python (any version)     860         860
stable ABI (abi3)             33          33
built for this version        43          99
no usable wheel               64          8
------------------------------------------------------
total                         1000        1000

"ready" = 936/1000 (93.6%) on 3.15.
860 of those are pure python and were never at risk.
```

Strip the pure-Python packages, which are version-independent by construction and were
never capable of being unready, and 140 remain. That is the only population that can block
an upgrade:

```
of the 140 compiled       3.15      share     3.14      share
------------------------------------------------------------------
stable ABI                33        23.6%     33        23.6%
built for it              43        30.7%     99        70.7%
NOT installable           64        45.7%     8         5.7%

3.14 is what settled looks like, one year on.
```

## The treadmill

```
pypi rank package                      version       had 3.14 wheel
---------------------------------------------------------------------
#14       pyyaml                       6.0.3         yes
#34       markupsafe                   3.0.3         yes
#39       pandas                       3.0.5         yes
#49       aiohttp                      3.14.3        yes
#95       pyarrow                      25.0.1        yes
#146      uvloop                       0.22.1        yes
#150      httptools                    0.8.0         yes
#207      zstandard                    0.25.0        yes
#223      google-crc32c                1.8.0         yes
#240      snowflake-connector-python   4.7.3         yes
#285      psycopg-binary               3.3.5         yes
#296      asyncpg                      0.31.0        yes
#304      fastuuid                     0.14.0        yes
#318      brotli                       1.2.0         yes
#323      pymongo                      4.18.1        yes
#324      lz4                          4.4.5         yes

56 packages shipped a version-specific wheel for 3.14
and have not yet shipped one for 3.15.
```

A package shipping `abi3` wheels needs no release at all for a new CPython.
`cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl` targets 3.11 and installs on 3.15.
A package shipping `cp3XX` wheels must publish a new build every single year.

## Cross-check against a real resolver

Reading filenames is not installing, so every compiled package was also resolved with
`uv pip install --only-binary :all: --dry-run` on 3.15.

```
of the 140 compiled packages                  count
----------------------------------------------------------
uv installs something, binary only            81
uv installs the LATEST release                68
uv installs nothing                           59

tag reading and resolver agree on 121/140 (86.4%).
13 packages install only by silently taking an older release.
```

The two disagree in both directions, and both are real: the tag reading sees only the
latest release (so it calls aiohttp blocked while uv installs an older aiohttp that has a
wheel), and it ignores the platform tag (so it calls tokenizers ready while no arm64 macOS
build exists).

## A bug worth reporting

The first run matched only `py3-none-any` and labelled **ruff, uv and playwright as
blocked**. Those ship `py3-none-macosx_11_0_arm64`: a version-independent *Python* tag with
a platform-specific binary. Matching the Python tag rather than the whole filename moved
39 packages out of blocked, 103 -> 64. Every number here is post-fix. See the comment in
`bench/classify.py`.

## Reproducing

```bash
uv python install 3.15
uv venv --python 3.15 .venv-verify

curl -sL -o results/top-pypi.json \
  https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json

python3 bench/classify.py 1000     # PyPI API -> pure/abi3/built/blocked
python3 bench/resolve_all.py       # uv resolve every compiled package on 3.15
python3 bench/verify.py            # spot-check the two against each other
python3 bench/tables.py            # regenerate every table above
```

Charts need matplotlib, which had no cp315 wheel at time of writing (it is in the blocked
list), so they run on a separate 3.14 environment:

```bash
uv venv --python 3.14 .venv-plot
uv pip install --python .venv-plot/bin/python matplotlib
.venv-plot/bin/python bench/chart.py
```

## Layout

| Path | What it is |
|---|---|
| `bench/classify.py` | wheel-tag classification from the PyPI JSON API |
| `bench/resolve_all.py` | uv binary-only resolution of all 140 compiled packages |
| `bench/verify.py` | sampled tag-vs-resolver agreement check |
| `bench/tables.py` | renders every table in this README |
| `bench/chart.py` | the two figures |
| `results/classified-1000.json` | per-package classification, 1000 rows |
| `results/resolve_all.json` | resolver outcome per compiled package |
| `results/top-pypi.json` | the input package list, as downloaded |

## Limits

- A snapshot. The Fedora tracker moved 90.0% -> 93.9% in about a fortnight; the blocker
  list is the fastest-decaying thing here.
- One machine, arm64 macOS. Linux x86_64 is better served. The tag counts are
  platform-independent; the resolver column is not.
- Latest release only. Pinning an older version gives you more options than this shows.
- Top 1,000 by downloads is not the long tail, where coverage is certainly worse.
- `requires_python` metadata was not used to exclude packages that have declared no 3.15
  support yet.

## License

MIT.
