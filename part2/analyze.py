import os
import sys
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results")
PART1_PATH = os.path.join(RESULTS_DIR, "results_part1.csv")
PART2_PATH = os.path.join(RESULTS_DIR, "results_part2.csv")
MERGED_PATH = os.path.join(RESULTS_DIR, "results.csv")

LABEL = {"hnsw": "HNSW", "ivf_flat": "IVF-Flat", "ivf_pq": "IVF-PQ"}
STYLE = {"hnsw": ("tab:blue", "o"), "ivf_flat": ("tab:orange", "s"), "ivf_pq": ("tab:green", "^")}
DIM = {"sift": 128, "glove": 100}
TARGETS = (0.90, 0.95)


def pareto_frontier(df):
    d = df.sort_values(["recall", "qps"], ascending=[False, False])
    keep, best = [], -np.inf
    for idx, row in d.iterrows():
        if row["qps"] > best:
            keep.append(idx)
            best = row["qps"]
    return d.loc[keep].sort_values("recall").reset_index(drop=True)


def first_at_or_above(front, target):
    r = front["recall"].values
    return None if r.max() < target else int(np.argmax(r >= target))


def qps_at(front, target):
    i = first_at_or_above(front, target)
    if i is None:
        return None
    r, q = front["recall"].values, front["qps"].values
    if i == 0 or r[i] == target:
        return float(q[i])
    t = (target - r[i - 1]) / (r[i] - r[i - 1])
    return float(np.exp(np.log(q[i - 1]) * (1 - t) + np.log(q[i]) * t))


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def save_table(df, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    df.to_csv(os.path.join(outdir, name + ".csv"), index=False)
    with open(os.path.join(outdir, name + ".md"), "w") as fh:
        fh.write(md_table(df))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    sfx = "_quick" if args.quick else ""
    part1_path = os.path.join(RESULTS_DIR, f"results_part1{sfx}.csv")
    part2_path = os.path.join(RESULTS_DIR, f"results_part2{sfx}.csv")
    merged_path = os.path.join(RESULTS_DIR, f"results{sfx}.csv")

    parts = [pd.read_csv(p) for p in (part1_path, part2_path) if os.path.exists(p)]
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(merged_path, index=False)

    p2 = df[(df["part"] == 2) & (df["split"] == "report")]
    exact = df[df["index"] == "exact"]

    qps_rows, cost_rows = [], []
    figdir = os.path.join(RESULTS_DIR, "figures")
    tdir = os.path.join(RESULTS_DIR, "tables")
    os.makedirs(figdir, exist_ok=True)

    for ds in sorted(p2["dataset"].unique()):
        fig, ax = plt.subplots(figsize=(6.2, 4.3))
        n = int(p2[p2["dataset"] == ds]["n"].iloc[0])
        lo = 1.0

        for kind in ("hnsw", "ivf_flat", "ivf_pq"):
            sub = p2[(p2["dataset"] == ds) & (p2["index"] == kind)]
            if sub.empty:
                continue
            front = pareto_frontier(sub)
            color, marker = STYLE[kind]
            ax.plot(front["recall"], front["qps"], marker=marker, color=color, label=LABEL[kind])
            lo = min(lo, front["recall"].min())

            row = {"dataset": ds, "index": LABEL[kind]}
            for t in TARGETS:
                v = qps_at(front, t)
                row[f"QPS @ recall {t:.2f}"] = (
                    f"{v:,.0f}" if v is not None else f"not reached (max {front['recall'].max():.3f})"
                )
            qps_rows.append(row)

            i = first_at_or_above(front, 0.95)
            reached = i is not None
            p = front.iloc[i if reached else len(front) - 1]
            cost_rows.append({
                "dataset": ds, "index": LABEL[kind], "config": p["build"],
                "search param": f"{p['param']}={int(p['value'])}",
                "recall": f"{p['recall']:.3f}" + ("" if reached else " (max, <0.95)"),
                "build time (s)": f"{p['build_time_s']:.1f}",
                "index size (MB)": f"{p['index_bytes'] / 1e6:.0f}",
                "bytes/vector": f"{p['bytes_per_vec']:.0f}"
            })

        ex = exact[(exact["dataset"] == ds) & (exact["n"] == n)]
        if not ex.empty:
            q = float(ex["qps_single"].iloc[-1])
            ax.scatter([1.0], [q], marker="*", s=140, color="black", zorder=5, label="Exact (flat)")
            qps_rows.append({"dataset": ds, "index": "Exact (flat)", **{f"QPS @ recall {t:.2f}": f"{q:,.0f}" for t in TARGETS}})
            d = DIM[ds]
            cost_rows.append({
                "dataset": ds, "index": "Exact (flat)", "config": "IndexFlatL2",
                "search param": "-", "recall": "1.000", "build time (s)": "~0",
                "index size (MB)": f"{n * d * 4 / 1e6:.0f}", "bytes/vector": f"{d * 4}"
            })
        else: 
            print(f"warning: no Part 1 exact row for {ds} (n={n})")

        for t in TARGETS:
            ax.axvline(t, color="grey", ls=":", lw=0.8)
        
        ax.set_yscale("log")
        ax.set_xlim(max(0.0, lo - 0.03), 1.01)
        ax.set_xlabel("recall@10")
        ax.set_ylabel("queries per second (1 thread)")
        ax.set_title(f"{ds}: recall vs speed ({n:,} vectors)")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend()
        fig.tight_layout()

        for ext in ("png", "pdf"):
            fig.savefig(os.path.join(figdir, f"recall_qps_{ds}.{ext}"), dpi=200)
        plt.close(fig)

    qdf, cdf = pd.DataFrame(qps_rows), pd.DataFrame(cost_rows)
    save_table(qdf, tdir, "qps_at_recall")
    save_table(cdf, tdir, "cost_at_recall_095")
    
    print(md_table(qdf))
    print(md_table(cdf))
    print(f"Analysis complete. Figures in {figdir}, tables in {tdir}")


if __name__ == "__main__":
    main()