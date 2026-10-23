import argparse
import gc
import math
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

DATASET = "sift"
TARGET = 0.95
FULL = dict(ns=[100_000, 300_000, 1_000_000], suffix="", n_tune=1000, n_report=5000, repeats=3,
            efc=200, M=16, n_exact_q=500, train_cap=256_000)
QUICK = dict(ns=[25_000, 50_000, 100_000], suffix="_quick", n_tune=500, n_report=1000, repeats=2,
             efc=100, M=16, n_exact_q=200, train_cap=100_000)
RESULTS_DIR = os.path.join(ROOT, "results")
LABEL = {"exact": "Exact (flat)", "hnsw": "HNSW", "ivf_flat": "IVF-Flat"}


def nlist_for(n):
    return int(2 ** round(math.log2(4 * math.sqrt(n))))


def run(cfg, out):
    if os.path.exists(out):
        os.remove(out)
    for n in cfg["ns"]:
        print(f"=== {DATASET} n={n:,} ===", flush=True)
        n_load = None if n >= 1_000_000 else n
        train, test, gt = b.load_dataset(DATASET, n_load)
        tune, report = b.split_queries(test, gt, cfg["n_tune"], cfg["n_report"])
        faiss.omp_set_num_threads(os.cpu_count())

        flat = faiss.IndexFlatL2(train.shape[1])
        flat.add(train)
        rq, rgt = report
        eq = rq[:cfg["n_exact_q"]]
        qps, I = b.time_single_query(flat, eq, b.K, repeats=cfg["repeats"])
        rec = b.evaluate_recall(I, rgt[:len(eq)], train, eq, b.K)
        b.append_results([dict(part=3, dataset=DATASET, index="exact", build="IndexFlatL2", n=n,
                               build_time_s=0.0, index_bytes=train.nbytes, bytes_per_vec=train.shape[1] * 4,
                               split="report", param="-", value=0, nq=len(eq), repeats=cfg["repeats"],
                               recall=rec, qps=qps)], out)
        print(f"  exact qps={qps:.1f} recall={rec:.4f}", flush=True)
        del flat

        builds = [("hnsw", f"M={cfg['M']},efC={cfg['efc']}",
                   lambda tr: b.build_hnsw(tr, cfg["M"], cfg["efc"]),
                   b.CONFIG["ef_grid"], dict(M=cfg["M"], efC=cfg["efc"]))]
        nl = nlist_for(n)
        builds.append(("ivf_flat", f"nlist={nl}",
                       lambda tr, nl=nl: b.build_ivf(tr, nl, cfg["train_cap"]),
                       [p for p in b.CONFIG["nprobe_grid"] if p <= nl], dict(nlist=nl)))
        for kind, label, build, grid, bcols in builds:
            print(f"  build {kind} {label} ...", flush=True)
            faiss.omp_set_num_threads(os.cpu_count())
            index, keep, build_s = build(train)
            size = int(faiss.serialize_index(index).nbytes)
            base = dict(part=3, dataset=DATASET, index=kind, build=label, n=n, build_time_s=build_s,
                        index_bytes=size, bytes_per_vec=size / n, **bcols)
            rows = b.sweep(index, kind, grid, train, tune, report, cfg["repeats"], base)
            b.append_results(rows, out)
            del index, keep
            gc.collect()


def analyze(out, suffix):
    df = pd.read_csv(out)
    df = df[(df["part"] == 3) & (df["split"] == "report")]
    rows = []
    for kind in ("exact", "hnsw", "ivf_flat"):
        for n in sorted(df["n"].unique()):
            sub = df[(df["index"] == kind) & (df["n"] == n)]
            if sub.empty:
                continue
            if kind == "exact":
                q, v, build_s = float(sub["qps"].iloc[-1]), "-", 0.0
            else:
                front = an.pareto_frontier(sub)
                q = an.qps_at(front, TARGET)
                i = an.first_at_or_above(front, TARGET)
                v = "not reached" if i is None else f"{front['param'].iloc[i]}={int(front['value'].iloc[i])}"
                build_s = float(sub["build_time_s"].iloc[0])
            rows.append(dict(index=kind, n=int(n), qps_at_095=q, search_param=v, build_time_s=build_s))
    t = pd.DataFrame(rows)

    slopes = {}
    for kind, g in t.dropna(subset=["qps_at_095"]).groupby("index"):
        if len(g) >= 2:
            slopes[kind] = float(np.polyfit(np.log(g["n"]), np.log(g["qps_at_095"]), 1)[0])
    out_rows = []
    for _, r in t.iterrows():
        same = t[t["index"] == r["index"]]
        base = same[same["n"] == same["n"].min()]["qps_at_095"].iloc[0]
        out_rows.append({"index": LABEL[r["index"]], "n": f"{r['n']:,}",
                         "QPS @ 0.95": "not reached" if pd.isna(r["qps_at_095"]) else f"{r['qps_at_095']:,.0f}",
                         "slowdown vs smallest n": "-" if pd.isna(r["qps_at_095"]) else f"{base / r['qps_at_095']:.1f}x",
                         "search param": r["search_param"], "build time (s)": f"{r['build_time_s']:.1f}",
                         "log-log slope": f"{slopes.get(r['index'], float('nan')):.2f}"})
    tab = pd.DataFrame(out_rows)
    an.save_table(tab, os.path.join(RESULTS_DIR, "tables" + suffix), "scaling")
    print(an.md_table(tab))

    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    sty = {"exact": ("black", "*"), "hnsw": an.STYLE["hnsw"], "ivf_flat": an.STYLE["ivf_flat"]}
    for kind, g in t.dropna(subset=["qps_at_095"]).groupby("index"):
        ax.plot(g["n"], g["qps_at_095"], marker=sty[kind][1], color=sty[kind][0], label=LABEL[kind])
    n0 = t["n"].min()
    q0 = t[(t["index"] == "exact") & (t["n"] == n0)]["qps_at_095"].iloc[0]
    ns = np.array(sorted(t["n"].unique()), dtype=float)
    ax.plot(ns, q0 * n0 / ns, color="grey", ls=":", label="ideal 1/n")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("number of vectors"); ax.set_ylabel("QPS at recall 0.95 (1 query, 1 thread)")
    ax.set_title("SIFT: speed at recall 0.95 vs dataset size")
    ax.grid(True, which="both", alpha=0.25); ax.legend()
    fig.tight_layout()
    figdir = os.path.join(RESULTS_DIR, "figures" + suffix)
    os.makedirs(figdir, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(figdir, f"scaling.{ext}"), dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    cfg = QUICK if args.quick else FULL
    out = os.path.join(RESULTS_DIR, f"results_part3{cfg['suffix']}.csv")
    if not args.analyze_only:
        run(cfg, out)
    analyze(out, cfg["suffix"])
    print(f"Part 3 done. Results in {out}")


if __name__ == "__main__":
    main()