import argparse
import gc
import os
import sys
import faiss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "part2"))
import benchmark as b
import analyze as an

SEED = 4
DIM = 128
N_CLUSTERS = 256
CENTER_STD = 1.0
WITHIN_STD = (0.2, 0.6)

BUDGETS = [1000, 600, 150, 50]
CONTROL = 1000
LABEL = {"hnsw": "HNSW", "ivf_flat": "IVF-Flat", "ivf_pq": "IVF-PQ"}

FULL = dict(n=200_000, nq=2000, n_tune=500, n_report=1000, repeats=3, efc=200, suffix="",
            hnsw_M=[4, 8, 16, 32], nlist=1024, pq_m=[8, 16, 32, 64, 128], train_cap=200_000)
QUICK = dict(n=50_000, nq=1000, n_tune=250, n_report=500, repeats=2, efc=100, suffix="_quick",
             hnsw_M=[4, 8, 16, 32], nlist=256, pq_m=[8, 16, 32, 64, 128], train_cap=50_000)
RESULTS_DIR = os.path.join(ROOT, "results")


def make_data(n, nq, d=DIM, seed=SEED):
    rng = np.random.default_rng(seed)
    centers = rng.normal(0.0, CENTER_STD, size=(N_CLUSTERS, d))
    stds = rng.uniform(*WITHIN_STD, size=N_CLUSTERS)

    def draw(count, r):
        c = r.integers(0, N_CLUSTERS, size=count)
        return np.ascontiguousarray((centers[c] + r.normal(size=(count, d)) * stds[c, None]).astype(np.float32))

    return draw(n, np.random.default_rng(seed + 1)), draw(nq, np.random.default_rng(seed + 2))


def candidate_builds(cfg):
    nl = cfg["nlist"]
    grid_ef = b.CONFIG["ef_grid"]
    grid_nprobe = b.CONFIG["nprobe_grid"]

    for M in cfg["hnsw_M"]:
        yield ("hnsw", f"M={M},efC={cfg['efc']}", lambda tr, M=M: b.build_hnsw(tr, M, cfg["efc"]),
               grid_ef, dict(M=M, efC=cfg["efc"]))
    
    yield ("ivf_flat", f"nlist={nl}", lambda tr: b.build_ivf(tr, nl, cfg["train_cap"]),
           [p for p in grid_nprobe if p <= nl], dict(nlist=nl))
    
    for m in cfg["pq_m"]:
        yield ("ivf_pq", f"nlist={nl},m={m}", lambda tr, m=m: b.build_ivf(tr, nl, cfg["train_cap"], pq_m=m),
               [p for p in grid_nprobe if p <= nl], dict(nlist=nl, pq_m=m))


def run(cfg, out):
    if os.path.exists(out):
        os.remove(out)
    train, queries = make_data(cfg["n"], cfg["nq"])
    faiss.omp_set_num_threads(os.cpu_count())
    
    flat = faiss.IndexFlatL2(DIM)
    flat.add(train)
    _, gt = flat.search(queries, 100)
    del flat

    tune, report = b.split_queries(queries, gt, cfg["n_tune"], cfg["n_report"])
    n = len(train)

    for kind, label, build, grid, bcols in candidate_builds(cfg):
        print(f"  build {kind} {label} ...", flush=True)
        faiss.omp_set_num_threads(os.cpu_count())
        index, keep, build_s = build(train)
        size = int(faiss.serialize_index(index).nbytes)
        print(f"  built in {build_s:.1f}s, {size / n:.1f} B/vec", flush=True)
        base = dict(part=4, dataset="synthetic", index=kind, build=label, n=n, build_time_s=build_s,
                    index_bytes=size, bytes_per_vec=size / n, **bcols)
        rows = b.sweep(index, kind, grid, train, tune, report, cfg["repeats"], base)
        b.append_results(rows, out)
        del index, keep
        gc.collect()


def analyze(out, suffix):
    df = pd.read_csv(out)
    df = df[(df["part"] == 4) & (df["split"] == "report")]
    rows, curves = [], {}

    for B in BUDGETS:
        for kind in ("hnsw", "ivf_flat", "ivf_pq"):
            allk = df[df["index"] == kind]
            fit = allk[allk["bytes_per_vec"] <= B]
            row = {"budget (B/vec)": B + 0, "setting": "control" if B == CONTROL else "limit",
                   "index": LABEL[kind]}
            if fit.empty:
                row.update({"configs that fit": f"none (smallest is {allk['bytes_per_vec'].min():.0f} B/vec)",
                            "best recall": "-", "QPS @ 0.90": "-", "QPS @ 0.95": "-"})
                curves[(B, kind)] = (np.nan, np.nan, np.nan)
            else:
                front = an.pareto_frontier(fit)
                qs = {t: an.qps_at(front, t) for t in (0.90, 0.95)}
                best = float(front["recall"].max())
                row.update({"configs that fit": ", ".join(sorted(fit["build"].unique())),
                            "best recall": f"{best:.3f}",
                            "QPS @ 0.90": "not reached" if qs[0.90] is None else f"{qs[0.90]:,.0f}",
                            "QPS @ 0.95": "not reached" if qs[0.95] is None else f"{qs[0.95]:,.0f}"})
                curves[(B, kind)] = (best, np.nan if qs[0.90] is None else qs[0.90],
                                     np.nan if qs[0.95] is None else qs[0.95])
            rows.append(row)

    tab = pd.DataFrame(rows)
    an.save_table(tab, os.path.join(RESULTS_DIR, "tables" + suffix), "memory_budget")
    print(an.md_table(tab))

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
    xs = np.arange(len(BUDGETS))
    for kind in ("hnsw", "ivf_flat", "ivf_pq"):
        color, marker = an.STYLE[kind]
        axes[0].plot(xs, [curves[(B, kind)][0] for B in BUDGETS], marker=marker, color=color, label=LABEL[kind])
        axes[1].plot(xs, [curves[(B, kind)][1] for B in BUDGETS], marker=marker, color=color, label=LABEL[kind])
    
    axes[0].axhline(0.95, color="grey", ls=":", lw=0.8)
    axes[0].set_ylabel("best recall@10 inside the budget")
    axes[0].set_ylim(0, 1.02)
    axes[1].set_ylabel("QPS at recall 0.90 (1 query, 1 thread)")
    axes[1].set_yscale("log")
    
    for ax in axes:
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{B}\n(control)" if B == CONTROL else str(B) for B in BUDGETS])
        ax.set_xlabel("budget (bytes per vector)")
        ax.grid(True, alpha=0.25)
    
    axes[0].legend(loc="lower left")
    fig.suptitle("Own data (Gaussian mixture): gaps mean the index does not fit or never reaches the target", fontsize=9)
    fig.tight_layout()
    
    figdir = os.path.join(RESULTS_DIR, "figures" + suffix)
    os.makedirs(figdir, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(figdir, f"memory_budget.{ext}"), dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    cfg = QUICK if args.quick else FULL
    out = os.path.join(RESULTS_DIR, f"results_part4{cfg['suffix']}.csv")
    if not args.analyze_only:
        run(cfg, out)
    analyze(out, cfg["suffix"])
    print(f"Part 4 done. Results in {out}")


if __name__ == "__main__":
    main()