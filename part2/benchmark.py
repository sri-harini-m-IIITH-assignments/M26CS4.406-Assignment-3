import argparse
import gc
import os
import sys
import time
import faiss
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "part1"))
from faiss_exact import DATASETS, dataset_loader, recall_at_k

RESULTS_DIR = os.path.join(ROOT, "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "results_part2.csv")
QUICK_PATH = os.path.join(RESULTS_DIR, "results_part2_quick.csv")

K = 10
STOP_RECALL = 0.97
PLATEAU_GAIN = 0.002
MIN_POINTS = 3

CONFIG = dict(
    n_train=None, n_tune=1000, n_report=5000, repeats=3, train_cap=256_000, efc=200,
    hnsw_M=[8, 16, 32],
    ef_grid=[10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024],
    ivf_nlist=[1024, 4096],
    nprobe_grid=[1, 2, 4, 8, 16, 32, 64, 128, 256],
    pq_nlist=[1024],
    pq_m={"sift": [16, 32], "glove": [20, 25]},
)

QUICK = dict(
    n_train=100_000, n_tune=500, n_report=1000, repeats=2, train_cap=100_000, efc=100,
    hnsw_M=[16, 32],
    ef_grid=[10, 20, 40, 80, 160, 320],
    ivf_nlist=[256, 1024],
    nprobe_grid=[1, 2, 4, 8, 16, 32, 64],
    pq_nlist=[256],
    pq_m={"sift": [16, 32], "glove": [20, 25]},
)

def load_dataset(name, n_train=None):
    train, test, gt = dataset_loader(name, n_train)
    if n_train is not None:
        faiss.omp_set_num_threads(os.cpu_count())
        index = faiss.IndexFlatL2(train.shape[1])
        index.add(train)
        _, gt = index.search(test, gt.shape[1])
    return train, test, gt

def split_queries(test, gt, n_tune=None, n_report=None):
    half = len(test) // 2
    tune = (test[:half][:n_tune], gt[:half][:n_tune])
    report = (test[half:][:n_report], gt[half:][:n_report])
    return tune, report

def sq_dists(train, queries, ids, chunk=1000):
    ids = np.asarray(ids)
    out = np.empty(ids.shape, dtype=np.float64)
    for s in range(0, len(ids), chunk):
        sub = ids[s:s + chunk]
        valid = sub >= 0
        diff = (train[np.where(valid, sub, 0)].astype(np.float64)
                - queries[s:s + chunk, None, :].astype(np.float64))
        d = np.einsum("qkd,qkd->qk", diff, diff)
        d[~valid] = np.inf
        out[s:s + chunk] = d
    return out

def evaluate_recall(I, gt, train, queries, k=10):
    true_d = sq_dists(train, queries, gt[:, :k])
    pred_d = sq_dists(train, queries, I[:, :k])
    return recall_at_k(I, gt, k=k, predicted_distance=pred_d, true_distance=true_d)

def time_single_query(index, queries, k=10, repeats=3, warmup=50):
    faiss.omp_set_num_threads(1)
    nq = len(queries)
    for i in range(min(warmup, nq)):
        index.search(queries[i:i + 1], k)
    labels = np.empty((nq, k), dtype=np.int64)
    qps = []
    for _ in range(repeats):
        start = time.perf_counter()
        for i in range(nq):
            _, I = index.search(queries[i:i + 1], k)
            labels[i] = I[0]
        qps.append(nq / (time.perf_counter() - start))
    return float(np.median(qps)), labels

def append_results(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = pd.DataFrame(rows)
    if os.path.exists(path):
        new = pd.concat([pd.read_csv(path), new], ignore_index=True)
    new.to_csv(path, index=False)

def build_hnsw(train, M, efc):
    index = faiss.IndexHNSWFlat(train.shape[1], M)
    index.hnsw.efConstruction = efc
    t = time.perf_counter()
    index.add(train)
    return index, None, time.perf_counter() - t

def _train_sample(train, nlist, cap, seed=0):
    n = min(len(train), max(50 * nlist, 100_000), cap)
    if n >= len(train):
        return train
    rng = np.random.default_rng(seed)
    return np.ascontiguousarray(train[np.sort(rng.choice(len(train), n, replace=False))])

def build_ivf(train, nlist, cap, pq_m=None):
    d = train.shape[1]
    quantizer = faiss.IndexFlatL2(d)
    if pq_m is None:
        index = faiss.IndexIVFFlat(quantizer, d, nlist)
    else:
        index = faiss.IndexIVFPQ(quantizer, d, nlist, pq_m, 8)
    sample = _train_sample(train, nlist, cap)
    t = time.perf_counter()
    index.train(sample)
    index.add(train)
    return index, quantizer, time.perf_counter() - t

def set_search_param(index, kind, value):
    if kind == "hnsw":
        index.hnsw.efSearch = int(value)
    else:
        index.nprobe = int(value)

def sweep(index, kind, grid, train, tune, report, repeats, base):
    param_name = "efSearch" if kind == "hnsw" else "nprobe"
    rows, keep, prev = [], [], None

    tq, tgt = tune
    for v in grid:
        set_search_param(index, kind, v)
        qps, I = time_single_query(index, tq, K, repeats=1)
        rec = evaluate_recall(I, tgt, train, tq, K)
        rows.append({**base, "split": "tune", "param": param_name, "value": v,
                     "nq": len(tq), "repeats": 1, "recall": rec, "qps": qps})
        print(f"    tune    {param_name}={v:<5} recall={rec:.4f} qps={qps:9.1f}", flush=True)
        keep.append(v)
        if rec >= STOP_RECALL:
            break
        if prev is not None and len(keep) >= MIN_POINTS and rec - prev < PLATEAU_GAIN:
            break
        prev = rec

    rq, rgt = report
    for v in keep:
        set_search_param(index, kind, v)
        qps, I = time_single_query(index, rq, K, repeats=repeats)
        rec = evaluate_recall(I, rgt, train, rq, K)
        rows.append({**base, "split": "report", "param": param_name, "value": v,
                     "nq": len(rq), "repeats": repeats, "recall": rec, "qps": qps})
        print(f"    report {param_name}={v:<5} recall={rec:.4f} qps={qps:9.1f}", flush=True)
    return rows

def configs(name, cfg, indexes):
    if "hnsw" in indexes:
        for M in cfg["hnsw_M"]:
            yield ("hnsw", f"M={M},efC={cfg['efc']}",
                   lambda tr, M=M: build_hnsw(tr, M, cfg["efc"]),
                   cfg["ef_grid"], dict(M=M, efC=cfg["efc"]))
    if "ivf_flat" in indexes:
        for nl in cfg["ivf_nlist"]:
            yield ("ivf_flat", f"nlist={nl}",
                   lambda tr, nl=nl: build_ivf(tr, nl, cfg["train_cap"]),
                   [p for p in cfg["nprobe_grid"] if p <= nl], dict(nlist=nl))
    if "ivf_pq" in indexes:
        for nl in cfg["pq_nlist"]:
            for m in cfg["pq_m"][name]:
                yield ("ivf_pq", f"nlist={nl},m={m}",
                       lambda tr, nl=nl, m=m: build_ivf(tr, nl, cfg["train_cap"], pq_m=m),
                       [p for p in cfg["nprobe_grid"] if p <= nl], dict(nlist=nl, pq_m=m))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=list(DATASETS), choices=list(DATASETS))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--indexes", nargs="+", default=["hnsw", "ivf_flat", "ivf_pq"],
                    choices=["hnsw", "ivf_flat", "ivf_pq"])
    args = ap.parse_args()
    cfg = CONFIG if not args.quick else QUICK
    out = QUICK_PATH if args.quick else RESULTS_PATH

    for name in args.datasets:
        print(f"=== {name} ===", flush=True)
        train, test, gt = load_dataset(name, cfg["n_train"])
        tune, report = split_queries(test, gt, cfg["n_tune"], cfg["n_report"])
        n = len(train)

        for kind, label, build, grid, bcols in configs(name, cfg, args.indexes):
            print(f"  build {kind} {label} ...", flush=True)
            faiss.omp_set_num_threads(os.cpu_count())
            index, keepalive, build_s = build(train)
            size = int(faiss.serialize_index(index).nbytes)
            print(f"  built in {build_s:.1f}s, {size / 1e6:.1f} MB ({size / n:.1f} B/vec)", flush=True)

            base = dict(part=2, dataset=name, index=kind, build=label, n=n,
                        build_time_s=build_s, index_bytes=size, bytes_per_vec=size / n, **bcols)
            rows = sweep(index, kind, grid, train, tune, report, cfg["repeats"], base)
            append_results(rows, out)

            del index, keepalive
            gc.collect()

    print(f"Finished. Results in {out}")


if __name__ == "__main__":
    main()