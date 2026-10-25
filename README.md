# Assignment 3: Benchmarking Approximate Nearest Neighbour Search

## Sriharini Margapuri (2026701030)

This repository contains the code for Information Retrieval and Extraction Assignment 3. It benchmarks exact FAISS search, HNSW, IVF-Flat, and IVF-PQ on the SIFT-128 and GloVe-100 ann-benchmarks datasets.

Part 3 analyzes scaling and Part 4 analyzes memory limits.

## Requirements

To install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

To download datasets:

```bash
bash download_data.sh
```

## Reproducing the results

Run the full pipeline. This regenerates the full `results/` directory:

```bash
bash run_all.sh
```

For a quick run on smaller subsets. This regenerates the separate
`results_quick/` directory:

```bash
bash run_all.sh --quick
```

Part 2 creates the initial consolidated `results.csv` from Parts 1 and 2.
Parts 3 and 4 append their own benchmark rows to that same file after their experiments finish. The quick run follows the same order in `results_quick/results_quick.csv`.

Individual checks can also be run directly:

```bash
python part1/faiss_exact.py --test
python part1/faiss_exact.py --quick
python part2/benchmark.py --quick
python part2/analyze.py --quick
python part3/scaling.py --quick
python part4/memory_limits.py --quick
```

## Repository layout

* `part1/faiss_exact.py` — exact baseline, tie-aware recall, and timing.
* `part2/benchmark.py` — HNSW, IVF-Flat, and IVF-PQ benchmarks.
* `part2/analyze.py` — merged results, trade-off plots, and report tables.
* `part3/scaling.py` — SIFT scaling experiment at 100K, 300K, and 1M.
* `part4/memory_limits.py` — seeded data generator and memory-budget
  experiment using HNSW, IVF-Flat, and IVF-PQ.
* `hypothesis.md` — hypotheses for Parts 3 and 4.
* `results/` — generated full-run results and report assets.
* `results_quick/` — generated quick-run results and report assets.
