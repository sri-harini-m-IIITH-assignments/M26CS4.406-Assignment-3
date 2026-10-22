import time
import pandas as pd
import numpy as np
import faiss
import h5py
import argparse
import os
import math

DATASETS = {"sift": "data/sift-128-euclidean.hdf5",
            "glove": "data/glove-100-angular.hdf5"}
            

def dataset_loader(name, n_train=None):
    with h5py.File(DATASETS[name], "r") as f:
        train = np.ascontiguousarray(f["train"][:n_train], dtype=np.float32)
        test = np.ascontiguousarray(f["test"][:], dtype=np.float32)
        gt = f["neighbors"][:] 
    if name == "glove":
        for x in (train, test):
            x /= np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
    return train, test, gt

def recall_at_k(predicted_labels, true_labels, k=10, predicted_distance=None, true_distance=None):
    predicted_labels = np.asarray(predicted_labels)
    true_labels = np.asarray(true_labels)

    if predicted_distance is None or true_distance is None:
        recalls = [
            len(set(pred[:k]).intersection(set(true[:k]))) / k
            for pred, true in zip(predicted_labels, true_labels)
        ]
        return float(np.mean(recalls))

    predicted_distance = np.asarray(predicted_distance)
    true_distance = np.asarray(true_distance)
    recalls = []

    for query in range(predicted_labels.shape[0]):
        pred_ids = predicted_labels[query, :k]
        true_ids = true_labels[query, :k]
        pred_distances = predicted_distance[query, :k]
        kth_true_distance = true_distance[query, k - 1]

        tolerance = max(1e-5, 1e-5 * abs(float(kth_true_distance)))
        matching_id = np.array([nid in true_ids for nid in pred_ids], dtype=bool)
        tied_or_better = pred_distances <= (kth_true_distance + tolerance)
        correct = matching_id | tied_or_better
        recalls.append(float(np.count_nonzero(correct)) / k)

    return float(np.mean(recalls)) if recalls else 0.0 

def check_exact_results(name, train, test, gt):
    index = faiss.IndexFlatL2(train.shape[1])
    index.add(train)
    D, I = index.search(test, gt.shape[1])
    true_d = ((train[gt[:, :10]] - test[:, None, :]) ** 2).sum(axis=2)
    rec = recall_at_k(I, gt, k=10, predicted_distance=D, true_distance=true_d)
    strict = recall_at_k(I, gt, k=10)
    print(f"{name}: tie-aware recall@10 = {rec:.4f}, id-only = {strict:.4f}")
    return rec

def time_exact_search(index, queries, k=10, n_single=500, repeats=3):
    faiss.omp_set_num_threads(1)
    index.search(queries[:1], k)
    one_at_a_time, batches = [], []
    for _ in range(repeats):
        start = time.perf_counter()
        for i in range(n_single):
            index.search(queries[i : i + 1], k)
        one_at_a_time.append(n_single / (time.perf_counter() - start))
        start = time.perf_counter()
        index.search(queries, k)
        batches.append(len(queries) / (time.perf_counter() - start))
    qps_single, qps_batch = np.median(one_at_a_time), np.median(batches)
    print(f"One at a time: {qps_single:.1f} QPS, batch: {qps_batch:.1f} QPS")
    return float(qps_single), float(qps_batch)

def test_recall():
    k = 3
    true_ids = np.array([[0, 1, 2]])
    true_d = np.array([[1.0, 2.0, 3.0]])
    assert recall_at_k([[0, 1, 2]], true_ids, k=k) == 1.0
    assert recall_at_k([[7, 8, 9]], true_ids, k=k) == 0.0
    assert math.isclose(recall_at_k([[0, 1, 9]], true_ids, k=k), 2/3)
    pred_ids = [[0, 1, 9]]
    pred_d = [[1.0, 2.0, 3.0]]
    assert recall_at_k(pred_ids, true_ids, k=k, predicted_distance=pred_d, true_distance=true_d) == 1.0

    print("All unit tests for recall_at_k passed successfully!")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--test", action="store_true", help="run recall unit tests and exit")
    args = ap.parse_args()

    if args.test:
        test_recall()
        raise SystemExit(0)

    n_train = 100_000 if args.quick else None
    os.makedirs("results", exist_ok=True)

    rows = []
    for name in DATASETS:
        train, test, gt = dataset_loader(name, n_train)
        index = faiss.IndexFlatL2(train.shape[1])
        index.add(train)

        if args.quick:
            print(f"{name}: quick mode, skipping agreement check")
            rec = float("nan")
        else:
            rec = check_exact_results(name, train, test, gt)

        qps_single, qps_batch = time_exact_search(index, test[5000:])
        rows.append(dict(dataset=name, index="exact", n=len(train),
                           recall_vs_file=rec,
                           qps_single=qps_single, qps_batch=qps_batch))

    out = "results/results_part1_quick.csv" if args.quick else "results/results_part1.csv"
    pd.DataFrame(rows).to_csv(out, index=False)

if __name__ == "__main__":
    main()